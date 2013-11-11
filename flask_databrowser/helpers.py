# -*- coding: UTF-8 -*-
import posixpath
import urlparse
from flask import request
from flask.ext.databrowser.form.validators import Unique


#TODO 将这几个函数作为field的方法
def is_required_form_field(field):
    if hasattr(field, "validators") and not in_batch_mode():
        from wtforms.validators import Required

        for validator in field.validators:
            if isinstance(validator, Required):
                return True
    return False


def is_unique_form_field(field):
    if hasattr(field, "validators") and in_batch_mode():
        for validator in field.validators:
            if isinstance(validator, Unique):
                return True
    return False
#TODO


#TODO 变成edit_form的一个属性
def in_batch_mode():
    return len(posixpath.basename(urlparse.urlparse(urlparse.unquote(request.url)).path).split(',')) > 1
#TODO