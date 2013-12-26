# -*- coding: UTF-8 -*-
from wtforms.validators import Required
from wtforms_components import Unique
from wtforms import widgets, validators
from flask_upload2.widgets import FileInput


class StuffedField(object):
    '''
    this is a proxy of BOUND field used to generate html
    '''
    def __init__(self, obj, bound_field, col_spec, focus_set):
        self.col_spec = col_spec
        self.field = bound_field
        self._auto_focus = not focus_set and not self.col_spec.disabled
        self._render_kwargs = col_spec.render_kwargs
        #TODO set flags here
        # override default widget
        if hasattr(col_spec, 'override_widget'):
            self.field.widget = col_spec.override_widget(obj)
        if not col_spec.disabled:
            self.create_url = col_spec.remote_create_url
        self.__read_only__ = self.col_spec.disabled

    def __getattr__(self, item):
        return getattr(self.field, item)

    def __call__(self, *args, **kwargs):
        kwargs.update(**self._render_kwargs.get('html_params', {}))
        if self.__read_only__:
            kwargs['disabled'] = True
            self.field.validators = [v for v in self.field.validators if not
                                     isinstance(v, validators.DataRequired)]
        if self._auto_focus:
            kwargs['autofocus'] = 'autofocus'
        if self.__required__ and not self.col_spec.disabled:
            kwargs['required'] = True
        return self.field(**kwargs)

    @property
    def __auto_focus__(self):
        return self._auto_focus

    @property
    def __render_kwargs__(self):
        return self._render_kwargs

    @property
    def __as_input__(self):
        allowable_widget_types = (widgets.Input, widgets.Select,
                                  widgets.TextArea, FileInput)
        return isinstance(self.field.widget, allowable_widget_types)

    @property
    def __required__(self):
        return hasattr(self, 'validators') and \
            any(isinstance(v, Required) for v in self.validators)

    @property
    def __unique__(self):
        return hasattr(self, "validators") and \
            any(isinstance(v, Unique) for v in self.validators)
