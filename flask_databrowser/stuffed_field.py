# -*- coding: UTF-8 -*-
from wtforms.validators import Required
from wtforms_components import Unique
from wtforms import widgets


class StuffedField(object):
    '''
    this is a field to generate html
    '''
    def __init__(self, col_spec, focus_set):
        self._col_spec = col_spec
        self.field = col_spec.field
        self._auto_focus = not focus_set and not self._col_spec.disabled

    def __getattr__(self, item):
        return getattr(self.field, item)

    def __call__(self, *args, **kwargs):
        if self._col_spec.disabled:
            kwargs['disabled'] = True
        if self._auto_focus:
            kwargs['autofocus'] = 'autofocus'
        if self.__required__:
            kwargs['required'] = True
        return self.field(**kwargs)

    @property
    def __read_only__(self):
        return self._col_spec.disabled

    @property
    def __as_input__(self):
        allowable_widget_types = (widgets.Input, widgets.Select,
                                  widgets.TextArea)
        return isinstance(self.field.widget, allowable_widget_types) \
            and self.field.type not in ["ReadOnlyField", "FileField"]

    @property
    def __required__(self):
        return hasattr(self, 'validators') and \
            any(isinstance(v, Required) for v in self.validators)

    @property
    def __unique__(self):
        return hasattr(self, "validators") and \
            any(isinstance(v, Unique) for v in self.validators)
