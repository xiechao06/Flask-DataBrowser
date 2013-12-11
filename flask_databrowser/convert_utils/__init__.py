# -*- coding: UTF-8 -*-


def convert_column(col_spec, converter, model_view, obj=None):
    """
    select the underlying convert utility for current ORM, and make the conversion
    """
    # TODO only sqlalchemy supported here
    from flask.ext.databrowser.convert_utils.sa import convert_column as sacc
    return sacc(col_spec, converter, model_view, obj)


def get_dict_converter():
    """
    select the underlying dict converter for current ORM, and make the conversion
    """
    # TODO only sqlalchemy supported here
    from flask.ext.databrowser.convert_utils.sa import DictConverter
    return DictConverter()