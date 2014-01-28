# -*- coding: utf-8 -*-
from collections import OrderedDict
import copy
from decimal import Decimal
from datetime import datetime, date

from sqlalchemy_utils import types as sa_util_types
from wtforms import validators, fields, ValidationError, SelectField, TextAreaField, BooleanField, FloatField, \
    PasswordField
from wtforms.widgets.html5 import URLInput
from wtforms.widgets import HTMLString, html_params, CheckboxInput, TextArea
from flask.ext.babel import _
from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import types as sa_types

from wtforms_components.utils import null_or_unicode
from wtforms_components import (ColorField, DateField, DateRange, DateTimeField, DateTimeLocalField, DecimalField,
                                Email, EmailField, IntegerField, NumberRangeField, PhoneNumberField, SelectField,
                                StringField, TimeField, TimeRange, Unique)
from wtforms_components.widgets import (ColorInput, EmailInput, DateInput,
                                        DateTimeInput, DateTimeLocalInput,
                                        NumberInput, TextInput, TimeInput)

from flask.ext.databrowser.kolumne import Kolumne
from flask.ext.databrowser.sa import sa_utils
from flask.ext.databrowser import extra_widgets, utils
from flask.ext.databrowser.extra_fields import URLField, ChoiceSelectField
from flask.ext.databrowser.col_spec import InputColSpec
from flask.ext.databrowser.sa.sa_fields import GroupedQuerySelectField, QuerySelectField, QuerySelectMultipleField


