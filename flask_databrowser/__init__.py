# -*- coding: UTF-8 -*-
__version__ = "0.9.0"

import os
import re
import codecs
from flask import render_template, render_template_string

class ModelView(object):

    def __init__(self, model):
        self.model = model
        self.blueprint = None

    @property
    def list_view_url(self):
        return "/" + re.sub(r"([A-Z])+", lambda m: "-" + m.groups()[0].lower(), 
                      self.model.__name__).lstrip("-") + "-list"

    @property
    def list_view_endpoint(self):
        return re.sub(r"([A-Z])+", lambda m: "_" + m.groups()[0].lower(), 
                      self.model.__name__).lstrip("_") + "_list"

    def list_view(self, **kwargs):
        """
        the view function of list of models
        """
        template_fname = self.blueprint.name + self.list_view_url+".html"
        if os.path.exists(template_fname):
            return render_template(template_fname, **kwargs)
        template_fname = os.path.join(__path__[0], "templates", "list.jade")
        from pyjade.utils import process
        from pyjade.ext.jinja import Compiler
        src = codecs.open(template_fname, encoding='utf-8').read()
        return render_template_string(process(src, Compiler))

class DataBrowser(object):
    
    def __init__(self, app):
       self.app = app

    def register_model(self, model, blueprint=None):
        return self.register_view(ModelView(model), blueprint)

    def register_model_view(self, model_view, blueprint=None):
        
        model_view.blueprint = blueprint
        
        blueprint.add_url_rule(model_view.list_view_url, 
                               model_view.list_view_endpoint, model_view.list_view, 
                               methods=["GET", "POST"])
