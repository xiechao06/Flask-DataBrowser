# -*- coding: utf-8 -*-
from wtforms.fields import Field
from flask.ext.databrowser.column_spec import ColumnSpec
from flask.ext.databrowser.extra_widgets import PlaceHolder


class PlaceHolderColumnSpec(ColumnSpec):
    def __init__(self, col_name, template_fname, label=None, doc=None,
                 form_width_class=None,
                 place_holder_kwargs=None, as_input=False,
                 record=None):
        super(PlaceHolderColumnSpec, self).__init__(col_name, label=label,
                                                    doc=doc,
                                                    form_width_class=
                                                    form_width_class)
        self.template_fname = template_fname
        self.place_holder_kwargs = place_holder_kwargs
        self.record = record
        self.as_input = as_input

    @property
    def field(self):
        return Field(label=self.label, description=self.doc,
                     widget=PlaceHolder(self.template_fname, self.record,
                                        self.place_holder_kwargs))
