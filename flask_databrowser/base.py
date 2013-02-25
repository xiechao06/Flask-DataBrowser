# -*- coding: UTF-8 -*-
import types
import os
import re
import itertools
import copy
from flask import render_template, flash, request, url_for, redirect
from flask.ext.babel import gettext, ngettext
from .utils import get_primary_key, named_actions

class ModelView(object):
    __list_formatters__ = {}
    __list_columns__ = {}
    __list_filters__ = {}
    __sortable_columns__ = []
    __column_labels__ = {}
    __column_docs__ = {}
    __column_filters__ = []
    __default_order__ = None
    __batch_form_columns__ = []
    __form_columns__ = []
    __render_preprocessors__ = []

    form = None
    form_formatters = None
    column_descriptions = None
    column_hide_backrefs = True

    can_create = can_edit = can_delete = True

    __create_form__ = __edit_form__ = __batch_edit_form__ = None

    list_template = create_template = edit_template = ""


    def render(self, template, **kwargs):
        kwargs['_gettext'] = gettext
        kwargs['_ngettext'] = ngettext
        from . import helpers

        kwargs['h'] = helpers
        kwargs.update(self.extra_params.get("list_view", {}))
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
            for col_name in self.__list_columns__:
                doc = self.__column_docs__.get(col_name, "")
                if not doc:
                    try:
                        doc = getattr(self.model.__table__.c,
                                      col_name).doc or ""
                    except AttributeError: # col may not be table's field
                        pass
                yield (
                    col_name, self.__column_labels__.get(col_name, col_name),
                    doc)
        else:
            for k, c in enumerate(self.model.__table__.c):
                yield (c.name, c.name, c.doc or "")

    def generate_model_string(self, link):
        return re.sub(r"([A-Z])+", lambda m: link + m.group(0).lower(),
                      self.model.__name__).lstrip(link) + link + "list"

    def get_one(self, id_):
        return self.model.query.get_or_404(id_)

    def object_view(self, id_=None):
        if id_:
            return self.edit_view(id_)
        else:
            return self.create_view()

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
            for name, field in form._fields.iteritems():
                if field.raw_data:
                    field.populate_obj(model, name)
            self.on_model_change(form, model)
            self.session.commit()
            return True
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)),
                  'error')
            self.session.rollback()
            return False

    @property
    def creation_allowable(self):
        return self.can_create() if isinstance(self.can_create, types.MethodType) else self.can_create

    @property
    def delete_allowable(self):
        return self.can_delete() if isinstance(self.can_delete, types.MethodType) else self.can_delete

    @property
    def edit_allowable(self):
        return self.can_edit() if isinstance(self.can_edit, types.MethodType) else self.can_edit

    def create_view(self):
        """
            Create model view
        """
        if self.create_template is None:
            import posixpath

            self.create_template = posixpath.join(
                self.data_browser.blueprint.name, "form.haml")

        return_url = request.args.get('url') or url_for(
            '.' + self.list_view_endpoint)

        if not self.creation_allowable:
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

        return self.render(self.create_template, form=form,
                           return_url=return_url)


    def edit_view(self, id_):
        """
            Edit model view
        """
        id_list = [int(i) for i in id_.split(",") if i]
        if self.edit_template is None:
            import posixpath

            self.edit_template = posixpath.join(
                self.data_browser.blueprint.name, "form.haml")

        return_url = request.args.get('url') or url_for(
            '.' + self.list_view_endpoint)

        if not self.edit_allowable:
            return redirect(return_url)

        if id_list is None:
            return redirect(return_url)
        if len(id_list) == 1:
            model = self.get_one(id_list[0])

            form = self.get_edit_form(obj=model)

            if form.validate_on_submit():
                if self.update_model(form, model):
                    return redirect(return_url)
        else:
            model_list = [self.get_one(id_) for id_ in id_list]
            model = None
            if request.method == "GET":
                model = self.model()
                for attr in dir(model):
                    if attr.startswith("_"):
                        continue
                    default_value = getattr(model_list[0], attr)
                    if all(getattr(model_,
                                   attr) == default_value for model_ in model_list):
                        setattr(model, attr, default_value)
                    else:
                        for column in self.model.__table__.c:
                            if column.name == attr:
                                default = getattr(column, "default", None)
                                if default is not None:
                                    value = getattr(default, 'arg', None)

                                    if value is not None:
                                        if getattr(default, 'is_callable',
                                                   False):
                                            value = value(None)
                                        else:
                                            if not getattr(default,
                                                           'is_scalar', True):
                                                value = None
                                    setattr(model, attr, value)
                self.session.rollback()
                #由于model为临时对象，不能持久化，所以需要rollback下。

            form = self.get_batch_edit_form(obj=model)
            if form.is_submitted():
                if all(self.update_model(form, model) for model in model_list):
                    return redirect(return_url)

        return self.render(self.edit_template,
                           form=form,
                           return_url=return_url)

    def get_form(self, list_columns=None):
        if self.form:
            return self.form

        return self.scaffold_form(list_columns)

    def scaffold_form(self, list_columns):
        """
            Create form from the model.
        """
        from flask.ext.databrowser.form.convent import AdminModelConverter, get_form

        converter = AdminModelConverter(self.session, self)
        form_class = get_form(self.model, converter, only=list_columns,
                              exclude=None, field_args=None)
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

    def get_edit_form(self, obj=None):
        if self.__edit_form__ is None:
            self.__edit_form__ = self.get_form(
                self.__form_columns__ or self.__list_columns__)
        return self.__edit_form__(obj=obj)

    def get_batch_edit_form(self, obj=None):
        if self.__batch_edit_form__ is None:
            self.__batch_edit_form__ = self.get_form(
                self.__batch_form_columns__ or self.__list_columns__)
        return self.__batch_edit_form__(obj=obj)

    def __init__(self, model, model_name=""):
        self.model = model
        self.blueprint = None
        self.data_browser = None
        self.extra_params = {}
        self.__model_name = model_name
        for fltr in self.__list_filters__:
            fltr.model_view = self
        for fltr in self.__column_filters__:
            fltr.model_view = self

    @property
    def model_name(self):
        return self.__model_name or self.model.__name__

    @property
    def session(self):
        return self.data_browser.db.session

        #def __init__(self, model):
        #self.model = model
        #self.blueprint = None
        #self.data_browser = None
        #self.extra_params = {}
        #for fltr in self.__column_filters__:
        #fltr.model_view = self

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
        from flask import request, url_for, redirect
        import yaml
        from flask.ext.sqlalchemy import Pagination

        if request.method == "GET":
            page, order_by, desc = self._parse_args()
            column_filters = self._parse_filters()
            kwargs = {}
            with self.data_browser.blueprint.open_resource(
                    "static/css_classes/list.yaml") as f:
                kwargs["__css_classes__"] = yaml.load(f.read())
            kwargs["__list_columns__"] = self.scaffold_list_columns(order_by,
                                                                    desc)
            kwargs["__filters__"] = [
                f.as_dict("op", "label", "input_type", "input_class", "value",
                          "options") for f in column_filters]
            kwargs["__actions__"] = self.scaffold_actions()
            count, kwargs["__data__"] = self.scaffold_list(page, order_by,
                                                           desc,
                                                           column_filters)
            kwargs["__object_url__"] = url_for(
                ".".join([self.blueprint.name, self.object_view_endpoint]))
            kwargs["__order_by__"] = lambda col_name: col_name == order_by
            kwargs["__can_create__"] = self.creation_allowable
            kwargs["__can_edit__"] = self.edit_allowable
            if desc:
                kwargs["__desc__"] = desc
            kwargs["__pagination__"] = Pagination(None, page,
                                                  self.data_browser.page_size,
                                                  count, kwargs["__data__"])



            import posixpath
            # try user defined template
            if self.list_template and os.path.exists(os.path.join(self.blueprint.template_folder,
                                           self.list_template)):
                return self.render(self.list_template, **kwargs)
            # try html first
            template_fname = self.blueprint.name + self.list_view_url + ".html"
            if os.path.exists(os.path.join(self.blueprint.template_folder,
                                           template_fname)):
                return self.render(template_fname, **kwargs)
                # then haml
            template_fname = self.blueprint.name + self.list_view_url + ".haml"
            if os.path.exists(os.path.join(self.blueprint.template_folder,
                                           template_fname)):
                return self.render(template_fname, **kwargs)
                # finally using default
            #jinja分割模板是用"/"，在windows下，os.path.join是用"\\"，导致模板路径分割失败。所以一定要用posixpath.join
            template_fname = posixpath.join(self.data_browser.blueprint.name,
                                            "list.haml")
            return self.render(template_fname, **kwargs)
        else: # POST
            action_name = request.form.get("action")
            models = self.model.query.filter(
                getattr(self.model, get_primary_key(self.model)).in_(
                    request.form.getlist('selected-ids'))).all()
            if action_name == gettext(u"删除"):
                op = lambda model: self.session.delete(model)
                success_message = lambda models: gettext(self.model_name + 
                                                         ','.join(str(getattr(model, get_primary_key(model))) for model in models) + 
                                                         ' deleted.')
                error_message = lambda models: gettext('Failed to delete. %(error)s', error=str(ex))
            else:
                for action in self.__customized_actions__:
                    if action["name"] == action_name:
                        break
                else:
                    return gettext('such action %(action)s doesn\'t be allowed', action=action_name), 403
                tmp_models = []
                for model in models:
                    for rpp in self.__render_preprocessors__:
                        model = rpp(model)
                    tmp_models.append(model)
                models = tmp_models
                op = action["op"]
                success_message = action.get("success_message", lambda models: "")
                error_message = action.get("error_message", lambda models: "")

            try:
                processed_models = []
                for model in models:
                    op(model)
                    processed_models.append(model)
                self.session.commit()
                flash(success_message(processed_models), 'success')
            except Exception, ex:
                flash(error_message(models), 
                      'error')
                self.session.rollback()
            
            #if request.form.get("action") == gettext(u"删除"):
                #models = self.model.query.filter(
                    #getattr(self.model, get_primary_key(self.model)).in_(
                        #request.form.getlist('selected-ids'))).all()
                #try:
                    #for model in models:
                        #self.session.delete(model)
                    #self.session.commit()
                #except Exception, ex:
                    #flash(gettext('Failed to delete model. %(error)s', error=str(ex)),
                          #'error')
                    #self.session.rollback()
            #else:
                #action_name = request.form.get("action")
                #for action in self.__customized_actions__:
                    #if action["name"] == action_name:
                        #break
                #else:
                    #return gettext('such action %(action)s doesn't be allowed', action_name), 403
                #models = self.model.query.filter(
                    #getattr(self.model, get_primary_key(self.model)).in_(
                        #request.form.getlist('selected-ids'))).all()
                #try:
                    #processed_models = []
                    #for model in models:
                        #for rpp in self.__render_preprocessors__:
                            #model = rpp(model)
                        #processed_models.append(model)
                        #action["action"](model)
                    #self.session.commit()
                    #flash(action["success_message"](processed_models))
                #except Exception, ex:
                    #flash(gettext('Failed to %(action)s. %(error)s', action["name"], error=str(ex)),
                          #'error')
                    #self.session.rollback()
                        

            return redirect(url_for(
                ".".join([self.blueprint.name, self.list_view_endpoint]),
                **request.args))


    def _parse_args(self):
        from flask import request

        page = request.args.get("page", 1, type=int)
        order_by = request.args.get("order_by")
        desc = request.args.get("desc", 0, type=int)
        if order_by is None and isinstance(self.__default_order__,
                                           (list, tuple)):
            try:
                order_by, desc = self.__default_order__
                if desc == "desc":
                    desc = 1
                else:
                    desc = 0
            except ValueError:
                order_by = self.__default_order__[0]
        return page, order_by, desc

    def scaffold_list_columns(self, order_by, desc):
        """
        collect columns displayed in table
        """
        from flask import request, url_for

        for c in self.normalized_list_columns:
            if c[0] in self.__sortable_columns__:
                args = request.args.copy()
                args["order_by"] = c[0]
                if order_by == c[
                    0]: # the table is sorted by c, so revert the order
                    if not desc:
                        args["desc"] = 1
                    else:
                        try:
                            args.pop("desc")
                        except KeyError:
                            pass
                sort_url = url_for(
                    ".".join([self.blueprint.name, self.list_view_endpoint]),
                    **args)
            else:
                sort_url = ""
            yield dict(name=c[0], label=c[1], doc=c[2], sort_url=sort_url)

    def scaffold_filters(self):
        return [dict(label="a", op=dict(name="lt", id="a__lt"))]

    def scaffold_actions(self):
        l = []
        if self.delete_allowable:
            l = [{"name": "delete", "value": gettext(u"删除")}]
        if self.edit_allowable:
            l.append({"name": "batch_edit", "value": gettext(u"批量修改")})

        for action in self.__customized_actions__:
            l.append({"name": action["name"], "value": action["name"]})
        return l

    def scaffold_list(self, page, order_by, desc, filters):
        from .utils import get_primary_key

        q = self.model.query

        for filter_ in self.__list_filters__:
            q = filter_.set_sa_criterion(q)

        for filter_ in filters:
            if filter_.has_value():
                q = filter_.set_sa_criterion(q)

        if order_by:
            order_by_list = order_by.split(".")
            for order_by in order_by_list:
                order_criterion = getattr(self.model, order_by)

                if hasattr(order_criterion.property, 'direction'):
                    order_criterion = enumerate(order_criterion.property.local_columns).next()[1]
                if desc:
                    order_criterion = order_criterion.desc()
                q = q.order_by(order_criterion)
        count = q.count()
        if page:
            q = q.offset((page - 1) * self.data_browser.page_size)
        q = q.limit(self.data_browser.page_size)

        def g():
            cnter = itertools.count()
            for r in q.all():
                for rpp in self.__render_preprocessors__:
                    r = rpp(r)
                pk = self.scaffold_pk(r)
                fields = []
                for c in self.normalized_list_columns:
                    raw_value = reduce(lambda x, y: getattr(x, y),
                                       [r] + c[0].split("."))
                    formatted_value = self.format_value(raw_value, c[0])
                    # add link to object if it is primary key
                    if get_primary_key(self.model) == c[0]:
                        formatted_value = {"value": formatted_value,
                                           "link": url_for(
                                               "." + self.object_view_endpoint,
                                               id_=raw_value, url=request.url)}
                    fields.append(formatted_value)
                yield dict(pk=pk, fields=fields,
                           css=self.patch_row_css(cnter.next(), r) or "")

        return count, g()

    def patch_row_css(self, idx, row):
        return ""

    def format_value(self, v, col_name):
        try:
            formatter = self.__list_formatters__[col_name]
        except KeyError:
            return v
        return formatter(self.model, v)

    def scaffold_pk(self, entry):
        from .utils import get_primary_key

        return getattr(entry, get_primary_key(self.model))

    def _parse_filters(self):
        """
        set filter's value using args
        """
        from flask import request

        shadow_column_filters = copy.copy(self.__column_filters__)
        #如果不用copy的话，会修改原来的filter

        op_id_2_filter = dict(
            (fltr.op.id, fltr) for fltr in shadow_column_filters)
        for k, v in request.args.items():
            try:
                op_id_2_filter[k].value = v
            except KeyError:
                pass
        return shadow_column_filters


