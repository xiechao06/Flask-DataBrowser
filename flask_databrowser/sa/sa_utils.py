# -*- coding: UTF-8 -*-
#TODO should be a library
import operator
from sqlalchemy import types
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.schema import Table


def is_relationship(model, col_name):
    return hasattr(operator.attrgetter(col_name)(model).property, 'direction')


def remote_side(col_def):
    return col_def.property.mapper.class_


def get_primary_key(model):
    """
        Return primary key name from a model

        :param model:
            Model class
    """
    if isinstance(model, Table):
        for idx, c in enumerate(model.columns):
            if c.primary_key:
                return c.key
    else:
        props = model._sa_class_manager.mapper.iterate_properties

        for p in props:
            if isinstance(p, ColumnProperty) and p.is_primary:
                return p.key

    return None


def get_joined_tables(model, col_name):
    result = []
    attrs = col_name.split(".")
    last_join_model = model
    for rel in attrs[:-1]:
        last_join_model = getattr(last_join_model, rel).property.mapper.class_
        result.append(last_join_model)
    return result


def get_column_default_value(column):
    kwargs = {}
    default = getattr(column, 'default', None)
    value = None
    if default is not None:
        value = getattr(default, 'arg', None)
        if value is not None:
            if getattr(default, 'is_callable', False):
                value = value(None)
            else:
                if not getattr(default, 'is_scalar', True):
                    value = None
    if value is not None:
        kwargs["default"] = value
    return kwargs


def is_numerical_column(column):
    return (
        is_integer_column(column) or
        isinstance(column.type, types.Float) or
        isinstance(column.type, types.Numeric)
    )


def is_integer_column(column):
    return (
        isinstance(column.type, types.Integer) or
        isinstance(column.type, types.SmallInteger) or
        isinstance(column.type, types.BigInteger)
    )


def is_date_column(column):
    return (
        isinstance(column.type, types.Date) or
        isinstance(column.type, types.DateTime)
    )


def is_str_column(column):
    return isinstance(column.type, (
        types.String, types.Unicode, types.Text, types.UnicodeText, types.LargeBinary,
        types.Binary))