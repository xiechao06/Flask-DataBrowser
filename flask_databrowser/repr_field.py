# -*- coding: UTF-8 -*-
from wtforms.validators import Required
from wtforms_components import Unique
from wtforms import widgets


class ReprField(object):
    '''
    this is a field to generate html
    '''
    def __init__(self, field):
        self.field = field

    def __getattr__(self, item):
        return getattr(self.field, item)

    def __call__(self, *args, **kwargs):
        if self.field.type == 'BooleanField':
            form_control_div = "<div class='checkbox'>%s</div>"
            return form_control_div % self.field(**kwargs)
        else:
            def _add_class(kwargs, _class):
                kwargs["class"] = " ".join((kwargs["class"], _class)) if kwargs.get("class") else _class

            _add_class(kwargs, "form-control" if self.is_input_field else "form-control-static")

            return self.field(**kwargs)

    @property
    def is_input_field(self):
        allowable_widget_types = (widgets.Input, widgets.Select,
                                  widgets.TextArea)
        return isinstance(self.field.widget, allowable_widget_types) \
            and self.field.type not in ["ReadOnlyField", "FileField"]

    @property
    def form_width_class(self):
        initial = getattr(self.field, "form_width_class", "")
        if initial:
            return initial
        if self.is_input_field:
            return "col-lg-3"
        label = getattr(self.field, "label")
        if getattr(label, "text", None) or label.get("text"):
            return "col-lg-10"
        return "col-lg-12"

    @property
    def required(self):
        return hasattr(self, 'validators') and \
            any(isinstance(v, Required) for v in self.validators)

    @property
    def unique(self):
        return hasattr(self, "validators") and \
            any(isinstance(v, Unique) for v in self.validators)
