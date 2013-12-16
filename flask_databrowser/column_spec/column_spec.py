# -*- coding: utf-8 -*-
from flask.ext.data_browser.pseudo_field import PseudoField
from flask.ext.data_browser.extra_widgets import PlainText


class ColumnSpec(object):
    def __init__(self, col_name, doc=None,
                 formatter=None, label=None, widget=PlainText(),
                 css_class="", render_kwargs={}):
        self.col_name = col_name
        self.formatter = formatter
        self.doc = doc
        self.label = col_name.replace('_', ' ').title if label is None else \
            label
        self.css_class = css_class
        self.render_kwargs = render_kwargs

    @property
    def field(self):
        return PseudoField(self.label, self.col_name,
                           widget=self.widget,
                           description=self.doc,
                           render_kwargs=self.render_kwargs)

PlainTextColumnSpec = ColumnSpec  # alias to ColumnSpec
