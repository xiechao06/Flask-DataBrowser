# -*- coding: UTF-8 -*-
from flask import request
from wtforms import fields
from . import extra_widgets
from flask.ext.databrowser.constants import BACK_URL_PARAM


class PseudoField(fields.Field):
    '''
    this is actually not wtforms' field, but a field only used to generate
    html
    '''
    def __init__(self, label, id, widget, record, col_spec, model_view,
                 description='',
                 render_kwargs='', **kwargs):
        super(PseudoField, self).__init__(label=label, id=id, widget=widget,
                                          **kwargs)
        self.description = description
        self.render_kwargs = render_kwargs
        self.col_spec = col_spec
        self.model_view = model_view
        self.record = record

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
        if not self.widget:
            self.widget = extra_widgets.PlainText()
        if self.col_spec.formatter:
            self.data = self.col_spec.formatter(self.data, self.record)
        elif self.col_spec.col_name == self.model_view.modell.primary_key:
            href = self.model_view.url_for_object(self.record,
                                                  **{BACK_URL_PARAM:
                                                     request.url})
            self.data = (value, href)
            self.widget = extra_widgets.Link()

    def _value(self):
        return self.data
