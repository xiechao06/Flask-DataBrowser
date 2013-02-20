# -*- coding: UTF-8 -*-
from flask import request
from flask.ext.databrowser.form.validators import Unique
from flask.ext.babel import _

def is_required_form_field(field):
    if not request.args.get("action") == _(u"批量修改"):
        from wtforms.validators import Required
        for validator in field.validators:
            if isinstance(validator, Required):
                return True
    return False


def is_disabled_form_field(field):
    if request.args.get("action") == _(u"批量修改"):
        for validator in field.validators:
            if isinstance(validator, Unique):
                return True
    return False