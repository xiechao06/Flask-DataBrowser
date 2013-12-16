"""
Useful form fields for use with SQLAlchemy ORM.
"""
import operator

from wtforms import widgets, Field
from wtforms.fields import SelectFieldBase
from wtforms.validators import ValidationError
from flask.ext.databrowser.extra_widgets import Select2Widget

try:
    from sqlalchemy.orm.util import identity_key

    has_identity_key = True
except ImportError:
    has_identity_key = False

__all__ = ('QuerySelectField', 'QuerySelectMultipleField')


class OptGroupWidget(object):
    def __call__(self, field, **kwargs):
        from flask.ext.databrowser.extra_widgets import Select2Widget
        return Select2Widget.render_optgroup(field.label.text, field.choices)


class GroupedSelectField(SelectFieldBase):
    optgroup_widget = OptGroupWidget()

    def __init__(self, label=None, validators=None, option_widget=None, **kwargs):
        self.grouper = kwargs.pop("grouper", None)
        super(GroupedSelectField, self).__init__(label, validators, option_widget, **kwargs)

    def iter_choices(self):
        """
        Provides data for choice widget rendering. Must return a sequence or
        iterable of (value, label, selected) tuples.
        """
        raise NotImplementedError()

    def __iter__(self):
        if self.grouper:
            optgroup_opts = dict(widget=self.optgroup_widget, _name=self.name, _form=None)
            i = 0
            for grouplabel, choices in self.iter_optgroups():
                og = self._OptGroup(label=grouplabel, **optgroup_opts)
                og.process(None)
                og.choices = choices #(o(value, label, selected, i) for value, label, selected in choices)
                yield og
                i += 1
        else:
            super(GroupedSelectField, self).__iter__()

    class _OptGroup(Field):
        def _value(self):
            return self.data

    def iter_optgroups(self):
        raise NotImplementedError()


class QuerySelectField(GroupedSelectField):
    """
    Will display a select drop-down field to choose between ORM results in a
    sqlalchemy `Query`.  The `data` property actually will store/keep an ORM
    model instance, not the ID. Submitting a choice which is not in the query
    will result in a validation error.

    This field only works for queries on models whose primary key column(s)
    have a consistent string representation. This means it mostly only works
    for those composed of string, unicode, and integer types. For the most
    part, the primary keys will be auto-detected from the model, alternately
    pass a one-argument callable to `get_pk` which can return a unique
    comparable key.

    The `query` property on the field can be set from within a view to assign
    a query per-instance to the field. If the property is not set, the
    `query_factory` callable passed to the field constructor will be called to
    obtain a query.

    Specify `get_label` to customize the label associated with each option. If
    a string, this is the name of an attribute on the model object to use as
    the label text. If a one-argument callable, this callable will be passed
    model instance and expected to return the label text. Otherwise, the model
    object's `__str__` or `__unicode__` will be used.

    If `allow_blank` is set to `True`, then a blank choice will be added to the
    top of the list. Selecting this choice will result in the `data` property
    being `None`. The label for this blank choice can be set by specifying the
    `blank_text` parameter.
    """
    widget = widgets.Select()

    def __init__(self, label=None, validators=None, query_factory=None,
                 get_pk=None, get_label=None, allow_blank=False,
                 blank_text=u'', opt_filter=None, **kwargs):
        super(QuerySelectField, self).__init__(label, validators, **kwargs)
        self.query_factory = query_factory

        if get_pk is None:
            if not has_identity_key:
                raise Exception('The sqlalchemy identity_key function could not be imported.')
            self.get_pk = get_pk_from_identity
        else:
            self.get_pk = get_pk

        if get_label is None:
            self.get_label = lambda x: x
        elif isinstance(get_label, basestring):
            self.get_label = operator.attrgetter(get_label)
        else:
            self.get_label = get_label

        self.allow_blank = allow_blank
        self.blank_text = blank_text
        self.query = None
        self._object_list = None
        self.opt_filter = opt_filter or (lambda obj: True)
        self._group_list = []
        self._values = None

    def _get_data(self):
        if self._formdata is not None:
            for pk, obj in self._get_object_list():
                if pk == self._formdata:
                    self._set_data(obj)
                    break
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def _get_object_list(self):
        if self._object_list is None:
            get_pk = self.get_pk
            self._object_list = list((unicode(get_pk(obj)), obj) for obj in self._query_objects())
        return self._object_list

    def _query_objects(self):
        if self._values is None:
            query = self.query or self.query_factory()
            self._values = list(obj for obj in query if self.opt_filter(obj))
        return self._values

    def iter_choices(self):
        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is None)

        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), obj == self.data)

    def _get_group_list(self):
        if not self._group_list:
            if self.grouper:
                import itertools

                for grouper, values in itertools.groupby(sorted(self._query_objects(), key=self.grouper),
                                                         key=self.grouper):
                    self._group_list.append((grouper, list(values)))

            else:
                self._group_list.append((None, self._query_objects()))
        return self._group_list

    def iter_optgroups(self):
        for grouplabel, choices in self._get_group_list():
            cs = []
            for obj in choices:
                cs.append((self.get_pk(obj), self.get_label(obj), obj == self.data))
            yield (grouplabel, cs)

    def process_formdata(self, valuelist):
        if valuelist:
            if self.allow_blank and valuelist[0] == u'__None':
                self.data = None
            else:
                self._data = None
                self._formdata = valuelist[0]

    def pre_validate(self, form):
        if not self.allow_blank or self.data is not None:
            for pk, obj in self._get_object_list():
                if self.data == obj:
                    break
            else:
                raise ValidationError(self.gettext(u'Not a valid choice'))


