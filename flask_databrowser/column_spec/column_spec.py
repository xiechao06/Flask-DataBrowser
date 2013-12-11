# -*- coding: utf-8 -*-


class ColumnSpec(object):
    def __init__(self, col_name, doc=None,
                 formatter=None, label=None, css_class="control-text",
                 trunc=None, form_width_class=None):
        self.col_name = col_name
        self.formatter = formatter
        self.doc = doc
        self.label = label
        self.css_class = css_class
        self.trunc = trunc
        self.form_width_class = form_width_class

    @property
    def field(self):
        raise NotImplementedError


PlainTextColumnSpec = ColumnSpec  # alias to ColumnSpec