# TODO should mainly use wtforms it self
class SAKolumne(Kolumne):
    hidden_pk = False

    TYPE_MAP = OrderedDict((
        (sa_types.UnicodeText, TextAreaField),
        (sa_types.BigInteger, IntegerField),
        (sa_types.SmallInteger, IntegerField),
        (sa_types.Text, TextAreaField),
        (sa_types.Boolean, BooleanField),
        (sa_types.Date, DateField),
        (sa_types.DateTime, DateTimeField),
        (sa_types.Enum, SelectField),
        (sa_types.Float, FloatField),
        (sa_types.Integer, IntegerField),
        (sa_types.Numeric, DecimalField),
        (sa_types.String, StringField),
        (sa_types.Time, TimeField),
        (sa_types.Unicode, StringField),
        (sa_util_types.ArrowType, DateTimeField),
        (sa_util_types.ChoiceType, ChoiceSelectField),
        (sa_util_types.ColorType, ColorField),
        (sa_util_types.EmailType, EmailField),
        (sa_util_types.NumberRangeType, NumberRangeField),
        (sa_util_types.PasswordType, PasswordField),
        (sa_util_types.PhoneNumberType, PhoneNumberField),
        (sa_util_types.ScalarListType, StringField),
        (sa_util_types.UUIDType, StringField),
        (sa_util_types.URLType, URLField),
    ))

    WIDGET_MAP = OrderedDict((
        (BooleanField, CheckboxInput),
        (ColorField, ColorInput),
        (DateField, DateInput),
        (DateTimeField, DateTimeInput),
        (DateTimeLocalField, DateTimeLocalInput),
        (DecimalField, NumberInput),
        (EmailField, EmailInput),
        (FloatField, NumberInput),
        (IntegerField, NumberInput),
        (TextAreaField, TextArea),
        (TimeField, TimeInput),
        (StringField, TextInput),
        (URLField, URLInput),
    ))

    def __init__(self, property_, db):
        assert isinstance(property_, (ColumnProperty, RelationshipProperty,
                                      InstrumentedAttribute))
        if isinstance(property_, InstrumentedAttribute):
            self._property = property_.property
        else:
            self._property = property_
        self._db = db

    def is_relationship(self):
        return hasattr(self._property, "direction")

    @property
    def remote_side(self):
        from flask.ext.databrowser.sa.sa_modell import SAModell

        return SAModell(self._property.mapper.class_, self._db)

    @property
    def local_column(self):
        return self._property.local_remote_pairs[0][0]

    def not_back_ref(self):
        """
        test if not is back reference
        """
        return self._property.backref

    def is_fk(self):
        """
        test if is foreign key column
        """
        return not self.is_relationship() and self._property.columns[0].foreign_keys

    def is_primary_key(self):
        return not self.is_relationship() and self._property.columns[0].primary_key

    @property
    def key(self):
        return self._property.key

    @property
    def direction(self):
        return self._property.direction.name

    def make_field(self, col_spec):
        assert isinstance(col_spec, InputColSpec)
        col_spec_kwargs = self._get_col_spec_args(col_spec)
        column_kwargs = self._get_property_specific_args()
        kwargs = self._merge_with_column_args(col_spec_kwargs, column_kwargs)

        if self.is_relationship():
            ret = self._get_relationship_field(col_spec, **kwargs)
        else:
            column = self._property.columns[0]
            if column.primary_key and self.hidden_pk:
                return fields.HiddenField()
            kwargs.update(sa_utils.get_column_default_value(column))
            kwargs.update(self._format_args(column))
            kwargs.update(self._choices_args(column))
            ret = self._get_field(column, **kwargs)
        return ret

    def _merge_with_column_args(self, col_spec_args, column_args):
        result = {}
        result.update(column_args)
        for k, v in col_spec_args.iteritems():
            if k == 'validators':
                result.setdefault('validators', []).extend(v)
            elif k == 'filters':
                result.setdefault('filters', []).extend(v)
            else:  # column specification is more important
                result[k] = v
        result["validators"].extend(self._get_validators())
        return result
        # merge them

    def _get_relationship_field(self, col_spec, **kwargs):
        """
        convert the relationship to field
        """
        direction_name = self._property.direction.name
        if direction_name == 'MANYTOONE':
            if col_spec.group_by:
                ret = GroupedQuerySelectField(col_spec, **kwargs)
            else:
                ret = QuerySelectField(**kwargs)
        elif direction_name == 'ONETOMANY':
            #TODO if group_by is considered, a more advanced widget should
            # be used to select multiple options
            if col_spec.group_by:
                kwargs["grouper"] = self._add_grouper(col_spec.group_by)
            ret = QuerySelectMultipleField(**kwargs)
        elif direction_name == 'MANYTOMANY':
            #TODO if group_by is considered, a more advanced widget should
            # be used to select multiple options
            if col_spec.group_by:
                kwargs["grouper"] = self._add_grouper(col_spec.group_by)
            ret = QuerySelectMultipleField(**kwargs)
        return ret

    def _get_field(self, column, **kwargs):
        """
        Returns WTForms field class. Class is based on a custom field class
        attribute or SQLAlchemy column type.

        :param column: SQLAlchemy Column object
        """
        if (type(column.type) not in self.TYPE_MAP) and isinstance(column.type, sa_types.TypeDecorator):
            check_type = column.type.impl
        else:
            check_type = column.type
        for type_ in self.TYPE_MAP:
            if isinstance(check_type, type_):
                field_cls = self.TYPE_MAP[type_]
                widget = self._widget(column, field_cls)
                kwargs['widget'] = widget
                return field_cls(**kwargs)
        return None

    def _get_col_spec_args(self, col_spec):
        def get_label_args(col_spec):
            return col_spec.entry_formatter if col_spec.entry_formatter else lambda x: unicode(x)

        kwargs = {
            'validators': copy.copy(col_spec.validators) or [],
            'filters': [],
            'label': col_spec.label,
            'description': col_spec.doc,
        }
        #if col_spec.read_only:
        #    kwargs['disabled'] = True
        if self.is_relationship():
            if col_spec.opt_filter:
                kwargs["opt_filter"] = col_spec.opt_filter
                # get_label is used to format options
            kwargs["get_label"] = get_label_args(col_spec)
            kwargs.update(self._query_factory_args(col_spec))
            if 'allow_blank' not in kwargs and self.local_column.foreign_keys:
                kwargs['allow_blank'] = self.local_column.nullable
            direction_name = self._property.direction.name
            multiple = direction_name != 'MANYTOONE'
            kwargs['widget'] = extra_widgets.Select2Widget(multiple=multiple)
        return kwargs

    def _query_factory_args(self, col_spec):
        remote_model = self._property.mapper.class_
        #query = self._db.session.query(remote_model)
        #query_factory = lambda: query
        #if col_spec.filter_:
            #query_factory = lambda: col_spec.filter_(query)
        # !!!important, why bother to do this? because flask sqlalchemy will
        # close the session after each request. so if we only remember query
        # here, then after one request, the query is obseleted!, so don't do
        # this:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #       query = self._db.session.query(remote_model)
        #       query_factory = lambda: query
        #       if col_spec.filter_:
        #           query_factory = lambda: col_spec.filter_(query)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        class QueryFactory(object):

            def __init__(self, db, remote_model, filter):
                self._db = db
                self._remote_model = remote_model
                self._filter = filter or (lambda q: q)

            def __call__(self):
                return self._filter(self._db.session.query(self._remote_model))

        query_factory = QueryFactory(self._db, remote_model, col_spec.filter_)
        return {'query_factory': query_factory}

    def _format_args(self, column):
        kwargs = {}
        date_format = None
        if isinstance(column.type, sa_types.DateTime) or isinstance(column.type, sa_util_types.ArrowType):
            date_format = self.datetime_format
        if isinstance(column.type, sa_types.Date):
            date_format = self.date_format
        if date_format:
            kwargs['format'] = date_format
        return kwargs

    def _widget(self, column, field_cls):
        """
        Returns WTForms widget for given column.

        :param column: SQLAlchemy Column object
        """
        kwargs = {}
        if isinstance(column.type, sa_types.Numeric):
            if column.type.scale is not None:
                kwargs['step'] = self.scale_to_step(column.type.scale)

        widget_class = self.WIDGET_MAP.get(field_cls)
        return widget_class and widget_class(**kwargs)

    def _choices_args(self, column):
        kwargs = {}
        if isinstance(column.type, sa_util_types.ChoiceType):
            kwargs['choices'] = column.type.choices
            kwargs['coerce'] = self._get_coerce(column)
        if hasattr(column.type, 'enums'):
            kwargs['coerce'] = self._get_coerce(column)
            kwargs['choices'] = [(enum, enum) for enum in column.type.enums]
        return kwargs

    def _get_coerce(self, column):
        """
        Returns coerce callable for given column

        :param column: SQLAlchemy Column object
        """
        try:
            python_type = column.type.python_type
        except NotImplementedError:
            return null_or_unicode

        if column.nullable and issubclass(python_type, basestring):
            return null_or_unicode
        return python_type

    @property
    def date_format(self):
        return "%Y-%m-%d"

    @property
    def datetime_format(self):
        return "%Y-%m-%d %H:%M"

    def _get_validators(self):
        # MANYTOMANY and ONETOMANY column won't be required
        ret = []
        if self.is_relationship():
            if not self.local_column.foreign_keys or self.local_column.nullable:
                ret.append(validators.Optional())
            elif self._property.direction.name == 'MANYTOONE':
                ret.append(validators.Required(message=_(u"this field can't be empty")))
        else:
            def unique_validator(column):
                """
                Returns unique validator for given column if column has a unique index

                :param column: SQLAlchemy Column object
                """
                if column.unique or column.primary_key:
                    #为了取得真正的model
                    return Unique(self._property.class_attribute, get_session=self._db.session,
                                  message=_("This field must be unique!"))

            def length_validator(column):
                """
                Returns length validator for given column

                :param column: SQLAlchemy Column object
                """
                if sa_utils.is_str_column(column) and getattr(column.type, "length", 0):
                    return validators.Length(max=column.type.length)

            def required_validator(column):
                if not column.nullable and not isinstance(column.type, sa_types.Boolean):
                    return validators.Required(message=_(u"this field can't be empty"))
                else:
                    return validators.Optional()

            column = self._property.columns[0]
            ret = [i for i in (unique_validator(column), length_validator(column), required_validator(column)) if
                   i is not None]
            if isinstance(column.type, sa_util_types.EmailType):
                ret.append(Email())
        return ret


    def _get_property_specific_args(self):
        return {}

    def scale_to_step(self, scale):
        """
        Returns HTML5 compatible step attribute for given decimal scale.

        :param scale: an integer that defines a Numeric column's scale
        """
        return str(pow(Decimal('0.1'), scale))

    @property
    def doc(self):
        return getattr(self._property, "doc", None)

    def _add_grouper(self, group_by):
        if hasattr(group_by, "__call__"):
            return group_by
        elif hasattr(group_by, "property"):
            if hasattr(group_by, "is_mapper") and group_by.is_mapper:
                column = sa_utils.get_primary_key(group_by.property)
            return lambda x: getattr(x, column.key)
        else:
            return lambda x: x


    def coerce_value(self, v):
        '''
        coerce value into the type comply with column definition
        '''
        assert isinstance(v, basestring)
        column = self._property.columns[0]
        if isinstance(column.type, sa_types.DateTime):
            return datetime.strptime(v, self.datetime_format)
        elif isinstance(column.type, sa_types.Date):
            return datetime.strptime(v, self.date_format)
        return v


def pack_grouper(field, col_spec):
    field.field_class = GroupedQuerySelectField
    field.kwargs["col_spec"] = col_spec
    return field
