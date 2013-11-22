# -*- coding: UTF-8 -*-
"""
convert utilities for sqlalchemy
"""
from wtforms import validators, ValidationError
from sqlalchemy import (Boolean, String, Integer, UnicodeText, Unicode, Text,
                        Integer, SmallInteger, Date, DateTime, Float, Numeric)
from flask.ext.babel import ngettext, gettext as _
from sqlalchemy.orm.exc import NoResultFound
from wtforms_components import Unique


def get_primary_key(model):
    """
        Return primary key name from a model

        :param model:
            Model class
    """
    from sqlalchemy.schema import Table

    if isinstance(model, Table):
        for idx, c in enumerate(model.columns):
            if c.primary_key:
                return c.key
    else:
        props = model._sa_class_manager.mapper.iterate_properties

        for p in props:
            if hasattr(p, 'columns'):
                for c in p.columns:
                    if c.primary_key:
                        return p.key

    return None


class DictConverter(object):
    def convert_select(self, direction, **kwargs):
        ret = kwargs
        ret["validators"] = [v for v in (self._convert_validator(v) for v in kwargs["validators"]) if v]
        ret["type"] = "select"
        ret["multiple"] = not direction.name == "MANYTOONE"
        ret["options"] = [(pk, unicode(opt)) for pk, opt in ret["options"]]
        ret["default"] = ret['default'] and getattr(ret['default'], get_primary_key(ret['default']))
        ret["value"] = ret.get('value', None) and getattr(ret['value'], get_primary_key(ret['value']))
        return ret

    def convert(self, col_type, **kwargs):
        ret = kwargs
        ret["validators"] = [v for v in (self._convert_validator(v) for v in kwargs["validators"]) if v]
        if isinstance(col_type, Text) or isinstance(col_type, UnicodeText):
            ret["type"] = "textarea"
        elif isinstance(col_type, Boolean):
            ret["type"] = "checkbox"
        elif isinstance(col_type, Date):
            ret["type"] = "date"
        elif isinstance(col_type, DateTime):
            ret["type"] = "datetime"
        elif isinstance(col_type, Integer) or isinstance(col_type, SmallInteger):
            ret["type"] = "integer"
        elif isinstance(col_type, Float) or isinstance(col_type, Numeric):
            ret["type"] = "float"
        elif isinstance(col_type, String) or isinstance(col_type, Unicode):
            if hasattr(col_type, 'enums'):
                ret['type'] = 'select'
                ret['options'] = [(f, f) for f in col_type.enums]
            else:
                ret["type"] = "string"
        else:
            ret["type"] = "string"

        return ret

    def _convert_validator(self, validator):
        ret = {}
        # note!!! Unique is left off, since it has no meaning to client
        if isinstance(validator, validators.DataRequired):
            ret['name'] = 'required'
            ret['message'] = validator.message
            if ret['message'] is None:
                ret['message'] = _('This field is required.')
        elif isinstance(validator, validators.Regexp):
            ret['name'] = 'regexp'
            ret['regexp'] = validator.regex
            ret['message'] = validator.message
            if ret['message'] is None:
                ret['message'] = _('the input must be like %s' % validator.regex)
        elif isinstance(validator, validators.URL):
            ret['name'] = 'url'
            ret['message'] = validator.message
            if ret['message'] is None:
                ret['message'] = _('Invalid URL')
        elif isinstance(validator, validators.AnyOf):
            ret['name'] = 'anyof'
            ret['values'] = validator.values
            if validator.message:
                ret['message'] = validator.message % dict(values=validator.values_formatter(validator.values))
            else:
                ret['message'] = _('Invalid value, must be one of: %(values)s.',
                                   values=validator.values_formatter(validator.values))
        elif isinstance(validator, validators.NoneOf):
            ret['name'] = 'noneof'
            ret['values'] = validator.values
            if validator.message:
                ret['message'] = validator.message % dict(values=validator.values_formatter(validator.values))
            else:
                ret['message'] = _('Invalid value, must be one of: %(values)s.',
                                   values=validator.values_formatter(validator.values))
        elif isinstance(validator, validators.Length):
            ret['name'] = 'length'
            ret['min'] = validator.min
            ret['max'] = validator.max
            message = validator.message
            if message is None:
                if validator.max == -1:
                    message = _('Field must be at least %%(min)d character long.')
                elif validator.min == -1:
                    message = _('Field cannot be longer than %%(max)d character.')
                else:
                    message = _('Field must be between %%(min)d and %%(max)d characters long.')
            ret['message'] = message % dict(min=validator.min, max=validator.max)
        elif isinstance(validator, validators.NumberRange):
            ret['name'] = 'range'
            ret['min'] = validator.min
            ret['max'] = validator.max
            message = validator.message
            if message is None:
                if validator.max is None:
                    message = _('Number must be greater than %%(min)s.')
                elif validator.min is None:
                    message = _('Number must be less than %%(max)s.')
                else:
                    message = _('Number must be between %%(min)s and %%(max)s.')
            ret['message'] = message % dict(min=validator.min, max=validator.max)
        elif isinstance(validator, validators.Email):
            ret['name'] = 'email'
            ret['message'] = validator.message
            if ret['message'] is None:
                self.message = _('Invalid email address.')
        return ret or None


