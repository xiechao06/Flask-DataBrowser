# -*- coding: UTF-8 -*-
import functools
import inspect
import copy

from wtforms import fields, validators
from sqlalchemy import Boolean, Column

from . import form
from .validators import Unique
from .fields import QuerySelectField, QuerySelectMultipleField
from flask.ext.databrowser.column_spec import InputColumnSpec, PlaceHolderColumnSpec, FileColumnSpec
from flask.ext.databrowser.utils import get_description, get_primary_key, make_disabled_field
from flask.ext.babel import _

try:
    # Field has better input parsing capabilities.
    from wtforms.ext.dateutil.fields import DateTimeField
except ImportError:
    from wtforms.fields import DateTimeField


def converts(*args):
    def _inner(func):
        func._converter_for = frozenset(args)
        return func

    return _inner


class ModelConverterBase(object):
    def __init__(self, converters=None, use_mro=True):
        self.use_mro = use_mro

        if not converters:
            converters = {}

        for name in dir(self):
            obj = getattr(self, name)
            if hasattr(obj, '_converter_for'):
                for classname in obj._converter_for:
                    converters[classname] = obj

        self.converters = converters

    def get_converter(self, column):
        if self.use_mro:
            types = inspect.getmro(type(column.type))
        else:
            types = [type(column.type)]

        # Search by module + name
        for col_type in types:
            type_string = '%s.%s' % (col_type.__module__, col_type.__name__)

            if type_string in self.converters:
                return self.converters[type_string]

        # Search by name
        for col_type in types:
            if col_type.__name__ in self.converters:
                return self.converters[col_type.__name__]

        return None


class InlineFormAdmin(object):
    """
        Settings for inline form administration.

        You can use this class to customize displayed form.
        For example::

            class MyUserInfoForm(InlineFormAdmin):
                form_columns = ('name', 'email')
    """
    _defaults = ['form_columns', 'form_excluded_columns', 'form_args']

    def __init__(self, model, **kwargs):
        """
            Constructor

            :param model:
                Target model class
            :param kwargs:
                Additional options
        """
        self.model = model

        for k in self._defaults:
            if not hasattr(self, k):
                setattr(self, k, None)

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def postprocess_form(self, form_class):
        """
            Post process form. Use this to contribute fields.

            For example::

                class MyInlineForm(InlineFormAdmin):
                    def postprocess_form(self, form):
                        form.value = wtf.TextField('value')
                        return form

                class MyAdmin(ModelView):
                    inline_models = (MyInlineForm(ValueModel),)
        """
        return form_class


