# -*- coding: utf-8 -*-
from flask.ext.databrowser.pseudo_field import PseudoField


class ColSpec(object):

    # tell I am not an input
    as_input = False
    disabled = True

    def __init__(self, col_name, label=None, doc=None,
                 formatter=None, widget=None,
                 css_class="", render_kwargs={}):
        self.col_name = col_name
        self.formatter = formatter
        self.doc = doc
        self.label = col_name.replace('_', ' ').title() if label is None else \
            label
        self.css_class = css_class
        self.widget = widget
        self.render_kwargs = render_kwargs

    def make_field(self, record=None, model_view=None):
        return PseudoField(self.label, self.col_name,
                           record=record,
                           model_view=model_view,
                           widget=self.widget,
                           description=self.doc,
                           col_spec=self,
                           render_kwargs=self.render_kwargs)

PlainTextColumnSpec = ColSpec  # alias to ColSpec