class DataBrowser(object):
    def __init__(self, app, db, page_size=16):
        self.app = app
        self.db = db
        from hamlish_jinja import HamlishExtension
        from . import utils

        app.jinja_env.add_extension(HamlishExtension)
        app.jinja_env.hamlish_mode = 'debug'
        app.jinja_env.hamlish_enable_div_shortcut = True
        app.jinja_env.globals['url_for_other_page'] = utils.url_for_other_page
        import urllib
        from jinja2 import Markup

        @app.template_filter('urlencode')
        def urlencode_filter(s):
            if type(s) == 'Markup':
                s = s.unescape()
            s = s.encode('utf8')
            s = urllib.quote_plus(s)
            return Markup(s)

        from flask import Blueprint
        # register it for using the templates of data browser
        self.blueprint = Blueprint("__data_browser__", __name__,
                                   static_folder="static",
                                   template_folder="templates")
        app.register_blueprint(self.blueprint, url_prefix="/__data_browser__")
        self.page_size = page_size


    def register_model(self, model, blueprint=None):
        return self.register_model_view(ModelView(model), blueprint)

    def register_model_view(self, model_view, blueprint, extra_params=None):
        model_view.blueprint = blueprint
        model_view.data_browser = self
        model_view.extra_params = extra_params or {}

        blueprint.add_url_rule(model_view.list_view_url,
                               model_view.list_view_endpoint,
                               model_view.list_view,
                               methods=["GET", "POST"])
        blueprint.add_url_rule(model_view.object_view_url,
                               model_view.object_view_endpoint,
                               model_view.object_view,
                               methods=["GET", "POST"])
        blueprint.add_url_rule(model_view.object_view_url + "/<string:id_>",
                               model_view.object_view_endpoint,
                               model_view.object_view,
                               methods=["GET", "POST"])
