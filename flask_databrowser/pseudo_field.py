# -*- coding: UTF-8 -*-
from wtforms import fields
from . import extra_widgets


class PseudoField(fields.Field):
    '''
    this is actually not wtforms' field, but a field only used to generate
    html
    '''
    def __init__(self, label, id, widget, description='', render_kwargs='',
                 **kwargs):
        super(PseudoField, self).__init__(label=label, id=id, widget=widget,
                                          **kwargs)
        self.description = description
        self.render_kwargs = render_kwargs

    def __call__(self, **kwargs):
        css_class = self.render_kwargs.get('css_class', '')
        if 'class' in kwargs:
            kwargs["class"] = " ".join([kwargs["class"], css_class])
        else:
            kwargs["class"] = css_class
        return self.widget(self, **kwargs)

    @property
    def __read_only__(self):
        return True

    @property
    def __render_kwargs__(self):
        return self.render_kwargs

    def process_data(self, value):
        self.data = value
        # TODO more need
        if not self.widget:
            self.widget = extra_widgets.PlainText()

    def _value(self):
        return self.data
