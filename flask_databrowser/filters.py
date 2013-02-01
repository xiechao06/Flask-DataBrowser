# -*- coding: UTF-8 -*-

# TODO need refactoring

from collections import namedtuple

class BaseFilter(object):

    def label(self, model_view):
        return model_view.__column_labels__.get(self.col_name, self.col_name)

class EqualTo(BaseFilter):

    __notation__ = ""

    def __init__(self, col_name, name="equals to", options=set()):
        # TODO datetime unsupported
        self.op = namedtuple("op", ["name", "id"])(name, col_name)
        self.col_name = col_name
        self.data_type = "numeric"
        self.input_type = "number"
        self.input_class = "numeric-filter"
    
class LessThan(BaseFilter):
    __notation__ = "__lt"

    def __init__(self, col_name, name="less than", options=set()):
        # TODO datetime unsupported
        self.op = namedtuple("op", ["name", "id"])(name, col_name+self.__notation__)
        self.col_name = col_name
        self.data_type = "numeric"
        self.input_type = "number"
        self.input_class = "numeric-filter"

class BiggerThan(BaseFilter):
    __notation__ = "__gt"

    def __init__(self, col_name, name="less than", options=set()):
        # TODO datetime unsupported
        self.op = namedtuple("op", ["name", "id"])(name, col_name+self.__notation__)
        self.col_name = col_name
        self.data_type = "numeric"
        self.input_type = "number"
        self.input_class = "numeric-filter"
