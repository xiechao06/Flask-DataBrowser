# -*- coding: UTF-8 -*-
import posixpath
import urlparse
import urllib
from flask import request
from flask.ext.databrowser.form.validators import Unique


def is_required_form_field(field):
    if hasattr(field, "validators") and not is_batch_edit():
        from wtforms.validators import Required
        for validator in field.validators:
            if isinstance(validator, Required):
                return True
    return False


def is_unique_form_field(field):
    if hasattr(field, "validators") and is_batch_edit():
        for validator in field.validators:
            if isinstance(validator, Unique):
                return True
    return False

def is_batch_edit():
    return len(posixpath.basename(urlparse.urlparse(urlparse.unquote(request.url)).path).split(',')) > 1
