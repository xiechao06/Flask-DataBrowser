# -*- coding: UTF-8 -*-

# TODO need refactoring

from hashlib import md5
from collections import namedtuple, Iterable
import operator
from .utils import TemplateParam, raised_when, get_primary_key
from flask.ext.babel import gettext as _

_raised_when_model_unset = raised_when(lambda inst, *args, **kwargs: not inst.model_view, 
                                       RuntimeError(r'field "model view" unset, you should set it'))


class BaseFilter(TemplateParam):
    __notation__ = ""
    multiple = False

    def __init__(self, col_name, name="", options=None, opt_formatter=None,
                 value=None, display_col_name=None, hidden=False, default_value=None):
        # TODO datetime unsupported
        self.op = namedtuple("op", ["name", "id"])(name, col_name + self.__notation__)
        self.col_name = col_name
        self.__display_col_name = display_col_name
        self.value = value
        self.model_view = None
        self.__options = options or []
        self.opt_formatter = opt_formatter
        self.hidden = hidden
        self.default_value = default_value

    @property
    @_raised_when_model_unset
    def model(self):
        return self.model_view.model

    @property
    def label(self):
        return self.__display_col_name or self.model_view.__column_labels__.get(self.col_name, self.col_name)

    @property
    @_raised_when_model_unset
    def data_type(self):
        return 'numeric'

    @property
    @_raised_when_model_unset
    def input_type(self):
        if self.options:
            return "select",
        else:
            attrs = self.col_name.split(".")
            last_join_model = self.model
            for rel in attrs[:-1]:
                last_join_model = getattr(last_join_model, rel).property.mapper.class_
            attr = getattr(last_join_model, attrs[-1])
            if hasattr(attr, 'property'):
                col_type = type(attr.property.columns[0].type).__name__
                if col_type == 'Integer':
                    return 'number',
                elif col_type == 'DateTime':
                    return 'datetime',
                else:
                    return 'text',

    @property
    @_raised_when_model_unset
    def input_class(self):
        return 'numeric-filter'

    @property
    def options(self):
        if self.__options:
            return [(md5(",".join(str(o[0]) for o in self.__options)).hexdigest(), u'--%s--' % _(u"all"))] + self.__options
        else:
            # if column is a relation, then we should find all of them, else return []
            attrs = self.col_name.split(".")
            last_join_model = self.model
            for rel in attrs[:-1]:
                last_join_model = getattr(last_join_model, rel).property.mapper.class_
            attr = getattr(last_join_model, attrs[-1])
            ret = []
            if hasattr(attr, 'property') and hasattr(attr.property, 'direction'):
                model = attr.property.mapper.class_
                ret.extend((getattr(row, get_primary_key(model)), self.opt_formatter(row) if self.opt_formatter else row) 
                        for row in model.query.all())
                if not ret:
                    ret = [("", u'--%s--' % _(u"all"))]
                elif not self.multiple:
                    ret.insert(0, (md5((",".join(unicode(r[0]) for r in ret)).encode("utf-8")).hexdigest(), u'--%s--' % _(u"all")))
            return ret

    @property
    def real_value(self):
        from flask import request
        value = request.args.get(self.col_name+self.__notation__, "")
        return value if value != (self.options and self.options[0][0]) else None

    def unfiltered(self, arg):
        return arg in (None, "") or arg == self.options[0][0]

    def has_value(self):
        if isinstance(self.value, list) or isinstance(self.value, tuple):
            return any(val not in (None, "") for val in self.value)
        else:
            return self.value not in (None, "") and self.value != (
               self.options and self.options[0][0])

    def set_sa_criterion(self, q):
        """
        set the query filter/join criterions
        """
        attrs = self.col_name.split(".")
        last_join_model = self.model
        for attr in attrs[:-1]:
            last_join_model = getattr(last_join_model, attr).property.mapper.class_
            q = q.join(last_join_model)

        # convert attr to InstrumentedAttribute
        attr = getattr(last_join_model, attrs[-1])
        if hasattr(attr.property, 'direction'):
            # translate the relation
            filter_criterion = self.__operator__(attr.property.local_remote_pairs[0][0], self.value)
        else:
            filter_criterion = self.__operator__(attr, self.value)
        q = q.filter(filter_criterion)
        return q

    @property
    def sa_criterion(self):
        
        attr = getattr(self.model, self.col_name)
        if hasattr(attr.property, 'direction'):
            # translate the relation
            return self.__operator__(attr.property.local_remote_pairs[0][0], self.value)
        else:
            return self.__operator__(attr, self.value)

class EqualTo(BaseFilter):
    __notation__ = ""
    __operator__ = operator.eq

class NotEqualTo(BaseFilter):
    __notation__ = "__ne"
    __operator__ = operator.ne

class LessThan(BaseFilter):
    __notation__ = "__lt"
    __operator__ = operator.lt

class BiggerThan(BaseFilter):
    __notation__ = "__gt"
    __operator__ = operator.gt

class Contains(BaseFilter):
    __notation__ = "__contains"
    __operator__ = lambda self, attr, value: attr.like(value.join(["%", "%"]))

class Between(BaseFilter):
    
    def __init__(self, col_name, name="", sep="--", default_value=None):
        super(Between, self).__init__(col_name=col_name, name=name, default_value=default_value)
        self.sep = sep

    def __operator__(self, attr, value_list):
        if value_list[0] and not value_list[1]:
            return operator.ge(attr, value_list[0])
        elif value_list[1] and not value_list[0]:
            return operator.le(attr, value_list[1])
        return attr.between(value_list[0], value_list[1])

    __notation__ = "__between"

    @property
    @_raised_when_model_unset
    def input_type(self):
        return super(Between, self).input_type * 2

    @property
    @_raised_when_model_unset
    def input_class(self):
        return 'numeric-filter'

class In_(BaseFilter):
    __notation__ = "__in"

    def __operator__(self, attr, value):
        return attr.in_(set(value))

    multiple = True

class Only(BaseFilter):

    def __init__(self, col_name, display_col_name, test, notation, default_value=False):
        self.__notation__ = notation
        super(Only, self).__init__(col_name=col_name, default_value=default_value, display_col_name=display_col_name)
        self.test = test

    def set_sa_criterion(self, q):
        """
        set the query filter/join criterions
        """
        if self.value:
            attrs = self.col_name.split(".")
            last_join_model = self.model
            for attr in attrs[:-1]:
                last_join_model = getattr(last_join_model, attr).property.mapper.class_
                q = q.join(last_join_model)

            # convert attr to InstrumentedAttribute
            attr = getattr(last_join_model, attrs[-1])
            if hasattr(attr.property, 'direction'):
                # translate the relation
                filter_criterion = self.test(attr.property.local_remote_pairs[0][0])
            else:
                filter_criterion = self.test(attr)
            q = q.filter(filter_criterion)
        return q

    @property
    def input_type(self):
        return "checkbox",
