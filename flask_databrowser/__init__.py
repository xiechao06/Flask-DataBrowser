# -*- coding: UTF-8 -*-
__version__ = "0.9.0"

import types
import os
import re
import codecs
from flask import render_template, render_template_string
from flask.ext.databrowser import utils

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
        return "/" + re.sub(r"([A-Z])+", lambda m: "-" + m.groups()[0].lower(), 
                      self.model.__name__).lstrip("-") + "-list"

    @property
    def list_view_endpoint(self):
        return re.sub(r"([A-Z])+", lambda m: "_" + m.groups()[0].lower(), 
                      self.model.__name__).lstrip("_") + "_list"

    def list_view(self):
        """
        the view function of list of models
        """
        page = self._parse_args()
        kwargs = {}
        kwargs["__list_columns__"] = self.scaffold_list_columns()
        kwargs["__actions__"] = self.scaffold_actions()
        count, kwargs["__data__"] = self.scaffold_list(page)
        from flask.ext.sqlalchemy import Pagination
        kwargs["__pagination__"] = Pagination(None, page, 
                                              self.data_browser.page_size,
                                              count, kwargs["__data__"])
        kwargs.update(self.extra_params.get("list_view", {}))
        template_fname = self.blueprint.name + self.list_view_url+".html"
        if not os.path.exists(template_fname):
            template_fname = os.path.join(self.data_browser.blueprint.name, "list.haml")
        return render_template(template_fname, **kwargs)

    def _parse_args(self):
        return None 

    def scaffold_list_columns(self):
        """
        collect columns displayed in table
        """
        return (dict(label=c[1], doc=c[2]) for c in self.normalized_list_columns)

    def scaffold_actions(self):
        return 1

    def scaffold_list(self, page):
        q = self.model.query
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
        app.register_blueprint(self.blueprint)
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
