#-*- coding:utf-8 -*-
import os
from flask import request, Blueprint
from flask.ext.principal import PermissionDenied

from flask.ext.databrowser.col_spec import LinkColumnSpec
from flask.ext.databrowser.utils import (url_for_other_page,
                                         urlencode_filter,
                                         truncate_str)
from flask.ext.databrowser.constants import (WEB_PAGE, WEB_SERVICE,
                                             BACK_URL_PARAM)


class DataBrowser(object):
    def __init__(self, app, logger=None, upload_folder='uploads',
                 plugins=None):
        self.logger = logger or app.logger
        self.blueprint = Blueprint("data_browser__", __name__,
                                   static_folder="static",
                                   template_folder="templates")
        for plugin in (plugins or []):
            self._enable_plugin(plugin)
        self.app = app
        self._init_app()
        self.__registered_view_map = {}
        self.upload_folder = upload_folder
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

    def _init_app(self):
        self.app.jinja_env.globals['url_for_other_page'] = url_for_other_page
        self.app.jinja_env.filters['urlencode'] = urlencode_filter
        self.app.jinja_env.filters['truncate'] = truncate_str
        # register it for using the templates of data browser
        self.app.register_blueprint(self.blueprint,
                                    url_prefix="/data_browser__")

    def register_modell(self, modell, blueprint=None):
        from flask.ext.databrowser.model_view import ModelView

        return self.register_model_view(ModelView(modell), blueprint)

    def register_model_view(self, model_view, blueprint, extra_params=None):
        model_view.blueprint = blueprint
        model_view.data_browser = self
        model_view.extra_params = extra_params or {}

        if model_view.serv_type & WEB_PAGE:
            model_view.add_page_url_rule()

        #if model_view.serv_type & WEB_SERVICE:
        #    model_view.add_api_url_rule()

        blueprint.before_request(model_view.before_request_hook)
        blueprint.after_request(model_view.after_request_hook)

        self.__registered_view_map[model_view.modell.token] = model_view

    def get_object_link_column_spec(self, modell, label=None):
        try:
            model_view = self.__registered_view_map[modell.token]
            model_view.try_view(modell)

            #TODO no link here
            return LinkColumnSpec(col_name=model_view.modell.primary_key,
                                  formatter=lambda v, obj:
                                  model_view.url_for_object(obj, label=label,
                                                            url=request.url),
                                  anchor=lambda v: unicode(v), label=label)

        except (KeyError, PermissionDenied):
            return None

    def search_create_url(self, modell, target, on_fly=1):
        try:
            model_view = self.__registered_view_map[modell.token]
            model_view.try_create()
            import urllib2
            return model_view.url_for_object(None, on_fly=on_fly,
                                             target=target)
        except (KeyError, PermissionDenied):
            return None

    def search_obj_url(self, modell):
        '''
        note!!! it actually return an object url generator
        '''
        try:
            model_view = self.__registered_view_map[modell.token]

            def f(pk):
                obj = modell.query.get(pk)
                try:
                    model_view.try_view([model_view.expand_model(obj)])
                    return model_view.url_for_object(obj,
                                                     **{BACK_URL_PARAM:
                                                        request.url})
                except PermissionDenied:
                    return None
            return f
        except (KeyError, PermissionDenied):
            return None

    def _enable_plugin(self, plugin_name):

        pkg = __import__('flask_databrowser.plugins.' + plugin_name,
                         fromlist=[plugin_name])
        pkg.setup(self)

    def grant_all(self, identity):
        for model_view in self.__registered_view_map.values():
            model_view.grant_all(identity)
