# -*- coding: utf-8 -*-
from flask.ext.databrowser.column_spec import ColumnSpec


class ListColumnSpec(ColumnSpec):

    def __init__(self, col_name, item_col_spec=None, doc=None,
                 formatter=None, label=None, css_class="",
                 compressed=False, item_css_class="", form_width_class=None):
        super(ListColumnSpec, self).__init__(col_name, doc=doc,
                                             formatter=formatter, label=label,
                                             css_class=css_class,
                                             form_width_class=form_width_class)
        self.item_col_spec = item_col_spec
        self.compressed = compressed
        self.item_css_class = item_css_class

    @property
    def field(self):
        #TODO unimplemented
        pass