class AdminModelConverter(ModelConverterBase):
    """
        SQLAlchemy model to form converter
    """

    def __init__(self, session, view):
        super(AdminModelConverter, self).__init__()

        self.session = session
        self.view = view

    def _get_label(self, name, field_args, col_spec):
        """
            Label for field name. If it is not specified explicitly,
            then the views prettify_name method is used to find it.

            :param field_args:
                Dictionary with additional field arguments
        """
        if col_spec and col_spec.label is not None:
            return col_spec.label
        if 'label' in field_args:
            return field_args['label']

        column_labels = getattr(self.view, '__column_labels__', {})

        if column_labels:
            return column_labels.get(name)

        return self.view.prettify_name(name)


    def _get_field_override(self, name):
        form_overrides = getattr(self.view, 'form_overrides', None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def add_grouper(self, col_spec):
        if hasattr(col_spec.group_by, "__call__"):
            return col_spec.group_by
        elif hasattr(col_spec.group_by, "property"):
            column = col_spec.group_by.property
            if hasattr(col_spec.group_by, "is_mapper") and col_spec.group_by.is_mapper:
                column = get_primary_key(column)
            return lambda x: getattr(x, column.key)
        else:
            return lambda x: x

    def convert(self, model, mapper, prop, field_args, hidden_pk, col_spec=None):
        # note!!! use copy here, otherwise col_spec.validators will be changed
        kwargs = {
            'validators': copy.copy(col_spec.validators) if col_spec else [],
            'filters': []
        }

        if field_args:
            kwargs.update(field_args)

        # Check if it is relation or property
        if hasattr(prop, 'direction'):
            remote_model = prop.mapper.class_
            local_column = prop.local_remote_pairs[0][0]

            kwargs['label'] = self._get_label(prop.key, kwargs, col_spec)
            kwargs['description'] = get_description(self.view, prop.key, col_spec)

            kwargs['get_label'] = functools.partial(
                self._get_label_func(prop.key, kwargs) or (
                    lambda x, model: unicode(x)),
                model=model)

            if not local_column.foreign_keys or local_column.nullable: # backref shouldn't be validated
                kwargs['validators'].append(validators.Optional())
            elif prop.direction.name != 'MANYTOMANY':
                kwargs['validators'].append(validators.Required(message=_(u"this field can't be empty")))

            # Override field type if necessary
            override = self._get_field_override(prop.key)
            if override:
                return override(**kwargs)

            # Contribute model-related parameters
            if 'allow_blank' not in kwargs and local_column.foreign_keys:
                kwargs['allow_blank'] = local_column.nullable
            if 'query_factory' not in kwargs:
                if col_spec and col_spec.filter_:
                    kwargs['query_factory'] = lambda: col_spec.filter_(self.session.query(remote_model))
                else:
                    kwargs['query_factory'] = lambda: self.session.query(remote_model)

            if col_spec and col_spec.opt_filter:
                kwargs['opt_filter'] = col_spec.opt_filter

            if prop.direction.name == 'MANYTOONE':
                if col_spec and col_spec.group_by:
                    session = self.session

                    class QuerySelectField_(QuerySelectField):

                        def __init__(self, col_spec, *args, **kwargs):
                            super(QuerySelectField_, self).__init__(*args, **kwargs)
                            self.col_spec = col_spec

                        def __call__(self, **kwargs):
                            grouper = form.Select2Widget()

                            class FakeField(object):

                                def __init__(self, name, data):
                                    self.name = name
                                    self.id = "_" + name
                                    self.data = data

                                def iter_choices(self):
                                    model = col_spec.group_by.property.mapper.class_
                                    pk = get_primary_key(model)
                                    for row in session.query(col_spec.group_by.property.mapper.class_).all():
                                        yield getattr(row, pk), unicode(row), getattr(row, pk) == self.data

                            grouper_kwargs = {}
                            if kwargs.get("class"):
                                grouper_kwargs["class"] = kwargs["class"]
                            if kwargs.get("disabled"):
                                grouper_kwargs["disabled"] = True
                            s = grouper(FakeField(self.col_spec.grouper_input_name,
                                                  getattr(self.data,
                                                          col_spec.group_by.property.local_remote_pairs[0][0].name)),
                                        **grouper_kwargs) + "<div class='text-center'>--</div>"
                            s += super(QuerySelectField_, self).__call__(**kwargs)
                            return s

                    return QuerySelectField_(col_spec, widget=form.Select2Widget(), **kwargs)
                return QuerySelectField(widget=form.Select2Widget(),
                                        **kwargs)
            elif prop.direction.name == 'ONETOMANY':
                # Skip backrefs
                if not local_column.foreign_keys and getattr(self.view, 'column_hide_backrefs', False):
                    return None
                if col_spec and col_spec.group_by:
                    kwargs["grouper"] = self.add_grouper(col_spec)

                return QuerySelectMultipleField(
                    widget=form.Select2Widget(multiple=True),
                    **kwargs)
            elif prop.direction.name == 'MANYTOMANY':
                if col_spec and col_spec.group_by:
                    kwargs["grouper"] = self.add_grouper(col_spec)

                return QuerySelectMultipleField(
                    widget=form.Select2Widget(multiple=True),
                    **kwargs)
        else:
            # Ignore pk/fk
            if hasattr(prop, 'columns'):
                # Check if more than one column mapped to the property
                if len(prop.columns) != 1:
                    raise TypeError('Can not convert multiple-column properties (%s.%s)' % (model, prop.key))

                # Grab column
                column = prop.columns[0]

                # Do not display foreign keys - use relations
                if column.foreign_keys:
                    return None

                # Only display "real" columns
                if not isinstance(column, Column):
                    return None

                unique = False

                if column.primary_key:
                    if hidden_pk:
                        # If requested to add hidden field, show it
                        return fields.HiddenField()
                    else:
                        kwargs['validators'].append(Unique(self.session,
                                                           model,
                                                           column, message=_(
                                "This field must be unique, but it already exists!")))
                        unique = True

                # If field is unique, validate it
                if column.unique and not unique:
                    kwargs['validators'].append(Unique(self.session,
                                                       model,
                                                       column,
                                                       message=_("This field must be unique, but it already exists!")))

                if not column.nullable and not isinstance(column.type, Boolean):
                    kwargs['validators'].append(validators.Required(message=_(u"this field can't be empty")))

                # Apply label and description if it isn't inline form field
                if self.view.model == mapper.class_:
                    kwargs['label'] = self._get_label(prop.key, kwargs, col_spec)
                    kwargs['description'] = get_description(self.view, prop.key, col_spec)

                # Figure out default value
                default = getattr(column, 'default', None)
                value = None

                if default is not None:
                    value = getattr(default, 'arg', None)

                    if value is not None:
                        if getattr(default, 'is_callable', False):
                            value = value(None)
                        else:
                            if not getattr(default, 'is_scalar', True):
                                value = None

                if value is not None:
                    kwargs['default'] = value

                # Check nullable
                if column.nullable:
                    kwargs['validators'].append(validators.Optional())

                # Override field type if necessary
                override = self._get_field_override(prop.key)
                if override:
                    return override(**kwargs)

                # Run converter
                if isinstance(col_spec, FileColumnSpec):
                    converter = self.converters["File"]
                else:
                    converter = self.get_converter(column)

                if converter is None:
                    return None
                return converter(model=model, mapper=mapper, prop=prop,
                                 column=column, field_args=kwargs)

        return None

    @classmethod
    def _string_common(cls, column, field_args, **extra):
        if column.type.length:
            field_args['validators'].append(validators.Length(max=column.type.length,
                                                              message=_(u"length exceeds %(max_length)%d",
                                                                        max_length=column.type.length)))

    @converts('String', 'Unicode')
    def conv_String(self, column, field_args, **extra):
        if hasattr(column.type, 'enums'):
            field_args['validators'].append(validators.AnyOf(column.type.enums,
                                                             message=_(u"value of this field must be %(values)s",
                                                                       values=", ".join(
                                                                           str(i) for i in column.type.enums[:-1])) +
                                                                     _(u" or %(last_value)s",
                                                                       last_value=column.type.enums[-1]) if (
                                                             len(column.type.enums) > 1) else ""))
            field_args['choices'] = [(f, f) for f in column.type.enums]
            return form.Select2Field(**field_args)
        self._string_common(column=column, field_args=field_args, **extra)

        class MyTextField(fields.TextField):
            def __call__(self, **kwargs):
                if column.type.length:
                    kwargs["maxlength"] = column.type.length
                if self._value() is None and column.default is not None:
                    kwargs['value'] = column.default.arg
                return super(MyTextField, self).__call__(**kwargs)

        return MyTextField(**field_args)

    @converts('File')
    def conv_File(self, column, field_args, **extra):
        return fields.FileField(**field_args)

    @converts('Text', 'UnicodeText',
              'sqlalchemy.types.LargeBinary', 'sqlalchemy.types.Binary')
    def conv_Text(self, field_args, **extra):
        self._string_common(field_args=field_args, **extra)
        return fields.TextAreaField(**field_args)

    @converts('Boolean')
    def conv_Boolean(self, field_args, **extra):
        return fields.BooleanField(**field_args)

    @converts('Date')
    def convert_date(self, field_args, **extra):
        field_args['widget'] = form.DatePickerWidget()
        return fields.DateField(**field_args)

    @converts('DateTime')
    def convert_datetime(self, field_args, **extra):
        field_args['widget'] = form.DateTimePickerWidget()
        return DateTimeField(**field_args)

    @converts('Time')
    def convert_time(self, field_args, **extra):
        return form.TimeField(**field_args)

    @converts('Integer', 'SmallInteger')
    def handle_integer_types(self, column, field_args, **extra):

        unsigned = getattr(column.type, 'unsigned', False)
        if unsigned:
            field_args['validators'].append(validators.NumberRange(min=0, message=_(u"this field must bigger than 0")))

        class MyIntegerField(fields.IntegerField):
            def __call__(self, **kwargs):
                kwargs['type'] = 'number'
                return super(MyIntegerField, self).__call__(**kwargs)

        return MyIntegerField(**field_args)
        #return fields.IntegerField(**field_args)

    @converts('Numeric', 'Float')
    def handle_decimal_types(self, column, field_args, **extra):
        places = getattr(column.type, 'scale', 2)
        if places is not None:
            field_args['places'] = places
        return fields.DecimalField(**field_args)

    @converts('databases.mysql.MSYear')
    def conv_MSYear(self, field_args, **extra):
        field_args['validators'].append(
            validators.NumberRange(min=1901, max=2155, message=_(u"this field must between 1901 and 2155")))
        return fields.TextField(**field_args)

    @converts('databases.postgres.PGInet', 'dialects.postgresql.base.INET')
    def conv_PGInet(self, field_args, **extra):
        field_args.setdefault('label', u'IP Address')
        field_args['validators'].append(validators.IPAddress(message=_(u"this field must be a valid IP address")))
        return fields.TextField(**field_args)

    @converts('dialects.postgresql.base.MACADDR')
    def conv_PGMacaddr(self, field_args, **extra):
        field_args.setdefault('label', u'MAC Address')
        field_args['validators'].append(validators.MacAddress(message=_(u"this field must be a valid MAC address")))
        return fields.TextField(**field_args)

    @converts('dialects.postgresql.base.UUID')
    def conv_PGUuid(self, field_args, **extra):
        field_args.setdefault('label', u'UUID')
        field_args['validators'].append(validators.UUID(message=_(u"this field must be a valid UUID")))
        return fields.TextField(**field_args)

    @converts('sqlalchemy.dialects.postgresql.base.ARRAY')
    def conv_ARRAY(self, field_args, **extra):
        return form.Select2TagsField(save_as_list=True, **field_args)


    def _get_label_func(self, name, field_args):
        if 'get_label' in field_args:
            return field_args['get_label']

        column_formatters = getattr(self.view, '__column_formatters__')

        if column_formatters:
            return column_formatters.get(name)

        return None

# Get list of fields and generate form
def get_form(model, converter,
             base_class=form.BaseForm,
             only=None, exclude=None,
             field_args=None,
             hidden_pk=False,
             ignore_hidden=True):
    """
        Generate form from the model.

        :param model:
            Model to generate form from
        :param converter:
            Converter class to use
        :param base_class:
            Base form class
        :param only:
            Include fields
        :param exclude:
            Exclude fields
        :param field_args:
            Dictionary with additional field arguments
        :param hidden_pk:
            Generate hidden field with model primary key or not
        :param ignore_hidden:
            If set to True (default), will ignore properties that start with underscore
    """

    # TODO: Support new 0.8 API
    if not hasattr(model, '_sa_class_manager'):
        raise TypeError('model must be a sqlalchemy mapped model')

    mapper = model._sa_class_manager.mapper
    field_args = field_args or {}

    # (property_name, property, column_spec)+
    properties = ((p.key, p, None) for p in mapper.iterate_properties)

    # TODO these codes should be rewritten, what a mess
    if only:
        props = dict(prop[:2] for prop in properties)

        def find(name):
            # Try to look it up in properties list first
            p = props.get(name)
            if p is not None:
                # Try to see if it is proxied property
                if hasattr(p, '_proxied_property'):
                    return p._proxied_property

                return p

            # If it is hybrid property or alias, look it up in a model itself
            p = getattr(model, name, None)
            if p is not None and hasattr(p, 'property'):
                return p.property

            raise ValueError('Invalid model property name %s.%s' % (model, name))

        # Filter properties while maintaining property order in 'only' list
        properties = []
        for x in only:
            if isinstance(x, InputColumnSpec) or isinstance(x, FileColumnSpec) or (
                    isinstance(x, PlaceHolderColumnSpec) and x.as_input):
                properties.append((x.col_name, find(x.col_name), x))
            else:
                properties.append((x, find(x), None))
    elif exclude:
        properties = (x for x in properties if x[0] not in exclude)

    field_dict = {}
    for name, prop, col_spec in properties:
        # Ignore protected properties
        if ignore_hidden and name.startswith('_'):
            continue
        field = converter.convert(model, mapper, prop, field_args.get(name), hidden_pk, col_spec)
        if field is not None:
            if col_spec and not isinstance(col_spec, PlaceHolderColumnSpec) and getattr(col_spec, "read_only", None):
                field = make_disabled_field(field)
            field_dict[name] = field

    return type(model.__name__ + 'Form', (base_class, ), field_dict)


class InlineModelConverterBase(object):
    def __init__(self, view):
        """
            Base constructor

            :param view:
                View class
        """
        self.view = view

    def get_label(self, info, name):
        """
            Get inline model field label

            :param info:
                Inline model info
            :param name:
                Field name
        """
        form_name = getattr(info, 'form_label', None)
        if form_name:
            return form_name

        column_labels = getattr(self.view, 'column_labels', None)

        if column_labels and name in column_labels:
            return column_labels[name]

        return None

    def get_info(self, p):
        """
            Figure out InlineFormAdmin information.

            :param p:
                Inline model. Can be one of:

                 - ``tuple``, first value is related model instance,
                 second is dictionary with options
                 - ``InlineFormAdmin`` instance
                 - Model class
        """
        if isinstance(p, tuple):
            return InlineFormAdmin(p[0], **p[1])
        elif isinstance(p, InlineFormAdmin):
            return p

        return None

