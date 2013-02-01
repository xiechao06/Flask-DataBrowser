# -*- coding: UTF-8 -*-


__version__ = "0.9.0"

import types
import os
import re
import codecs
from flask import render_template, render_template_string, request, url_for,\
    flash, redirect
from flask.ext.babel import gettext, ngettext
from flask.ext.sqlalchemy import Pagination
import yaml

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

def expose(url='/', methods=('GET',)):
    """
        Use this decorator to expose views in your view classes.

        :param url:
            Relative URL for the view
        :param methods:
            Allowed HTTP methods. By default only GET is allowed.
    """
    def wrap(f):
        if not hasattr(f, '_urls'):
            f._urls = []
        f._urls.append((url, methods))
        return f
    return wrap


class ModelView(object):

    __list_formatters__ = {}
    __list_columns__ = {}
    __sortable_columns__ = []

    group_label = None

    form = None

    session = None

    can_create = True

    can_delete = True

    can_edit = True

    column_descriptions = None

    column_hide_backrefs = True

    __create_form__ = None


    def render(self, template, **kwargs):

        def is_required_form_field(field):
            from wtforms.validators import Required
            for validator in field.validators:
                if isinstance(validator, Required):
                    return True
            return False

        kwargs['_gettext'] = gettext
        kwargs['_ngettext'] = ngettext
        kwargs['is_required_form_field'] = is_required_form_field

        return render_template(template, **kwargs)

    def get_column_name(self, field):
        if self.__list_columns__:
            for c in self.__list_columns__:
                if isinstance(c, types.TupleType):
                    if field == c[0]:
                        return c[1]

        return self.prettify_name(field)

    # Various helpers
    def prettify_name(self, name):
        """
            Prettify pythonic variable name.

            For example, 'hello_world' will be converted to 'Hello World'

            :param name:
                Name to prettify
        """
        return name.replace('_', ' ').title()

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

    def __init__(self, model, session, list_columns=None, list_formatters=None):
        self.model = model
        self.session = session
        self.__list_columns__ = list_columns or {}
        self.__list_formatters__ = list_formatters or {}
        self.blueprint = None
        self.data_browser = None
        self.extra_params = {}


    def generate_model_string(self, link):
        return re.sub(r"([A-Z])+", lambda m: link + m.group(0).lower(),
                      self.model.__name__).lstrip(link) + link + "list"

    @property
    def list_view_url(self):
        return self.object_view_url + "-list"

    @property
    def list_view_endpoint(self):
        return self.object_view_endpoint + "_list"

    @property
    def object_view_url(self):
        return "/" + re.sub(r"([A-Z])+", lambda m: "-" + m.group(0).lower(),
                              self.model.__name__).lstrip("-")

    @property
    def object_view_endpoint(self):
        return re.sub(r"([A-Z])+", lambda m: "_" + m.group(0).lower(),
                              self.model.__name__).lstrip("_")

    def list_view(self):
        """
        the view function of list of models
        """
        page, order_by, desc = self._parse_args()
        kwargs = {}
        with self.data_browser.blueprint.open_resource("static/css_classes/list.yaml") as f:
            kwargs["__css_classes__"] = yaml.load(f.read())
        kwargs["__list_columns__"] = self.scaffold_list_columns(order_by, desc)
        kwargs["__actions__"] = self.scaffold_actions()
        count, kwargs["__data__"] = self.scaffold_list(page, order_by, desc)
        kwargs["__create_url__"] = url_for(".".join([self.blueprint.name, self.object_view_endpoint]), url=request.url)
        kwargs["__order_by__"] = lambda col_name: col_name == order_by
        if desc:
            kwargs["__desc__"] = desc
            kwargs["__pagination__"] = Pagination(None, page,
                                              self.data_browser.page_size,
                                              count, kwargs["__data__"])
        kwargs.update(self.extra_params.get("list_view", {}))
        template_fname = self.blueprint.name + self.list_view_url+".html"
        if not os.path.exists(template_fname):
            import posixpath
            #jinja分割模板是用"/"，在windows下，os.path.join是用"\\"，导致模板路径分割失败。所以一定要用posixpath.join
            template_fname = posixpath.join(self.data_browser.blueprint.name,"list.haml")
        return self.render(template_fname, **kwargs)


    def object_view(self, id_=None):
        if id_:
            return self.edit_view(id_)
        else:
            return self.create_view()

    def get_one(self, id_):
        return self.model.query.get(id_)

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

        


    # Model handlers
    def on_model_change(self, form, model):
        """
            Allow to do some actions after a model was created or updated.

            Called from create_model and update_model in the same transaction
            (if it has any meaning for a store backend).

            By default do nothing.
        """
        pass

    def on_model_delete(self, model):
        """
            Allow to do some actions before a model will be deleted.

            Called from delete_model in the same transaction
            (if it has any meaning for a store backend).

            By default do nothing.
        """
        pass

        # Model handlers

    def create_model(self, form):
        """
            Create model from form.

            :param form:
                Form instance
        """
        try:
            model = self.model()
            form.populate_obj(model)
            self.session.add(model)
            self.on_model_change(form, model)
            self.session.commit()
            return True
        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)),
                  'error')
            self.session.rollback()
            return False

    def update_model(self, form, model):
        """
            Update model from form.

            :param form:
                Form instance
            :param model:
                Model instance
        """
        try:
            form.populate_obj(model)
            self.on_model_change(form, model)
            self.session.commit()
            return True
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)),
                  'error')
            self.session.rollback()
            return False

    def delete_model(self, model):
        """
            Delete model.

            :param model:
                Model to delete
        """
        try:
            self.on_model_delete(model)
            self.session.flush()
            self.session.delete(model)
            self.session.commit()
            return True
        except Exception, ex:
            flash(gettext('Failed to delete model. %(error)s', error=str(ex)),
                  'error')
            self.session.rollback()
            return False



    def create_view(self):
        """
            Create model view
        """
        return_url = request.args.get('url') or url_for(
            '.' + self.list_view_endpoint)

        if not self.can_create:
            return redirect(return_url)

        form = self.get_create_form()

        if form.validate_on_submit():
            if self.create_model(form):
                if '_add_another' in request.form:
                    flash(gettext('Model was successfully created.'))
                    return redirect(url_for('.' + self.object_view_endpoint,
                                            url=return_url))
                else:
                    return redirect(return_url)
        import posixpath
        return self.render(posixpath.join(self.data_browser.blueprint.name,"form.haml"), form=form,
                           return_url=return_url)


    def edit_view(self, id_):
        """
            Edit model view
        """
        return_url = request.args.get('url') or url_for(
            '.' + self.list_view_endpoint)

        if not self.can_edit:
            return redirect(return_url)

        if id_ is None:
            return redirect(return_url)

        model = self.get_one(id_)

        if model is None:
            return redirect(return_url)

        form = self.edit_form(obj=model)

        if form.validate_on_submit():
            if self.update_model(form, model):
                return redirect(return_url)

        return self.render(self.edit_template,
                               form=form,
                               return_url=return_url)

    def delete_view(self):
        """
            Delete model view. Only POST method is allowed.
        """
        return_url = request.args.get('url') or url_for(
            '.' + self.list_view_endpoint)

        if not self.can_delete:
            return redirect(return_url)

        id = request.args.get('id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model:
            self.delete_model(model)

        return redirect(return_url)


    def get_form(self):
        if self.form:
            return self.form

        return self.scaffold_form()

    def scaffold_form(self):
        """
            Create form from the model.
        """
        from flask_admin.contrib.sqlamodel.form import AdminModelConverter, get_form
        converter = AdminModelConverter(self.session, self)
        form_class = get_form(self.model, converter,
                          only=self.__list_columns__,
                          exclude=None,
                          field_args=None)

        return form_class

    def scaffold_inline_form_models(self, form_class):
        """
            Contribute inline models to the form

            :param form_class:
                Form class
        """
        converter = self.model_form_converter(self.session, self)
        inline_converter = self.inline_model_form_converter(self.session, self)

        for m in self.inline_models:
            form_class = inline_converter.contribute(converter,
                                                self.model,
                                                form_class,
                                                m)

        return form_class

    def get_create_form(self):
        if self.__create_form__ is None:
            self.__create_form__ = self.get_form()
        return self.__create_form__()



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

    def register_model(self, model, session, blueprint=None, list_columns=None, list_formatters=None):
        return self.register_model_view(ModelView(model, session, list_columns, list_formatters), blueprint)

    def register_model_view(self, model_view, blueprint, extra_params=None):
        
        model_view.blueprint = blueprint
        model_view.data_browser = self
        model_view.extra_params = extra_params or {}
        
        blueprint.add_url_rule(model_view.list_view_url, 
                               model_view.list_view_endpoint, model_view.list_view, 
                               methods=["GET", "POST"])
        blueprint.add_url_rule(model_view.object_view_url,
                               model_view.object_view_endpoint,
                               model_view.object_view, methods=["GET", "POST"])
        blueprint.add_url_rule(model_view.object_view_url + "/<int:id_>",
                               model_view.object_view_endpoint,
                               model_view.object_view, methods=["GET", "POST"])
