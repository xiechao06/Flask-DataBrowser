# -*- coding: utf-8 -*-
from flask.ext.databrowser.col_spec import ColSpec


class ListColumnSpec(ColSpec):

    def __init__(self, col_name, item_col_spec=None, doc=None,
                 formatter=None, label=None,
                 compressed=False, item_css_class="", render_kwargs={}):
        super(ListColumnSpec, self).__init__(col_name, doc=doc,
                                             formatter=formatter, label=label,
                                             render_kwargs=render_kwargs)
        self.item_col_spec = item_col_spec
        self.compressed = compressed
        self.item_css_class = item_css_class

    @property
    def field(self):
        #TODO unimplemented
        pass
