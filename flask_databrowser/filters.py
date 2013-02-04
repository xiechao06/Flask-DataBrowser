# -*- coding: UTF-8 -*-

# TODO need refactoring

from collections import namedtuple
import operator
from .utils import TemplateParam, raised_when, get_primary_key
from flask.ext.babel import gettext as _

_raised_when_model_unset = raised_when(lambda inst, *args, **kwargs: not inst.model_view, 
                                       RuntimeError(r'field "model view" unset, you should set it'))

class BaseFilter(TemplateParam):

    def __init__(self, col_name, name, options=[], opt_formatter=None):
        # TODO datetime unsupported
        self.op = namedtuple("op", ["name", "id"])(name, col_name)
        self.col_name = col_name
        self.value = None
        self.model_view = None
        self.__options = options
        if self.__options and len(self.__options) > 1:
            self.__options.insert(0, (",".join(str(o[0]) for o in self.__options), u'--%s--' % _(u"所有")))
        self.opt_formatter = opt_formatter

    @property
    @_raised_when_model_unset
    def model(self):
        return self.model_view.model

    @property
    def label(self):
        return self.model_view.__column_labels__.get(self.col_name, self.col_name)

    @property
    @_raised_when_model_unset
    def data_type(self):
        return 'numeric'

    @property
    @_raised_when_model_unset
    def input_type(self):
        if self.options:
            return "select"
        else:
            attr = getattr(self.model, self.col_name)
            if hasattr(attr, 'property'):
                col_type = type(attr.property.columns[0].type).__name__
                if col_type == 'Integer':
                    return 'number'
                else:
                    return 'text'

    @property
    @_raised_when_model_unset
    def input_class(self):
        return 'numeric-filter'

    @property
    def sa_criterion(self):
        """
        generate the sqlalchemy filter criterion
        """
        raise NotImplementedError("this is base filter")

    @property
    def options(self):
        if self.__options:
            return self.__options
        else:
            """
            if column is a relation, then we should find all of them
            """
            # TODO table joinning unsupported
            attr = getattr(self.model, self.col_name)
            ret = []
            if hasattr(attr, 'property') and hasattr(attr.property, 'direction'):
                model = attr.property.mapper.class_
                ret.extend((getattr(row, get_primary_key(model)), self.opt_formatter(row) if self.opt_formatter else row) 
                        for row in model.query.all())
            if len(ret) > 1:
                ret.insert(0, (",".join(str(r[0]) for r in ret), u'--%s--' % _(u"所有")))
            return ret


    def has_value(self):
        return self.value not in (None, "") and self.value != (self.options and self.options[0][0])

    @property
    def sa_criterion(self):
        attr = getattr(self.model, self.col_name)
        if hasattr(attr.property, 'direction'):
            return self.__operator__(enumerate(attr.property.local_columns).next()[1], self.value)
        else:
            return self.__operator__(attr, self.value)

class EqualTo(BaseFilter):

    __notation__ = ""
    __operator__ = operator.eq

class LessThan(BaseFilter):
    __notation__ = "__lt"
    __operator__ = operator.lt


class BiggerThan(BaseFilter):
    __notation__ = "__gt"
    __operator__ = operator.gt

