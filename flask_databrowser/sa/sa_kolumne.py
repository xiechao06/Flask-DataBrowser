# -*- coding: utf-8 -*-
import copy

from wtforms import validators, fields, ValidationError
from flask.ext.babel import _
from sqlalchemy import Boolean
from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.exc import NoResultFound

from flask.ext.databrowser.kolumne import Kolumne
from flask.ext.databrowser.sa import SAModell
from flask.ext.databrowser import extra_widgets, extra_fields, sa_utils
from flask.ext.databrowser.col_spec import FileColumnSpec
from . import sa_converter


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
        kwargs = {
            'validators': copy.copy(col_spec.validators),
            'filters': [],
            'label': col_spec.label,
            'doc': col_spec.doc,
            'opt_filter': col_spec.opt_filter
        }

        # Check if it is relation or property
        if self.is_relationship():
            remote_model = self._property.mapper.class_
            local_column = self.local_column

            # get_label is used to format options
            if col_spec.formatter:
                kwargs['get_label'] = lambda x: col_spec.formatter(x,
                                                                   self.modell)
            else:
                kwargs['get_label'] = lambda x: unicode(x)

            # MANYTOMANY and ONETOMANY column won't be required
            if self._property.direction.name == 'MANYTOONE' and \
               not local_column.nullable:
                validator = validators.Required(
                    message=_(u"this field can't be empty"))
                kwargs['validators'].append(validator)
            else:
                kwargs['allow_blank'] = local_column.nullable

            query_factory = lambda: self.modell.session.query(remote_model)
            if col_spec.filter_:
                query_factory = lambda: col_spec.filter_(query_factory)
            kwargs['query_factory'] = query_factory

            if self._property.direction.name == 'MANYTOONE':
                widget = extra_widgets.Select2Widget()
                if col_spec.group_by:
                    return GroupedQuerySelectField(col_spec,
                                                   self.modell.session,
                                                   widget=widget,
                                                   **kwargs)
                return extra_fields.QuerySelectField(widget=widget, **kwargs)
            elif self._property.direction.name == 'ONETOMANY':
                #TODO if group_by is considered, a more advanced widget should
                # be used to select multiple options
                return extra_fields.QuerySelectMultipleField(
                    widget=extra_widgets.Select2Widget(multiple=True),
                    **kwargs)
            elif self._property.direction.name == 'MANYTOMANY':
                #TODO if group_by is considered, a more advanced widget should
                # be used to select multiple options
                return extra_fields.QuerySelectMultipleField(
                    widget=extra_widgets.Select2Widget(multiple=True),
                    **kwargs)
        else:  # not relationship
            column = self._property.columns[0]
            # primary key can't be altered
            if column.primary_key:
                return fields.HiddenField()
            if column.primary_key or column.unique:
                message = _("This field must be unique, "
                            "but it already exists!")
                kwargs['validators'].append(Unique(self.session,
                                                   self.modell.model,
                                                   column,
                                                   message=message))
            if not column.nullable and not isinstance(column.type, Boolean):
                message = _(u"this field can't be empty")
                validator = validators.Required(message=message)
                kwargs['validators'].append(validator)
            kwargs['default'] = sa_utils.get_column_default_value(column)
            if isinstance(col_spec, FileColumnSpec):
                converter = sa_converter.converters["File"]
            else:
                converter = sa_converter.get_converter(column)

            if converter is None:
                return None

            return converter(model=self.modell.model, column=column)


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
