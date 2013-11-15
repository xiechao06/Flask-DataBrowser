#-*- coding:utf-8 -*-
from flask import request, Blueprint
from flask.ext.principal import PermissionDenied

from flask.ext.databrowser.column_spec import LinkColumnSpec
from flask.ext.databrowser.utils import (test_request_type, url_for_other_page, urlencode_filter, truncate_str, get_identity_name)
from flask.ext.databrowser.constants import WEB_PAGE, WEB_SERVICE


class DataBrowser(object):
    def __init__(self, app, db, page_size=16, logger=None):
        self.db = db
        self.logger = logger or app.logger
        self.blueprint = Blueprint("__data_browser__", __name__, static_folder="static", template_folder="templates")
        self.app = app
        self._init_app()
        self.page_size = page_size
        self.__registered_view_map = {}

    def _init_app(self):
        self.app.jinja_env.globals['url_for_other_page'] = url_for_other_page
        self.app.jinja_env.filters['urlencode'] = urlencode_filter
        self.app.jinja_env.filters['truncate'] = truncate_str
        self.app.before_request(test_request_type)
        # register it for using the templates of data browser
        self.app.register_blueprint(self.blueprint, url_prefix="/__data_browser__")

    def register_model(self, model, blueprint=None):
        from flask.ext.databrowser.model_view import ModelView
        return self.register_model_view(ModelView(model), blueprint)

    def register_model_view(self, model_view, blueprint, extra_params=None):
        model_view.blueprint = blueprint
        model_view.data_browser = self
        model_view.extra_params = extra_params

        if model_view.serv_type & WEB_PAGE:
            model_view.add_page_url_rule()

        if model_view.serv_type & WEB_SERVICE:
            model_view.add_api_url_rule()

        blueprint.before_request(model_view.before_request_hook)
        blueprint.after_request(model_view.after_request_hook)

        self.__registered_view_map[get_identity_name(model_view.model)] = model_view

    def get_object_link_column_spec(self, model, label=None):
        try:
            model_view = self.__registered_view_map[get_identity_name(model)]

            #TODO 移动到model_view中
            model_view.try_view(model)

            return LinkColumnSpec(col_name=model_view.backend.primary_key,
                                  formatter=lambda v, obj: model_view.url_for_object(obj, label=label,
                                                                                     url=request.url),
                                  anchor=lambda v: unicode(v), label=label)
            #TODO

        except (KeyError, PermissionDenied):
            return None

    def get_create_url(self, model, target):
        try:
            model_view = self.__registered_view_map[get_identity_name(model)]

            #TODO 移动到model_view中
            model_view.try_create()
            return model_view.url_for_object(None, url=request.url, on_fly=1, target=target)
            #TODO

        except (KeyError, PermissionDenied):
            return None

    def get_form_url(self, obj, **kwargs):
        try:
            model_view = self.__registered_view_map[get_identity_name(obj.__class__)]
            return model_view.url_for_object(obj, **kwargs)
        except KeyError:
            return None
