# -*- coding: UTF-8 -*-

# TODO need refactoring

from hashlib import md5
from collections import namedtuple
import operator

from flask.ext.babel import gettext as _
from werkzeug.utils import cached_property

from .utils import TemplateParam
from flask.ext.databrowser.sa.sa_utils import get_primary_key


class BaseFilter(TemplateParam):
    __notation__ = ""
    multiple = False

    def __init__(self, col_name, model_view, name="", options=None,
                 opt_formatter=None,
                 label=None, hidden=False,
                 default_value=None, value=None):
        # TODO datetime unsupported
        self.op = namedtuple("op",
                             ["name", "id"])(name,
                                             col_name + self.__notation__)
        self.col_name = col_name
        self.model_view = model_view
        self.label = label
        self.value = value
        self.__options = options or []
        self.opt_formatter = opt_formatter
        self.hidden = hidden
        self.default_value = default_value

    @property
    def model(self):
        # TODO obviously don't use
        return self.model_view.modell.model

    @property
    def data_type(self):
        return 'numeric'

    @property
    def input_type(self):
        """
        用tuple 是因为有可能返回 类似于(number, number)的双控件
        """
        if self.options:
            return "select",
        else:
            if hasattr(self.attr, 'property'):
                col_type = type(self.attr.property.columns[0].type).__name__
                if col_type == 'Integer':
                    return 'number',
                elif col_type == 'DateTime':
                    return 'datetime',
                else:
                    return 'text',

    @property
    def input_class(self):
        return 'numeric-filter'

    @cached_property
    def attr(self):
        # TODO no sa
        attrs = self.col_name.split(".")
        last_join_model = self.model
        for rel in attrs[:-1]:
            last_join_model = getattr(last_join_model,
                                      rel).property.mapper.class_
        attr = getattr(last_join_model, attrs[-1])
        return attr

    # TODO seemed no need any more
    @cached_property
    def joined_tables(self):
        # TODO no sa
        ret = []
        attrs = self.col_name.split(".")
        last_join_model = self.model
        for rel in attrs[:-1]:
            last_join_model = getattr(last_join_model,
                                      rel).property.mapper.class_
            ret.append(last_join_model)
        return ret

    @property
    def options(self):
        if self.__options:
            return [(md5(",".join(str(o[0]) for o in self.__options)).hexdigest(),
                     u'--%s--' % _(u"all"))] + self.__options
        else:
            # if column is a relation, then we should find all of them, else return []
            ret = []
            if hasattr(self.attr, 'property') and hasattr(self.attr.property, 'direction'):
                model = self.attr.property.mapper.class_
                ret.extend(
                    (getattr(row, get_primary_key(model)), self.opt_formatter(row) if self.opt_formatter else row)
                    for row in model.query.all())
                if not ret:
                    ret = [("", u'--%s--' % _(u"all"))]
                elif not self.multiple:
                    ret.insert(0, (
                    md5((",".join(unicode(r[0]) for r in ret)).encode("utf-8")).hexdigest(), u'--%s--' % _(u"all")))
            return ret

    @property
    def real_value(self):
        from flask import request

        value = request.args.get(self.col_name + self.__notation__, "")
        return value if value != (self.options and self.options[0][0]) else None

    def unfiltered(self, arg):
        return arg in (None, "") or arg == self.options[0][0]

    def has_value(self):
        if isinstance(self.value, list) or isinstance(self.value, tuple):
            return any(val not in (None, "") for val in self.value)
        else:
            return self.value not in (None, "") and self.value != (self.options and self.options[0][0])

    # TODO it seemd that it is no need any more
    def set_sa_criterion(self, q):
        """
        set the query filter/join criterions
        """
        # NOTE! we don't join table here
        if hasattr(self.attr.property, 'direction'):
            # translate the relation
            filter_criterion = self.__operator__(self.attr.property.local_remote_pairs[0][0],
                                                 self.value)
        else:
            filter_criterion = self.__operator__(self.attr, self.value)
        q = q.filter(filter_criterion)
        return q

    def __call__(self, q, **kwargs):
        """
        set the query filter/join criterions
        """
        # NOTE! we don't join table here
        # TODO no sa
        if hasattr(self.attr.property, 'direction'):
            value = self.value
            if hasattr(self.value, '__mapper__'):
                value = self.model_view.modell.get_pk_value(self.value)
            filter_criterion = self.__operator__(
                self.attr.property.local_remote_pairs[0][0], value)
        else:
            filter_criterion = self.__operator__(self.attr, self.value)
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
    def __init__(self, col_name, model_view, name="", sep="--",
                 default_value=None, label=None):
        super(Between, self).__init__(col_name=col_name,
                                      model_view=model_view, name=name,
                                      default_value=default_value,
                                      label=label)
        self.sep = sep

    def __operator__(self, attr, value_list):
        if value_list[0] and not value_list[1]:
            return operator.ge(attr, value_list[0])
        elif value_list[1] and not value_list[0]:
            return operator.le(attr, value_list[1])
        return attr.between(value_list[0], value_list[1])

    __notation__ = "__between"

    @property
    def input_type(self):
        return super(Between, self).input_type * 2

    @property
    def input_class(self):
        return 'numeric-filter'


class In_(BaseFilter):
    __notation__ = "__in"

    def __operator__(self, attr, value):
        return attr.in_(set(value))

    multiple = True


class Only(BaseFilter):
    def __init__(self, col_name, model_view, label, test, notation,
                 default_value=False):
        self.__notation__ = notation
        super(Only, self).__init__(col_name=col_name, model_view=model_view,
                                   default_value=default_value,
                                   label=label)
        self.test = test
        self._value = None

    def set_sa_criterion(self, q):
        """
        set the query filter/join criterions
        """
        # NOTE! we don't join table here
        if self.value:
            filter_criterion = self.test(self.attr)
            q = q.filter(filter_criterion)
        return q

    def __call__(self, q, **kwargs):
        """
        set the query filter/join criterions
        """
        # NOTE! we don't join table here
        if self.value:
            filter_criterion = self.test(self.attr)
            q = q.filter(filter_criterion)
        return q

    @property
    def input_type(self):
        return "checkbox",

    @property
    def value(self):
        return 1 if self._value else 0

    @value.setter
    def value(self, v):
        self._value = False if v == '0' else v