def extrac_validators(column, model_view):
    """
    get validators from non-relationship property
    """
    ret = []
    if not column.nullable and not isinstance(column.type, Boolean):
        ret.append(validators.DataRequired(message=_(u"this field can't be empty")))

    unique = False
    if column.primary_key:
        ret.append(Unique(column, model_view._session, message=_("This field must be unique, but it already exists!")))
        unique = True

    # If field is unique, validate it
    if column.unique and not unique:
        ret.append(Unique(column, model_view._session, message=_("This field must be unique, but it already exists!")))
    if isinstance(column.type, String) or isinstance(column.type, Unicode):
        if hasattr(column.type, 'enums'):
            ret.append(validators.AnyOf(column.type.enums,
                                        message=_(u"value of this field must be %(values)s",
                                                  values=", ".join(str(i) for i in column.type.enums[:-1])) +
                                                _(u" or %(last_value)s", last_value=column.type.enums[-1]) if (
                                        len(column.type.enums) > 1) else ""))
        else:
            ret.append(validators.Length(max=column.type.length))
    elif isinstance(column.type, Text) or isinstance(column.type, UnicodeText):
        ret.append(validators.Length(max=column.type.length))
    elif isinstance(column.type, Integer) or isinstance(column.type, SmallInteger):
        unsigned = getattr(column.type, 'unsigned', False)
        if unsigned:
            ret.append(validators.NumberRange(min=0, message=_(u"this field must bigger than 0")))
    return ret


def convert_column(col_spec, converter, model_view, obj):
    """
    NOTE!!! obviously, for column in the format of InputColumnSpec or PlaceHolderColumnSpec, only "label",
    "read_only", "doc", "filter_", "opt_filter" and "validators" take effects
    """
    ret = {
        "name": col_spec.col_name,
        "label": col_spec.label,
        "doc": col_spec.doc,
        "disabled": col_spec.disabled,
        "group_by": col_spec.group_by,
        'validators': [],
    }
    # get validators and options
    if hasattr(col_spec.kolumne, "direction"): # relationship
        remote_model = col_spec.property_.mapper.class_
        local_column = col_spec.property_.local_remote_pairs[0][0]
        if not local_column.foreign_keys or local_column.nullable: # backref shouldn't be validated
            ret['validators'].append(validators.Optional())
        elif col_spec.property_.direction.name != 'MANYTOMANY': # many to many allowed to be empty
            ret['validators'].append(validators.DataRequired(message=_(u"this field can't be empty")))
        if col_spec.filter_:
            ret['options'] = [(getattr(obj_, get_primary_key(remote_model)), obj_) for obj_ in
                              col_spec.filter_(model_view._session.query(remote_model)).all()]
        else:
            ret['options'] = [(getattr(obj_, get_primary_key(remote_model)), obj_) for obj_ in
                              model_view._session.query(remote_model).all()]
        if col_spec.opt_filter:
            ret['options'] = [(pk, opt) for pk, opt in ret['options'] if (col_spec.opt_filter(opt))]
        default = local_column.default
        if default is None:
            ret['default'] = None
        else:
            default = default.arg
            ret["default"] = remote_model.query.get(default(None) if hasattr(default, '__call__') else default)
        if obj:
            ret['value'] = getattr(obj, col_spec.col_name, None)
        return converter.convert_select(col_spec.property_.direction, **ret)
    else:
        column = col_spec.property_.columns[0]
        # get default value
        default = column.default
        if default is None:
            ret["default"] = None
        else:
            default = default.arg
            ret["default"] = unicode(default(None) if hasattr(default, "__call__") else default)
        if obj:
            ret['value'] = getattr(obj, col_spec.col_name, None)
            # get type and validators
        ret["validators"] = extrac_validators(col_spec.property_.columns[0], model_view) + col_spec.validators
        return converter.convert(column.type, **ret)
