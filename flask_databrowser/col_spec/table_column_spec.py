# -*- coding: utf-8 -*-
from flask.ext.databrowser.col_spec import ColSpec


class TableColumnSpec(ColSpec):

    def __init__(self, col_name, col_specs=[], anchor="", doc=None,
                 formatter=None, label=None,
                 css_class="table table-condensed table-bordered",
                 sum_fields=[], preprocess=None):
        super(TableColumnSpec, self).__init__(col_name, doc=doc,
                                              formatter=formatter, label=label,
                                              css_class=css_class)
        self.anchor = anchor
        self.col_specs = col_specs
        self.sum_fields = sum_fields
        self.preprocess = preprocess

    def __iter__(self):
        return iter(self.col_specs)

    @property
    def field(self):
        #TODO unimplemented
        pass
