# -*- coding: UTF-8 -*-
import operator

def is_relationship(model, col_name):
    return hasattr(operator.attrgetter(col_name)(model).property, 'direction')


def remote_side(col_def):
    return col_def.property.mapper.class_
