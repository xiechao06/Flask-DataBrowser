# -*- coding: utf-8 -*-
from flask.ext.databrowser.column_spec import ColumnSpec


class ImageColumnSpec(ColumnSpec):

    def __init__(self, col_name, alt="", doc=None, formatter=None,
                 label=None, render_kwargs={}):
        super(ImageColumnSpec, self).__init__(col_name, doc=doc,
                                              formatter=formatter, label=label,
                                              render_kwargs=render_kwargs)
        self.alt = alt

    @property
    def field(self):
        #TODO unimplemented
        pass
