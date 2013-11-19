# -*- coding: utf-8 -*-
import copy

import sqlalchemy as sa
from wtforms import validators, fields, ValidationError
from wtforms.widgets import HTMLString, html_params
from flask.ext.babel import _
from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.exc import NoResultFound

from flask.ext.databrowser.kolumne import Kolumne
from flask.ext.databrowser.sa import SAModell, convert
from flask.ext.databrowser import extra_widgets, extra_fields, sa_utils
from flask.ext.databrowser.col_spec import FileColumnSpec, InputColumnSpec


class SAKolumne(Kolumne):
    def __init__(self, property_, modell):
        assert isinstance(property_, (ColumnProperty, RelationshipProperty,
                                      InstrumentedAttribute))
        if isinstance(property_, InstrumentedAttribute):
            self._property = property_.property
        self._property = property_
        self._modell = modell

    def is_relationship(self):
        return hasattr(self._property, "direction")

    @property
    def remote_side(self):
        return SAModell(self._modell.model, self._modell.db)

    def local_column(self):
        return self._property.local_remote_pairs[0][0]

    def not_back_ref(self):
        '''
        test if not is back reference
        '''
        return self._property.backref

    def is_fk(self):
        '''
        test if is foreign key column
        '''
        return not self.is_relationship() and \
            self._property.columns[0].foreign_keys

    @property
    def key(self):
        return self._property.key

    @property
    def direction(self):
        return self._property.direction.name

    def make_field(self, col_spec):
        assert isinstance(col_spec, InputColumnSpec)
        kwargs = self._get_col_spec_args()
        column_kwargs = self.get_property_specific_args()
        self._merge_with_column_args(column)

        if self.is_relationship():
            field_class = self._get_relationship_field_class(col_spec)
            ret = field_class(**kwargs)
            if col_spec.remote_create_url:
                ret = pack_remote_create_url(ret, col_spec.remote_create_url)
            if col_spec.group_by:
                ret = pack_grouper(ret)
        else:
            column = self._property.columns[0]
            if column.primary_key:
                return fields.HiddenField()
            field_class = convert.get_field_class(column)
            ret = field_class(**kwargs)
        return ret

    def _merge_with_column_args(self, col_spec_args, column_args):
        for k, v in col_spec_args:
            if k == 'validators':
                column_args.setdefault('validators', []).extends(v)
            elif k == 'filters':
                column_args.setdefault('filters', []).extends(v)
            else:  # column specification is more important
                column_args[k] = v
        return column_args
        # merge them

    def _get_relationship_field(self, col_spec, **kwargs):
        """
        convert the relationship to field
        """
        direction_name = self._property.direction.name
        if direction_name == 'MANYTOONE':
            if col_spec.group_by:
                ret = GroupedQuerySelectField(col_spec,
                                              self.modell.session,
                                              **kwargs)
            else:
                ret = extra_fields.QuerySelectField(**kwargs)
        elif self._property.direction.name == 'ONETOMANY':
            #TODO if group_by is considered, a more advanced widget should
            # be used to select multiple options
            ret = extra_fields.QuerySelectMultipleField(**kwargs)
        elif self._property.direction.name == 'MANYTOMANY':
            #TODO if group_by is considered, a more advanced widget should
            # be used to select multiple options
            ret = extra_fields.QuerySelectMultipleField(**kwargs)
        return ret

    def _get_field_class(self):
        """
        Returns WTForms field class. Class is based on a custom field class
        attribute or SQLAlchemy column type.

        :param column: SQLAlchemy Column object
        """
        if 'choices' in column.info and column.info['choices']:
            return SelectField
        if (type(column.type) not in self.TYPE_MAP) and \
           isinstance(column.type, sa.types.TypeDecorator):
            check_type = column.type.impl
        else:
            check_type = column.type
        for type_ in self.TYPE_MAP:
            if isinstance(check_type, type_):
                return self.TYPE_MAP[type_]
        return None

    def _get_col_spec_args(self, col_spec):
        kwargs = {
            'validators': copy.copy(col_spec.validators) or [],
            'filters': [],
            'label': col_spec.label,
            'description': col_spec.doc,
            'opt_filter': col_spec.opt_filter
        }
        if col_spec.read_only:
            kwargs['disabled'] = True
        if self.is_relationship():
            # get_label is used to format options
            kwargs.update(self._get_label_args(col_spec))
            kwargs.update(self._query_factory_args(col_spec))
            column = self.local_column
            kwargs['allow_blank'] = column.nullable
            direction_name = self._property.direction.name
            multiple = direction_name != 'MANYTOONE'
            kwargs['widget'] = extra_widgets.Select2Widget(multiple=multiple)
        else:
            column = self._property.columns[0]

        return kwargs

    def _get_label_args(self, col_spec):
        kwargs = {}
        if col_spec.formatter:
            kwargs['get_label'] = lambda x: col_spec.formatter(x,
                                                                self.modell)
        else:
            kwargs['get_label'] = lambda x: unicode(x)
        return kwargs

    def _query_factory_args(self, col_spec):
        remote_model = self._property.mapper.class_
        query_factory = lambda: self.modell.session.query(remote_model)
        if col_spec.filter_:
            query_factory = lambda: col_spec.filter_(query_factory)

        return {'query_factory': query_factory}

    def _format_args(self):
        kwargs = {}
        data_format = None
        column = self._property.columns[0]
        if isinstance(column.type, sa.types.DateTime) or \
           isinstance(column.type, types.ArrowType):
            data_format = self.meta.datetime_format
        if isinstance(column.type, sa.types.Date):
            data_format = self.meta.date_format
        if date_format:
            kwargs['format'] = date_format
        return kwargs

    def _choices_args(self):
        kwargs = {}
        column = self._property.columns[0]
        if isinstance(column.type, types.ChoiceType):
            kwargs['choices'] = column.type.choices
            kwargs['coerce'] = self._get_coerce(column)
        if hasattr(column.type, 'enums'):
            kwargs['coerce'] = self._get_coerce(column)
            kwargs['choices'] = [
                (enum, enum) for enum in column.type.enums
            ]
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

    def _get_date_format(self, column):
        """
        Returns date format for given column.

        :param column: SQLAlchemy Column object
        """
        if (
            isinstance(column.type, sa.types.DateTime) or
            isinstance(column.type, types.ArrowType)
        ):
            return self.meta.datetime_format

        if isinstance(column.type, sa.types.Date):
            return self.meta.date_format

    def _get_validators(self):
        # MANYTOMANY and ONETOMANY column won't be required
        if self.is_relationship():
            ret = []
            if self._property.direction.name == 'MANYTOONE' and \
               not self.local_column.nullable:
                validator = validators.Required(
                    message=_(u"this field can't be empty"))
                ret.append(validator)
        else:
            column = self._property.columns[0]
            if column.unique:
                message = _("This field must be unique!")
                ret.append(Unique(self.modell.session,
                                  self.modell.model,
                                  column,
                                  message=message))
                if isinstance(column.type, sa.types.String) and \
                   hasattr(column.type, 'length') and column.type.length:
                    ret.append(Length(max=column.type.length))
        if isinstance(column.type, types.EmailType):
            ret.append(Email())
        return ret

    def _get_widget(self):
        """
        Returns WTForms widget for given column.

        :param column: SQLAlchemy Column object
        """
        kwargs = {}

        step = column.info.get('step', None)
        if step is not None:
            kwargs['step'] = step
        else:
            if isinstance(column.type, sa.types.Numeric):
                if (
                    column.type.scale is not None and
                    not column.info.get('choices')
                ):
                    kwargs['step'] = self.scale_to_step(column.type.scale)

        if kwargs:
            widget_class = self.WIDGET_MAP[
                self.get_field_class(column)
            ]
            return widget_class(**kwargs)


