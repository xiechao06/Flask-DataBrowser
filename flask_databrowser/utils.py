# -*- coding: UTF-8 -*-
import types
from flask import request,url_for

def get_primary_key(model):
    """
        Return primary key name from a model

        :param model:
            Model class
    """
    props = model._sa_class_manager.mapper.iterate_properties

    for p in props:
        if hasattr(p, 'columns'):
            for c in p.columns:
                if c.primary_key:
                    return p.key

    return None

def url_for_other_page(page):
    """
    generate the other page's url
    """
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args) # pylint: disable=W0142

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

named_actions = set()

from functools import wraps

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

def disabled_field_or_widget(convert):

    @wraps(convert)
    def convert_(*args, **kwargs):
        field_or_widget = convert(*args, **kwargs)
        def __call__(self, field, **kwargs):
            kwargs["disabled"] = True
            return super(self.__class, self).__call__(field, **kwargs)
        field_or_widget.__call__ = types.MethodType(__call__, field_or_widget, field_or_widget.__class__)
        return field_or_widget

    return convert_

def fslice(iterable, predict):
    a = []
    b = []
    for i in iterable:
        if predict(i):
            a.append(i)
        else:
            b.append(i)
    return a, b

