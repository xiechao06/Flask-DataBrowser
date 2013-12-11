# -*- coding: utf-8 -*-
from .column_spec import ColumnSpec


class FileColumnSpec(ColumnSpec):

    def __init__(self, col_name, label, validators=None):
        super(FileColumnSpec, self).__init__(col_name, label=label)
        self.validators = validators or []

    @property
    def field(self):
        #TODO unimplemented
        pass
