# -*- coding: utf-8 -*-
from wtforms.fields import Field
from flask.ext.databrowser.col_spec import ColSpec


class PlaceHolderColumnSpec(ColSpec):
    def __init__(self, col_name, template_fname, label=None, doc=None,
                 place_holder_kwargs=None,
                 record=None, render_kwargs={}):
        super(PlaceHolderColumnSpec, self).__init__(col_name, label=label,
                                                    doc=doc,
                                                    render_kwargs=
                                                    render_kwargs)
        self.template_fname = template_fname
        self.place_holder_kwargs = place_holder_kwargs
        self.record = record

    @property
    def field(self):
        from flask.ext.databrowser.extra_widgets import PlaceHolder
        return Field(label=self.label, description=self.doc,
                     widget=PlaceHolder(self.template_fname, self.record,
                                        self.place_holder_kwargs))
