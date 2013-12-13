# -*- coding: utf-8 -*-
from flask.ext.databrowser.column_spec import ColumnSpec


class LinkColumnSpec(ColumnSpec):

    def __init__(self, col_name, anchor="", doc=None, formatter=None,
                 label=None, css_class="", render_kwargs={}):
        super(LinkColumnSpec, self).__init__(col_name, doc=doc,
                                             formatter=formatter, label=label,
                                             css_class="",
                                             render_kwargs=render_kwargs)
        self.anchor = anchor

    @property
    def field(self):
        #TODO unimplemented
        pass
