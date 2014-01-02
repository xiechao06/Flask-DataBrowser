# -*- coding: UTF-8 -*-
import os
import string
import random
import types
import urllib
from functools import wraps

from flask import request, url_for
from jinja2 import Markup
from wtforms import widgets
from wtforms.validators import Required
from wtforms_components import Unique


def wrap_form_field(field, create_url=None):
    class FormFieldProxy(object):
        def __init__(self, field, create_url):
            self.field = field
            self.create_url = create_url

        def __getattr__(self, item):
            return getattr(self.field, item)

        def __call__(self, *args, **kwargs):
            if self.field.type == 'BooleanField':
                form_control_div = "<div class='checkbox'>%s</div>"
                return form_control_div % self.field(**kwargs)
            else:
                def _add_class(kwargs, _class):
                    kwargs["class"] = " ".join((kwargs["class"], _class)) if kwargs.get("class") else _class

                _add_class(kwargs, "form-control" if self.is_input_field else "form-control-static")

                return self.field(**kwargs)

        @property
        def is_input_field(self):
            return isinstance(self.field.widget, (widgets.Input, widgets.Select, widgets.TextArea)) \
                and self.field.type not in ["ReadOnlyField", "FileField"]

        @property
        def form_width_class(self):
            initial = getattr(self.field, "form_width_class", "")
            if initial:
                return initial
            if self.is_input_field:
                return "col-lg-3"
            label = getattr(self.field, "label")
            if getattr(label, "text", None) or label.get("text"):
                return "col-lg-10"
            return "col-lg-12"

        def is_required(self):
            if hasattr(self, "validators"):
                for validator in self.validators:
                    if isinstance(validator, Required):
                        return True
            return False

        def is_unique(self):
            if hasattr(self, "validators"):
                for validator in self.validators:
                    if isinstance(validator, Unique):
                        return True
            return False

    return FormFieldProxy(field, create_url)


def make_field_disabled(field):
    class DisabledField(field.field_class):
        def __call__(self, **kwargs):
            kwargs.setdefault("disabled", True)
            return super(DisabledField, self).__call__(**kwargs)

        def validate(self, form, extra_validators=()):
            return True

        # dirty trick
        @property
        def __read_only__(self):
            return True

    field.field_class = DisabledField
    return field


def url_for_other_page(page):
    """
    generate the other page's url
    """
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)  # pylint: disable=W0142


class TemplateParam(object):
    """A class intends to be templates parameter should inherit this class"""

    def as_dict(self, *fields):
        items = []
        for field in fields:
            if isinstance(field, types.StringType):
                if field == "values":
                    raise ValueError(u'you can\'t use "values" as the key, since it is the method of dict type')
                v = getattr(self, field)
                if v is None:
                    v = ""
            elif isinstance(field, types.TupleType):
                if field[0] == "values":
                    raise ValueError(u'you can\'t use "values" as the key, since it is the method of dict type')
                v = getattr(self, field[0])
                if v is None:
                    v = ""
            items.append((field, v))
        return dict(items)


def raised_when(test, assertion):
    def decorator(f):
        @wraps(f)
        def f_(*args, **kwargs):
            if test(*args, **kwargs):
                raise assertion
            return f(*args, **kwargs)

        return f_

    return decorator


def raised(E, test, *args, **kwargs):
    try:
        test(*args, **kwargs)
        return True
    except E:
        return False


def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return Markup(s)


def truncate_str(s, length=255, killwords=False, end='...', href="#"):
    a_ = "<a title='" + s
    if href:
        a_ = a_ + "' href='" + href + "'>" + end + "<a>"
    else:
        a_ = a_ + "'>" + end + "<a>"
    if len(s) <= length:
        return s
    elif killwords:
        return s[:length] + a_
    words = s.split(' ')
    result = []
    m = 0
    for word in words:
        m += len(word) + 1
        if m > length:
            break
        result.append(word)
    result.append(a_)
    return u' '.join(result)


def random_str(size=6, chars=string.ascii_uppercase + string.digits):
    random.seed = (os.urandom(1024))
    return ''.join(random.choice(chars) for x in range(size))