class QuerySelectMultipleField(QuerySelectField):
    """
    Very similar to QuerySelectField with the difference that this will
    display a multiple select. The data property will hold a list with ORM
    model instances and will be an empty list when no value is selected.

    If any of the items in the data list or submitted form data cannot be
    found in the query, this will result in a validation error.
    """
    widget = widgets.Select(multiple=True)

    def __init__(self, label=None, validators=None, default=None, opt_filter=None, **kwargs):
        if default is None:
            default = []
        super(QuerySelectMultipleField, self).__init__(label, validators, default=default, opt_filter=opt_filter,
                                                       **kwargs)
        self._invalid_formdata = False

    def _get_data(self):
        formdata = self._formdata
        if formdata is not None:
            data = []
            for pk, obj in self._get_object_list():
                if not formdata:
                    break
                elif pk in formdata:
                    formdata.remove(pk)
                    data.append(obj)
            if formdata:
                self._invalid_formdata = True
            self._set_data(data)
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def iter_choices(self):
        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), obj in self.data)

    def iter_optgroups(self):
        for grouplabel, choices in self._get_group_list():
            cs = []
            for obj in choices:
                cs.append((self.get_pk(obj), self.get_label(obj), obj in self.data))
            yield (grouplabel, cs)

    def process_formdata(self, valuelist):
        self._formdata = set(valuelist)

    def pre_validate(self, form):
        if self._invalid_formdata:
            raise ValidationError(self.gettext(u'Not a valid choice'))
        elif self.data:
            obj_list = list(x[1] for x in self._get_object_list())
            for v in self.data:
                if v not in obj_list:
                    raise ValidationError(self.gettext('Not a valid choice'))


#TODO should be more elegant
class GroupedQuerySelectField(QuerySelectField):
    def __init__(self, col_spec, *args, **kwargs):
        super(GroupedQuerySelectField, self).__init__(*args, **kwargs)
        self.col_spec = col_spec

    def __call__(self, **kwargs):
        grouper = Select2Widget()
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


def get_pk_from_identity(obj):
    # TODO: Remove me
    cls, key = identity_key(instance=obj)
    return u':'.join(unicode(x) for x in key)
