# -*- coding: utf-8 -*-
from flask.ext.databrowser.column_spec import ColumnSpec


class PlaceHolderColumnSpec(ColumnSpec):

    def __init__(self, col_name, template_fname, label=None, doc=None,
                 form_width_class=None):
        super(PlaceHolderColumnSpec, self).__init__(col_name, label=label,
                                                    doc=doc,
                                                    form_width_class=
                                                    form_width_class)
        self.template_fname = template_fname

    @property
    def field(self):
        #TODO unimplemented
        pass
