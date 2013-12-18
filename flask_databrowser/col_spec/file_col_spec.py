# -*- coding: utf-8 -*-
from flask_wtf.file import FileField
from .col_spec import ColSpec


class _FileField(FileField):

    def __init__(self, save_path=None, *args, **kwargs):
        super(_FileField, self).__init__(*args, **kwargs)
        self.save_path = save_path


class FileColSpec(ColSpec):

    as_input = True
    disabled = False

    def __init__(self, col_name, label=None, validators=None, save_path=None,
                 doc=None):
        super(FileColSpec, self).__init__(col_name, label=label, doc=doc)
        self.validators = validators or []
        self.save_path = save_path

    @property
    def field(self):
        return _FileField(save_path=self.save_path, id=self.col_name,
                          validators=self.validators,
                          label=self.label, description=self.doc)

    @property
    def remote_create_url(self):
        return None