#TODO should be more elegant
class GroupedQuerySelectField(extra_fields.QuerySelectField):

    def __init__(self, session, col_spec, *args, **kwargs):
        super(GroupedQuerySelectField, self).__init__(*args, **kwargs)
        self.col_spec = col_spec
        self.session = session

    def __call__(self, **kwargs):
        grouper = extra_widgets.Select2Widget()
        grouper_kwargs = {}
        if kwargs.get("class"):
            grouper_kwargs["class"] = kwargs["class"]
        if kwargs.get("disabled"):
            grouper_kwargs["disabled"] = True
        s = grouper(FakeGroupField(self.col_spec.grouper_input_name,
                                   self.col_spec.group_by.group(self.data),
                                   self.col_spec.group_by.options),
                    **grouper_kwargs) + "<div class='text-center'>--</div>"
        s += super(GroupedQuerySelectField, self).__call__(**kwargs)
        return s


class FakeGroupField(object):

    def __init__(self, name, data, options):
        self.name = name
        self.id = "_" + name
        self.data = data
        self.options = options

    def iter_choices(self):
        for opt in self.options:
            # id, value, selected
            yield opt, opt, opt == self.data


class Unique(object):
    """Checks field value unique against specified table field.

    :param db_session:
        A given SQAlchemy Session.
    :param model:
        The model to check unique against.
    :param column:
        The unique column.
    :param message:
        The error message.
    """
    field_flags = ('unique', )

    def __init__(self, db_session, model, column, message=None):
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message

    def __call__(self, form, field):
        try:
            obj = (self.db_session.query(self.model)
                   .filter(self.column == field.data).one())

            if not hasattr(form, '_obj') or not form._obj == obj:
                if self.message is None:
                    message = field.gettext(
                        "This field must be unique, but it already exists!")
                    self.message = message
                raise ValidationError(self.message)
        except NoResultFound:
            pass


def pack_remote_create_url(field, create_url):

    class FakeField(field.field_class):

        def __call__(self, **kwargs):
            ret = super(FakeField, self).__call__(**kwargs)
            params = {
                'href': create_url,
                'data-role': 'new-related-obj',
                'data-target': 'field.name',
                'class': 'btn btn-primary'
            }
            params = html_params(**params)
            ret += HTMLString('<a %s>%s</a>' % (params, _("create")))
            return ret

    field.field_class = FakeField
    return field
