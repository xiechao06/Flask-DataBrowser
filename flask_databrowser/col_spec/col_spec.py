# -*- coding: utf-8 -*-
from flask.ext.databrowser.pseudo_field import PseudoField


class ColSpec(object):

    # tell I am not an input
    as_input = False
    disabled = True

    def __init__(self, col_name, doc=None,
                 formatter=None, label=None, widget=None,
                 css_class="", render_kwargs={}):
        self.col_name = col_name
        self.formatter = formatter
        self.doc = doc
        self.label = col_name.replace('_', ' ').title() if label is None else \
            label
        self.css_class = css_class
        self.widget = widget
        self.render_kwargs = render_kwargs

    @property
    def field(self):
        return PseudoField(self.label, self.col_name,
                           widget=self.widget,
                           description=self.doc,
                           render_kwargs=self.render_kwargs)

PlainTextColumnSpec = ColSpec  # alias to ColSpec
