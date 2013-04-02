# -*- coding: UTF-8 -*-
import types
from flask import request,url_for

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


def make_disabled_field(field):
    class FakeField(field.field_class):
        
        def __call__(self, **kwargs):
            kwargs["disabled"] = True
            return super(FakeField, self).__call__(**kwargs)

    field.field_class = FakeField
    return field
    
def fslice(iterable, predict):
    a = []
    b = []
    for i in iterable:
        if predict(i):
            a.append(i)
        else:
            b.append(i)
    return a, b


def get_description(view, col_name, col_spec=None):
    if col_spec and col_spec.doc:
            return col_spec.doc
    if view.__column_docs__:
        ret = view.__column_docs__.get(col_name)
        if ret:
            return ret
    return get_doc_from_table_def(view, col_name)


def get_doc_from_table_def(view, col_name):
    doc = ""
    attr_name_list = col_name.split('.')
    last_model = view.model
    for attr_name in attr_name_list[:-1]:
        attr = getattr(last_model, attr_name)
        if hasattr(attr, "property"):
            last_model = attr.property.mapper.class_
        else:
            last_model = None
            break
    if last_model:
        if hasattr(last_model, attr_name_list[-1]):
            from operator import attrgetter
            try:
                doc = attrgetter(attr_name_list[-1] + ".property.doc")(last_model)
            except AttributeError:
                pass
    return doc
