#-*- coding:utf-8 -*-
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField
from flask.ext.upload2.fields import FileField as FileField2
from flask.ext.databrowser.utils import wrap_form_field


class BaseForm(Form):
    """
        Customized form class.
    """

    def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
        if formdata:
            super(BaseForm, self).__init__(formdata, obj, prefix, **kwargs)
        else:
            super(BaseForm, self).__init__(obj=obj, prefix=prefix, **kwargs)

        self._obj = obj

    @property
    def has_file_field(self):
        for f in self:
            if f.name.startswith("_"):
                continue
            if isinstance(f, (FileField, FileField2)):
                return True
            else:
                try:
                    if f.form.has_file_field:
                        return True
                except AttributeError:
                    continue
            return False


class FormProxy(object):
    def __init__(self, form, fields=None, create_url_map=None):
        self._form = form
        create_url_map = create_url_map or {}
        if fields is None:
            self._fields = [wrap_form_field(field, create_url_map.get(field.name, None)) for field in form._fields.values()]
        else:
            self._fields = [wrap_form_field(field, create_url_map.get(field.name, None)) for field in fields]
        self._field_map = {field.name: field for field in self._fields}

    def __iter__(self):
        return iter(self._fields)

    def __getattr__(self, item):
        return getattr(self._form, item)

    def __getitem__(self, item):
        return self._field_map[item]
