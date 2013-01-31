# -*- coding: UTF-8 -*-
__version__ = "0.9.0"

import types
import os
import re
import codecs
from flask import render_template, render_template_string, request, url_for
from flask.ext.databrowser import utils
from flask.ext.sqlalchemy import Pagination

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

class ModelView(object):

    __list_formatters__ = {}
    __list_columns__ = {}
    __sortable_columns__ = []

    @property
    def normalized_list_columns(self):
        if self.__list_columns__: 
            for c in self.__list_columns__:
                if isinstance(c, types.TupleType):
                    col_name = c[0]
                    col_label = c[1]
                    col_doc = c[2] if len(c) == 3 else ""
                else:
                    col_name = c
                    col_label = c
                    col = getattr(self.model, col_name)
                    try:
                        col_doc = getattr(col, "doc")
                    except AttributeError:
                        col_doc = ""
                yield (col_name, col_label, col_doc) 
        else:
            for k, c in enumerate(self.model.__table__.c):
                yield (c.name, c.name, c.doc if c.doc else "")

    def __init__(self, model):
        self.model = model
        self.blueprint = None
        self.data_browser = None
        self.extra_params = {}

    @property
    def list_view_url(self):
        return self.object_view_url + "-list"

    @property
    def list_view_endpoint(self):
        return self.object_view_endpoint + "_list"

    @property
    def object_view_url(self):
        return "/" + re.sub(r"([A-Z])+", lambda m: "-" + m.groups()[0].lower(), 
                              self.model.__name__).lstrip("-")

    @property
    def object_view_endpoint(self):
        return re.sub(r"([A-Z])+", lambda m: "_" + m.groups()[0].lower(), 
                              self.model.__name__).lstrip("_")

    def list_view(self):
        """
        the view function of list of models
        """
        page, order_by, desc = self._parse_args()
        kwargs = {}
        kwargs["__list_columns__"] = self.scaffold_list_columns(order_by, desc)
        kwargs["__actions__"] = self.scaffold_actions()
        count, kwargs["__data__"] = self.scaffold_list(page, order_by, desc)
        kwargs["__create_url__"] = url_for(".".join([self.blueprint.name, self.object_view_endpoint]))
        kwargs["__order_by__"] = lambda col_name: col_name == order_by
        if desc:
            kwargs["__desc__"] = desc
        kwargs["__pagination__"] = Pagination(None, page, 
                                              self.data_browser.page_size,
                                              count, kwargs["__data__"])

        kwargs.update(self.extra_params.get("list_view", {}))
        template_fname = self.blueprint.name + self.list_view_url+".html"
        if not os.path.exists(template_fname):
            template_fname = os.path.join(self.data_browser.blueprint.name, "list.haml")
        return render_template(template_fname, **kwargs)

    def object_view(self, id_):
        pass

    def _parse_args(self):
        from flask import request
        order_by = request.args.get("order_by")
        desc = int(request.args.get("desc", 0))
        return None, order_by, desc

    def scaffold_list_columns(self, order_by, desc):
        """
        collect columns displayed in table
        """
        for c in self.normalized_list_columns:
            if c[0] in self.__sortable_columns__:
                args = request.args.copy()
                args["order_by"] = c[0]
                if order_by == c[0]: # the table is sorted by c, so revert the order
                    if not desc:
                        args["desc"] = 1
                    else:
                        try:
                            args.pop("desc")
                        except KeyError:
                            pass
                sort_url = url_for(".".join([self.blueprint.name, self.list_view_endpoint]), 
                                   **args)
            else:
                sort_url = ""
            yield dict(name=c[0], label=c[1], doc=c[2], sort_url=sort_url)

    def scaffold_actions(self):
        return 1

    def scaffold_list(self, page, order_by, desc):
        q = self.model.query
        if order_by:
            order_criterion = getattr(self.model, order_by)
            if desc:
                order_criterion = order_criterion.desc()
            q = q.order_by(order_criterion)
        count = q.count()
        if page:
            q.offset((page-1) * self.data_browser.page_size)
            q.limit(self.data_browser.page_size)
        def g():
            for r in q.all():
                pk = self.scaffold_pk(r)
                fields = []
                for c in self.normalized_list_columns:
                    fields.append(self.format_value(getattr(r, c[0]), c[0]))
                yield dict(pk=pk, fields=fields)
        return count, g()

    def format_value(self, v, col_name):
        try:
            formatter = self.__list_formatters__[col_name]
        except KeyError:
            return v
        return formatter(self.model, v)

    def scaffold_pk(self, entry):
        return getattr(entry, get_primary_key(self.model))

        

class DataBrowser(object):
    
    def __init__(self, app, page_size=16):
        self.app = app
        from jinja2 import Environment
        from hamlish_jinja import HamlishExtension
        app.jinja_env.add_extension(HamlishExtension)
        app.jinja_env.globals['url_for_other_page'] = utils.url_for_other_page
        from flask import Blueprint
        # register it for using the templates of data browser
        self.blueprint = Blueprint("__data_browser__", __name__, 
                                   static_folder="static", 
                                   template_folder="templates")
        app.register_blueprint(self.blueprint, url_prefix="/__data_browser__")
        self.page_size = page_size


    def register_model(self, model, blueprint=None):
        return self.register_view(ModelView(model), blueprint)

    def register_model_view(self, model_view, blueprint, extra_params={}):
        
        model_view.blueprint = blueprint
        model_view.data_browser = self
        model_view.extra_params = extra_params
        
        blueprint.add_url_rule(model_view.list_view_url, 
                               model_view.list_view_endpoint, model_view.list_view, 
                               methods=["GET", "POST"])
        blueprint.add_url_rule(model_view.object_view_url, 
                               model_view.object_view_endpoint, model_view.object_view, 
                               methods=["GET", "POST"])

