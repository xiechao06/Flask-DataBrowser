# -*- coding: utf-8 -*-
from .column_spec import ColSpec


class SelectColumnSpec(ColSpec):

    def __init__(self, col_name, read_only=False, doc=None, formatter=None,
                 label=None, render_kwargs={}, validators=None,
                 choices=None):
        super(SelectColumnSpec, self).__init__(col_name, doc=doc,
                                               formatter=formatter,
                                               label=label,
                                               render_kwargs=render_kwargs)
        self.read_only = read_only
        self.validators = validators or []
        self.choices = choices or []

    @property
    def field(self):
        #TODO unimplemented
        pass
