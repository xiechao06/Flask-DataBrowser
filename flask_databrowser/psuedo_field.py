# -*- coding: UTF-8 -*-
from wtforms import fields


class PseudoField(fields.Field):
    '''
    this is actually not wtforms' field, but a field only used to generate
    html
    '''
    def __init__(self, label, name, widget, description='', render_kwargs=''):
        self.label = label
        self.name = name
        self.widget = widget
        self.description = description
        self.render_kwargs = render_kwargs

    def __call__(self, **kwargs):
        css_class = self.render_kwargs.get('css_class')
        if 'class' in kwargs:
            kwargs["class"] = " ".join([kwargs["class"], css_class])
        else:
            kwargs["class"] = css_class
        return self.widget(self, **kwargs)

    @property
    def __read_only__(self):
        return True

    def _value(self):
        return self.data
