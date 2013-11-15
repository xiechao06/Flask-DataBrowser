# -*- coding: UTF-8 -*-
import copy
import itertools
import json
import operator
import re
import sys
import types
from collections import OrderedDict
import urlparse

import werkzeug
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict

from flask import (render_template, flash, request, url_for, redirect, Flask, make_response, jsonify)
from flask.ext.babel import _
from flask.ext.principal import PermissionDenied
from flask.ext.sqlalchemy import Pagination

from flask.ext.databrowser import sa_utils, helpers, filters, fake_form
from flask.ext.databrowser.column_spec import (LinkColumnSpec, ColumnSpec, InputColumnSpec, PlaceHolderColumnSpec,
                                               FileColumnSpec)
from flask.ext.databrowser.convert import ValueConverter
from flask.ext.databrowser.exceptions import ValidationError
from flask.ext.databrowser.extra_widgets import PlaceHolder
from flask.ext.databrowser.form import form
from flask.ext.databrowser.convert_utils import convert_column, get_dict_converter
from flask.ext.databrowser.constants import WEB_SERVICE, WEB_PAGE


class ModelView(object):
    """
    changelog v2: remove params: __create_columns__, __sortable_columns__

    现确立如下规则：
    没有"_"开头的属性（包括property）可以重写
    以"_"开头的属性，理论上不应该重写
    """

    # 可以重写的属性
    __column_formatters__ = {}
    __list_columns__ = {}
    __column_labels__ = {}
    __column_docs__ = {}
    __column_filters__ = []
    default_order = None
    __batch_form_columns__ = []
    __form_columns__ = []
    __customized_actions__ = []
    __max_col_len__ = 255
    __model_list__ = []
    __extra_fields__ = {}

    serv_type = WEB_PAGE | WEB_SERVICE

    language = "en"
    column_hide_backrefs = True
    __create_form__ = __edit_form__ = __batch_edit_form__ = None
    list_template = "__data_browser__/list.html"
    create_template = edit_template = "__data_browser__/form.html"
    can_batchly_edit = True

    hidden_pk = True
    create_in_steps = False
    step_create_templates = []

    def __init__(self, backend):
        self.backend = backend
        self.model = self.backend.model
        self.blueprint = None
        self.extra_params = {}
        self.data_browser = None
        self.__list_column_specs = []
        self.__normalized_create_columns = []
        self.__normalized_form_columns = []
        self._default_list_filters = []

    # 可以重写的property
    @property
    def create_columns(self):
        return []

    def _get_create_columns(self):
        """
        get all the *NORMALIZED* create columns for model view. which means,
        if you override this method, you should guarantee that return value are
        normalized. see ModelView.normalize_create_columns
        """
        if not self.__normalized_create_columns:
            # 只接受form的字段或者InputColumnSpec或者PlaceholderColumnSpec
            columns = [col for col in self.create_columns if
                       isinstance(col, (basestring, InputColumnSpec, PlaceHolderColumnSpec) and col.as_input)]

            self.__normalized_create_columns = self._normalize_columns(columns)
        return self.__normalized_create_columns

    #TODO 重构
    @property
    def form_columns(self):
        """
        get all the *NORMALIZED* form columns for model view. which means,
        if you override this method, you should guarantee that return value are
        normalized. see ModelView.normalize_form_columns 
        """
        # only for backward compatiple, feel comfortable to ignore it
        if hasattr(self, 'get_form_columns') and isinstance(self.get_form_columns, types.MethodType):
            return self._normalize_columns(self.get_form_columns())
        if not self.__normalized_form_columns:
            self.__normalized_form_columns = self._normalize_columns(self.__form_columns__)
        return self.__normalized_form_columns

    def get_step_create_template(self, step):
        try:
            return self.step_create_templates[step] or '__data_browser__/form.html'
        except IndexError:
            return '__data_browser__/form.html'

    def _get_column_doc(self, column):
        return self.__column_docs__.get(column) or self.backend.get_column_doc(column)

    def _normalize_columns(self, columns):
        """
        this utility function handle the following matters:

            * if columns not defined in fieldsets, add them to one fieldset whose name is empty string
            * if columns are empty undefined, fill the form_columns from model
            * convert all the column of 'basestring' to InputColumn
            * purge the create columns, only columns defined in model, foreign key could be displayed in edit form,
            and pass the test
            * fill the label and doc of each column
        """
        def _input_column_spec_from_kolumne(k):
            return InputColumnSpec(k.key,
                                   doc=self._get_column_doc(k.key),
                                   label=self.__column_labels__.get(k.key),
                                   property_=k)

        if not columns:
            return {"": [_input_column_spec_from_kolumne(k) for k in self.backend.kolumnes]}

        ret = OrderedDict()
        col_name_2_prop = dict((k.key, k) for k in self.backend.kolumnes)

        if isinstance(columns, types.DictType):
            fieldsets = columns
        else:
            fieldsets = {"": columns}

        for fieldset_name, columns in fieldsets.items():
            ret[fieldset_name] = []
            for col in columns:
                if isinstance(col, basestring):
                    if col in col_name_2_prop:
                        ret[fieldset_name].append(_input_column_spec_from_kolumne(col_name_2_prop[col]))
                elif col.col_name in col_name_2_prop:
                    col.property_ = col_name_2_prop[col.col_name]
                    if col.label is None:
                        col.label = self.__column_labels__.get(col.col_name)
                    if col.doc is None:
                        col.doc = self._get_column_doc(col.col_name)
                    ret[fieldset_name].append(col)

        return ret

    @property
    def _session(self):
        #TODO 移至backend
        return self.data_browser.db.session

    @property
    def list_view_url(self):
        return self.object_view_url + "-list"

    @property
    def list_api_url(self):
        return "/apis" + self.list_view_url

    @property
    def obj_api_url(self):
        return "/apis" + self.object_view_url

    @property
    def filters_api_url(self):
        return "/apis" + self.object_view_url + "-filters"

    @property
    def sort_columns_api_url(self):
        return "/apis" + self.object_view_url + "-sort-columns"

    @property
    def list_view_endpoint(self):
        return self.object_view_endpoint + "_list"


    @property
    def list_api_endpoint(self):
        return self.object_view_endpoint + "_list_api"

    @property
    def obj_api_endpoint(self):
        return self.object_view_endpoint + "_api"

    @property
    def create_api_endpoint(self):
        return self.object_view_endpoint + "_create_api"

    @property
    def sort_columns_api_endpoint(self):
        return self.object_view_endpoint + "_sort_columns_api"

    @property
    def filters_api_endpoint(self):
        return self.object_view_endpoint + "_filters_api"

    @property
    def object_view_url(self):
        return "/" + re.sub(r"([A-Z]+)", lambda m: "-" + m.groups()[0].lower(),
                            self.model.__name__).lstrip("-")

    @property
    def list_column_specs(self):
        if self.__list_column_specs:
            return self.__list_column_specs

        list_columns = self.get_list_columns()
        if not list_columns:
            list_columns = [col.name for col in self.backend.columns]
        if list_columns:
            for col in list_columns:
                if isinstance(col, basestring):
                    col = self._col_spec_from_str(col)
                else:
                    assert isinstance(col, ColumnSpec)
                    col.label = self.__column_labels__.get(col.col_name, col.col_name) if (
                        col.label is None) else col.label

                self.__list_column_specs.append(col)

        return self.__list_column_specs

    @property
    def object_view_endpoint(self):
        return re.sub(r"([A-Z]+)", lambda m: "_" + m.groups()[0].lower(),
                      self.model.__name__).lstrip("_")

    def before_request_hook(self):
        pass

    def after_request_hook(self, response):
        return response

    def within_domain(self, url, bp_name):
        url = url.lower()
        import urlparse

        path_ = urlparse.urlparse(url).path
        segs = path_.split("/")[1:]
        if len(segs) < 2:
            return False
        if segs[0] != bp_name.lower():
            return False
        return any("/" + seg in {self.object_view_url, self.list_view_url} for seg in segs[1:])

    def __list_filters__(self):
        return []

    def _get_default_list_filters(self):
        if not self._default_list_filters:
            for filter_ in self.__list_filters__():
                if not filter_.model_view:
                    filter_.model_view = self
                self._default_list_filters.append(filter_)
        return self._default_list_filters

    def preprocess(self, obj):
        return obj

    def render(self, template, **kwargs):
        from . import helpers

        kwargs['h'] = helpers
        return render_template(template, **kwargs)

    def prettify_name(self, name):
        """
            Prettify pythonic variable name.

            For example, 'hello_world' will be converted to 'Hello World'

            :param name:
                Name to prettify
        """
        return name.replace('_', ' ').title()

    def _col_spec_from_str(self, col):
        """
        get column specification from string
        """
        # we get document from sqlalchemy models
        doc = self.__column_docs__.get(col, "")
        if not doc:
            doc = self.backend.get_column_doc(col)
        label = self.__column_labels__.get(col, col)
        if self.backend.primary_key == col:
            formatter = lambda x, obj: self.url_for_object(obj, url=request.url)
            col_spec = LinkColumnSpec(col, doc=doc, anchor=lambda x: x,
                                      formatter=formatter,
                                      label=label, css_class="control-text")
        else:
            formatter = self.__column_formatters__.get(col, lambda x, obj: unicode(x))
            col_spec = ColumnSpec(col, doc=doc, formatter=formatter, label=label, css_class="control-text")
        return col_spec

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

    def create_model(self, form):
        """
            Create model from form.

            :param form:
                Form instance
        """
        try:
            model = self.populate_obj(form)
            self.on_model_change(form, model)
            self._session.add(model)
            self._session.commit()
            return model
        except Exception:
            self._session.rollback()
            raise

    def populate_obj(self, form):
        model = self.model()
        form.populate_obj(model)
        return model

    def get_column_filters(self):
        return self.__column_filters__

    def _get_column_filters(self):
        ret = []
        for fltr in self.get_column_filters():
            if not fltr.model_view:
                fltr.model_view = self
            ret.append(fltr)
        return ret

    def get_customized_actions(self, processed_objs=None):
        return self.__customized_actions__

    def _get_customized_actions(self, processed_objs=None):
        ret = []
        for action in self.get_customized_actions(processed_objs):
            action.model_view = self
            ret.append(action)
        return ret

    def update_objs(self, form, objs):
        """
            Update objs from form.
            :param form:
                Form instance
            :param objs:
                a list of Model instance
        """

        action_name = request.form.get("__action__")
        processed_objs = [self.preprocess(obj) for obj in objs]

        if action_name:
            for action in self._get_customized_actions(processed_objs):
                if action.name == action_name:
                    action.try_(processed_objs)
                    for obj in processed_objs:
                        ret_code = action.test_enabled(obj)
                        if ret_code != 0:
                            flash(_(u"can't apply %(action)s due to %(reason)s",
                                    action=action.name,
                                    reason=action.get_forbidden_msg_formats()[
                                               ret_code] % unicode(obj)),
                                  'error')
                            return False
                    try:
                        ret = action.op_upon_list(processed_objs, self)
                        if isinstance(ret, tuple):
                            flash(ret[-1], "error")
                            return False

                        self._session.commit()
                        if isinstance(ret, werkzeug.wrappers.BaseResponse) and ret.status_code == 302:
                            if not action.direct:
                                flash(action.success_message(processed_objs), 'success')
                            return ret
                        if not action.direct:
                            flash(action.success_message(processed_objs), 'success')
                        return True
                    except Exception, ex:
                        flash(
                            _('Failed to update %(model_name)s %(objs)s due to %(error)s', model_name=self._model_name,
                              objs=",".join(unicode(obj) for obj in processed_objs), error=unicode(ex)), 'error')
                        self._session.rollback()
                        raise
            raise ValidationError(
                _('invalid action %(action)s', action=action_name))
            # normal modify
        try:
            self.try_edit(processed_objs)
            # compute the field should be holded
            holded_fields = set(name[len("hold-value-"):] for name, field in request.form.iteritems() if
                                name.startswith("hold-value-"))
            for obj in objs:
                for name, field in form._fields.iteritems():
                    from wtforms.fields import FileField

                    if isinstance(field, FileField):
                        file_ = request.files[field.name]
                        if file_:
                            filename = secure_filename(file_.filename)
                            import os

                            upload_folder = self.data_browser.app.config.get("UPLOAD_FOLDER", "")
                            if not os.path.isdir(upload_folder):
                                os.makedirs(upload_folder)
                            file_.save(os.path.join(self.data_browser.app.config.get("UPLOAD_FOLDER", ""), filename))
                            setattr(obj, field.name, filename)
                        continue
                    if name not in holded_fields and not helpers.is_unique_form_field(
                            field) and field.data is not None:
                        field.populate_obj(obj, name)

                self.do_update_log(obj, _("update"))
                flash(_(u"%(model_name)s %(obj)s was updated and saved",
                        model_name=self._model_name, obj=unicode(obj)))
                self.on_model_change(form, obj)
                self._session.commit()
            return True
        except Exception, ex:
            flash(
                _('Failed to update %(model_name)s %(obj)s due to %(error)s',
                  model_name=self._model_name, obj=",".join([unicode(obj) for obj in objs]),
                  error=unicode(ex)), 'error')
            self._session.rollback()
            return False

    def try_view(self, processed_objs=None):
        """
        control if user could view objects list or object
        NOTE!!! don't return anything, if you determine that something should't be viewed,
        throw PermissionDenied

        :param objs: the objs to be viewed, is None, we are in list view
        """
        pass

    def try_create(self):
        """
        control if user could create the new object
        """
        pass

    def try_edit(self, processed_objs=None):
        pass

    def create_view_2(self):
        #TODO 重写
        self.try_create()

        return_url = request.args.get('url') or url_for('.' + self.list_view_endpoint)
        on_fly = int(request.args.get("on_fly", 0))
        current_step = int(request.args.get('__step__', 0)) if self.create_in_steps else None
        create_columns = self._get_create_columns()
        form = self._get_create_form(create_columns, current_step)
        if form.validate_on_submit():
            model = self.create_model(form)
            if model:
                self.do_create_log(model)
                flash(_(u'%(model_name)s %(model)s was created successfully',
                        model_name=self._model_name, model=unicode(model)))
                if request.form.get("__builtin_action__") == _("add another"):
                    return redirect(self.url_for_object(url=return_url))
                else:
                    if on_fly:
                        return render_template("__data_browser__/on_fly_result.html",
                                               model_cls=self._model_name,
                                               obj=unicode(model),
                                               obj_pk=self.backend.get_pk_value(model),
                                               target=request.args.get("target"))
                    else:
                        return redirect(return_url)
        #get or validate error
        kwargs = self._get_extra_params("create_view")
        if self.create_in_steps:
            create_template = self.get_step_create_template(current_step)
            kwargs["last_step"], kwargs["next_step"] = self._get_arround_steps(current_step, create_columns.keys())
        else:
            create_template = self.create_template
        resp = self.render(create_template, form=form, return_url=return_url, **kwargs)

        if form.is_submitted():
            # alas! something wrong
            resp = make_response(resp, 403)
            resp.headers["Warning"] = u"&".join([k + u"-" + u"; ".join(v) for k, v in form.errors.items()]).encode(
                "utf-8")
        return resp

    def _get_arround_steps(self, current_step, step_names):
        last_step = None
        next_step = None
        if current_step > 0:
            args = request.args.to_dict()
            args['__step__'] = current_step - 1
            last_step = {
                'name': step_names[current_step - 1],
                'url': urlparse.urlunparse(
                    ('', '', request.path, '', '&'.join(k + '=' + unicode(v) for k, v in args.items()), ''))
            }
        if current_step < len(step_names) - 1:
            args = request.args.to_dict()
            args['__step__'] = current_step + 1
            next_step = {
                'name': self._get_create_columns().keys()[current_step + 1],
                'url': urlparse.urlunparse(
                    ('', '', request.path, '', '&'.join(k + '=' + unicode(v) for k, v in args.items()), ''))
            }
        return last_step, next_step

    def create_view(self):
        self.try_create()

        return_url = request.args.get('url') or url_for(
            '.' + self.list_view_endpoint)
        on_fly = int(request.args.get("on_fly", 0))

        if self.create_in_steps:
            current_step = int(request.args.get('__step__', 0))
            create_columns = dict([self._get_create_columns().items()[current_step]])
        else:
            create_columns = self._get_create_columns()
        form = self.get_create_form()
        # if submit and validated, go, else re-display the create page and show the errors
        if form.validate_on_submit():
            model = self.create_model(form)
            if model:
                self.do_create_log(model)
                flash(_(u'%(model_name)s %(model)s was created successfully',
                        model_name=self._model_name, model=unicode(model)))
                if request.form.get("__builtin_action__") == _("add another"):
                    return redirect(self.url_for_object(url=return_url))
                else:
                    if on_fly:
                        return render_template("__data_browser__/on_fly_result.html",
                                               model_cls=self._model_name,
                                               obj=unicode(model),
                                               obj_pk=self.backend.get_pk_value(model),
                                               target=request.args.get("target"))
                    else:
                        return redirect(return_url)
        create_url_map = {}
        for col in [f.name for f in form if f.name != "csrf_token"]:
            col_name = col if isinstance(col, basestring) else col.col_name
            attr = getattr(self.model, col_name)
            if hasattr(attr.property, "direction"):
                remote_side = attr.property.mapper.class_
                create_url = self.data_browser.get_create_url(remote_side, col_name)
                if create_url:
                    create_url_map[col] = create_url

        compound_form = self.get_create_compound_form(form, create_columns)
        form = compound_form or form

        placeholder_kwargs = {}
        form_kwargs = self._extra_params.get("create_view", {})
        for k, v in form_kwargs.items():
            if isinstance(v, types.FunctionType):
                v = v(self)
            placeholder_kwargs[k] = v

        for f in form:
            if isinstance(f.widget, PlaceHolder):
                f.widget.set_args(**placeholder_kwargs)

        fieldset_list = []

        if isinstance(create_columns, types.DictType):
            for fieldset, cols in create_columns.items():
                fieldset_list.append(
                    (fieldset, [form[col.col_name if isinstance(col, ColumnSpec) else col] for col in cols]))
        else:
            fieldset_list.append(("", form))

        last_step = None
        next_step = None
        if self.create_in_steps:
            create_template = self.get_step_create_template(current_step)
            if current_step:
                args = request.args.to_dict()
                args['__step__'] = current_step - 1
                last_step = {
                    'name': self._get_create_columns().keys()[current_step - 1],
                    'url': urlparse.urlunparse(
                        ('', '', request.path, '', '&'.join(k + '=' + unicode(v) for k, v in args.items()), ''))
                }

                previous_columns = {}
                for i in xrange(0, current_step):
                    for c in self._get_create_columns().values()[i]:
                        previous_columns[c.col_name] = c.label or c.col_name

                if previous_columns:
                    for k, v in request.args.iterlists():
                        if k in previous_columns:
                            col_def = operator.attrgetter(k)(self.model)
                            if hasattr(col_def.property, 'direction'): # is a relation ship
                                v = unicode(sa_utils.remote_side(col_def).query.get(v))
                            placeholder_kwargs.setdefault('previous_steps_info', []).append(
                                (previous_columns[k], v[0] if len(v) == 1 else v))

            if current_step < len(self._get_create_columns()) - 1:
                args = request.args.to_dict()
                args['__step__'] = current_step + 1
                next_step = {
                    'name': self._get_create_columns().keys()[current_step + 1],
                    'url': urlparse.urlunparse(
                        ('', '', request.path, '', '&'.join(k + '=' + unicode(v) for k, v in args.items()), ''))
                }
        else:
            create_template = self.create_template
        placeholder_kwargs['last_step'] = last_step
        placeholder_kwargs['next_step'] = next_step
        resp = self.render(create_template, form=form,
                           fieldset_list=fieldset_list,
                           create_url_map=create_url_map,
                           return_url=return_url, extra="" if on_fly else "create",
                           help_message=self.get_create_help(),
                           hint_message=self.create_hint_message(),
                           model_view=self,
                           **placeholder_kwargs)
        if form.is_submitted():
            # alas! something wrong
            resp = make_response(resp, 403)
            resp.headers["Warning"] = u"&".join([k + u"-" + u"; ".join(v) for k, v in form.errors.items()]).encode(
                "utf-8")
        return resp

    def do_update_log(self, obj, action):
        from flask.ext.login import current_user

        def _log(obj_):
            self.data_browser.logger.debug(
                _("%(user)s performed %(action)s", user=unicode(current_user), action=action),
                extra={"obj": obj_, "obj_pk": self.backend.get_pk_value(obj_),
                       "action": action, "actor": current_user})

        if isinstance(obj, list) or isinstance(obj, tuple):
            for obj_ in obj:
                _log(obj_)
        else:
            _log(obj)

    def do_create_log(self, obj):
        from flask.ext.login import current_user

        self.data_browser.logger.debug(
            _('%(model_name)s %(model)s was created successfully',
              model_name=self._model_name, model=unicode(obj)),
            extra={"obj": obj, "obj_pk": self.backend.get_pk_value(obj),
                   "action": _(u"create"), "actor": current_user})

    def batch_edit_hint_message(self, objs, read_only=False):
        if read_only:
            return _(
                u"you are viewing %(model_name)s-%(obj)s, "
                u"since you have only read permission",
                model_name=self._model_name,
                obj=",".join(unicode(model) for model in objs))
        else:
            return _(u"edit %(model_name)s-%(objs)s",
                     model_name=self._model_name,
                     objs=",".join(unicode(model) for model in objs))

    def edit_hint_message(self, obj, read_only=False):
        if read_only:
            return _(
                u"you are viewing %(model_name)s-%(obj)s, "
                u"since you have only read permission",
                model_name=self._model_name, obj=unicode(obj))
        else:
            return _(u"edit %(model_name)s-%(obj)s",
                     model_name=self._model_name,
                     obj=unicode(obj))

    def create_hint_message(self):
        return _(u"create %(model_name)s", model_name=self._model_name)

    def edit_view(self, id_):
        """
            Edit model view
        """
        if isinstance(id_, int):
            id_list = [id_]
        else:
            id_list = [i for i in id_.split(",") if i]

        return_url = request.args.get('url') or url_for('.' + self.list_view_endpoint)

        if id_list is None:
            return redirect(return_url)

        compound_form = None
        pre_url = next_url = ""
        if len(id_list) == 1:
            model = self.get_one(id_list[0])
            self.try_view([model])  # first, we test if we could view
            cdx = request.args.get("cdx", None, int)
            if cdx:
                page, order_by, desc = self._parse_args()
                if cdx == 1:
                    # only retrieve the next one
                    count, models = self.query_data(order_by, desc, [],
                                                    offset=cdx, limit=1)
                    try:
                        next_model = models[0]
                        next_url = self.url_for_object(next_model, url=return_url,
                                                       cdx=cdx + 1)
                    except IndexError:
                        pass
                else:
                    # only retrieve the previous and next url
                    count, models = self.query_data(order_by, desc, [],
                                                    offset=cdx - 2, limit=3)
                    pre_model = models[0]
                    pre_url = self.url_for_object(pre_model, cdx=cdx - 1,
                                                  url=return_url)
                    try:
                        # note, next object may be None
                        next_model = models[2]
                        next_url = self.url_for_object(next_model, cdx=cdx + 1,
                                                       url=return_url)
                    except IndexError:
                        pass

            preprocessed_obj = self.preprocess(model)
            try:
                self.try_edit([preprocessed_obj])
                read_only = False
            except PermissionDenied:
                read_only = True
            form = self.get_edit_form(obj=model)
            if form.validate_on_submit():  # ON POST
                ret = self.update_objs(form, [model])
                if ret:
                    if isinstance(ret, werkzeug.wrappers.BaseResponse) and ret.status_code == 302:
                        return ret
                    else:
                        return redirect(request.url)
                # ON GET
            compound_form = self.get_compound_edit_form(obj=model, form=form)
            hint_message = self.edit_hint_message(preprocessed_obj, read_only)
            all_customized_actions = self._get_customized_actions([preprocessed_obj])
            help_message = self.get_edit_help(preprocessed_obj)
            actions = all_customized_actions
        else:
            model_list = [self.get_one(id_) for id_ in id_list]
            preprocessed_objs = [self.preprocess(obj) for obj in model_list]
            self.try_view(preprocessed_objs) # first, we test if we could view
            model = None
            if request.method == "GET":
                model = type("_temp", (object,), {})()
                for prop in self.model.__mapper__.iterate_properties:
                    attr = prop.key
                    default_value = getattr(model_list[0], attr)
                    if all(getattr(model_,
                                   attr) == default_value for model_ in
                           model_list):
                        setattr(model, attr, default_value)
            try:
                self.try_edit(preprocessed_objs)
                read_only = False
            except PermissionDenied:
                read_only = True

            fake_obj = model if model else request.form
            form = self.get_batch_edit_form(fake_obj, read_only)
            # we must validate batch edit as well
            if form.is_submitted():  # ON POST
                ret = self.update_objs(form, model_list)
                if ret:
                    if isinstance(ret, werkzeug.wrappers.BaseResponse) and ret.status_code == 302:
                        return ret
                    else:
                        return redirect(request.url)
            compound_form = self.get_compound_batch_edit_form(fake_obj, form)

            # ON GET
            hint_message = self.batch_edit_hint_message(preprocessed_objs, read_only)
            all_customized_actions = self._get_customized_actions(preprocessed_objs)
            help_message = self.get_edit_help(preprocessed_objs)
            actions = all_customized_actions
        grouper_info = {}
        model_columns = self._model_columns(model)
        for col in model_columns:
            grouper_2_cols = {}
            if isinstance(col, InputColumnSpec) and col.group_by and getattr(self.model,
                                                                             col.col_name).property.direction.name \
                    == "MANYTOONE":
                assert hasattr(col.group_by, "property") or hasattr(col.group_by, "__call__")
                rows = [row for row in col.filter_(self._session.query(getattr(self.model,
                                                                              col.col_name).property.mapper.class_))
                .all()
                        if col.opt_filter(row)]
                for row in rows:
                    # should use pk here
                    key = None
                    if hasattr(col.group_by, "property"):
                        key = getattr(row, col.group_by.property.key)
                        key = getattr(key, sa_utils.get_primary_key(col.group_by.mapper.class_))
                    elif hasattr(col.group_by, "__call__"):
                        key = col.group_by(row)
                    grouper_2_cols.setdefault(key, []).append(dict(id=row.id, text=unicode(row)))
                grouper_info[col.grouper_input_name] = grouper_2_cols
        create_url_map = {}
        if not read_only:  # 当前的form是只读，没有必要生成create_url_map
            for col in model_columns:
                if isinstance(col, InputColumnSpec) and not col.read_only:
                    continue
                col_name = col.col_name if isinstance(col, InputColumnSpec) or isinstance(col, FileColumnSpec) else col
                try:
                    attr = getattr(self.model, col_name)
                    if hasattr(attr.property, "direction"):
                        remote_side = attr.property.mapper.class_
                        create_url = self.data_browser.get_create_url(remote_side, col_name)
                        if create_url:
                            create_url_map[col_name] = create_url
                except AttributeError:
                    pass

        form = compound_form or form
        kwargs = {}
        form_kwargs = self._extra_params.get("form_view", {})
        for k, v in form_kwargs.items():
            if isinstance(v, types.FunctionType):
                v = v(self)
            kwargs[k] = v

        for f in form:
            if isinstance(f.widget, PlaceHolder):
                f.widget.set_args(**kwargs)

        form_columns = self.get_form_columns(preprocessed_obj) if len(id_list) == 1 else self.get_batch_form_columns(
            preprocessed_objs)
        fieldset_list = []
        if isinstance(form_columns, types.DictType):
            for fieldset, cols in form_columns.items():
                fieldset_list.append(
                    (fieldset, [form[col.col_name if isinstance(col, ColumnSpec) else col] for col in cols]))
        else:
            fieldset_list.append(("", form))

        resp = self.render(self.get_edit_template(),
                           obj=self.preprocess(model) if len(id_list) == 1 else None,
                           form=form,
                           fieldset_list=fieldset_list,
                           pre_url=pre_url,
                           next_url=next_url,
                           create_url_map=create_url_map,
                           grouper_info=grouper_info,
                           actions=actions,
                           return_url=return_url,
                           hint_message=hint_message,
                           help_message=help_message,
                           model_view=self,
                           __read_only__=read_only,
                           **kwargs)
        if form.is_submitted():
            # alas! something wrong
            resp = make_response(resp, 403)
            resp.headers["Warning"] = u"&".join([k + u"-" + u"; ".join(v) for k, v in form.errors.items()]).encode(
                "utf-8")
        return resp

    def get_create_help(self):
        return ""

    def get_edit_help(self, objs):
        return ""

    def get_list_help(self):
        return ""

    def scaffold_form(self, columns):
        """
            Create form from the model.
        """
        from flask.ext.databrowser.form.convert import AdminModelConverter, get_form

        converter = AdminModelConverter(self._session, self)
        form_class = get_form(self.model, converter,
                              base_class=form.BaseForm, only=columns,
                              exclude=None, field_args=None)
        return form_class

    def _model_columns(self, obj):
        """
        select the model columns from __form_columns__
        """
        form_columns = self.get_form_columns(obj)
        if not form_columns:
            # if no form columns given, use the model's attribute
            #mapper = self.model._sa_class_manager.mapper
            #form_columns = [p.key for p in mapper.iterate_properties]
            form_columns = self.backend.kolumnes

        if isinstance(form_columns, types.DictType):
            form_columns = list(itertools.chain(*form_columns.values()))
        ret = []
        model_clumns = set(
            [p.key for p in self.model.__mapper__.iterate_properties])
        for col in form_columns:
            if isinstance(col, InputColumnSpec):
                col_name = col.col_name
                # try_edit will override the field's read_only attribute
            elif isinstance(col, basestring) and (not '.' in col):
                col_name = col
            elif isinstance(col, FileColumnSpec):
                col_name = col.col_name
            else:
                continue
            if col_name in model_clumns:
                ret.append(col)
        return ret

    def get_create_form(self):
        create_columns = self._get_create_columns()
        if self.__create_form__ is None:
            if isinstance(create_columns, types.DictType):
                create_columns = list(itertools.chain(*create_columns.values()))
            self.__create_form__ = self.scaffold_form(create_columns)
            # if request specify some fields, then use these fields
        default_args = {}

        for k, v in request.args.iterlists():
            if hasattr(self.model, k):
                col = getattr(self.model, k)
                if hasattr(col.property, 'direction'): # relationship
                    q = col.property.mapper.class_.query
                    if col.property.direction.name == "MANYTOONE":
                        default_args[k] = q.get(v[0])
                    else:
                        default_args[k] = [q.get(i) for i in v]
                else:
                    default_args[k] = v[0]
        if default_args:
            for prop in self.model.__mapper__.iterate_properties:
                if prop.key not in default_args:
                    default_args[prop.key] = None
            obj = type("_temp", (object, ), default_args)()
            ret = self.__create_form__(obj=obj, **default_args)
            # set the default args in form, otherwise the last step of creation won't be finished
            for k, v in default_args.items():
                if v and hasattr(ret, k) and k not in request.form:
                    getattr(ret, k).data = v
            return ret
        return self.__create_form__()

    def get_create_compound_form(self, form, create_columns):

        if isinstance(create_columns, types.DictType):
            create_columns = list(itertools.chain(*create_columns.values()))

        ret = []
        value_converter = ValueConverter(None, self)
        for col in create_columns:
            if isinstance(col, InputColumnSpec):
                ret.append(form[col.col_name])
            elif isinstance(col, basestring):
                ret.append(form[col])
            elif isinstance(col, PlaceHolderColumnSpec) and col.as_input:
                field = value_converter(operator.attrgetter(col.col_name)(form._obj or self.model()), col)
                ret.append(field)
        return fake_form.FakeForm(form, ret)

    def get_edit_form(self, obj=None):
        if self.__edit_form__ is None:
            self.__edit_form__ = self.scaffold_form(self._model_columns(obj))
            # if request specify some fields, then we override fields with this value
        for k, v in request.args.items():
            if hasattr(self.model, k):
                col = getattr(self.model, k)
                if hasattr(col.property, 'direction'): # relationship
                    setattr(obj, k, col.property.mapper.class_.query.get(v))
                else:
                    setattr(obj, k, v)
        ret = self.__edit_form__(obj=obj)
        return ret

    def _get_fake_form_columns(self, form, form_columns, original_obj):
        processed_obj = self.preprocess(original_obj)
        value_converter = ValueConverter(processed_obj, self)

        ret = []
        if isinstance(form_columns, types.DictType):
            form_columns = list(itertools.chain(*form_columns.values()))
        for col in form_columns:
            if isinstance(col, InputColumnSpec) or isinstance(col, FileColumnSpec):
                ret.append(form[col.col_name])
            elif isinstance(col, basestring):
                try:
                # if it is a models property, we yield from model_form
                    ret.append(form[col])
                except KeyError:
                    col_spec = self._col_spec_from_str(col)
                    widget = value_converter(operator.attrgetter(col)(processed_obj),
                                             col_spec)
                    ret.append(widget)
            else:
                field = value_converter(operator.attrgetter(col.col_name)(processed_obj), col)
                # we force the field's name is the column's name (when the column is a
                # the relationship, field name may be the pk, see convert.py),
                # else, the form can't be grouped by fieldset, since we can't
                # figure out which field it is exactly. see function edit_view
                field.name = col.col_name
                ret.append(field)
        return ret

    def get_compound_batch_edit_form(self, obj, form):
        batchly_form_columns = self.get_batch_form_columns()
        if not batchly_form_columns:
            return fake_form.FakeForm(form, form._fields.values())
        ret = self._get_fake_form_columns(form, batchly_form_columns, obj)
        return fake_form.FakeForm(form, ret)

    def get_compound_edit_form(self, obj=None, form=None):
        if not form:
            form = self.get_edit_form(obj=obj)

        form_columns = self.get_form_columns(obj)
        if not form_columns:
            return form

        ret = self._get_fake_form_columns(form, form_columns, obj)
        return fake_form.FakeForm(form, ret)

    def get_batch_edit_form(self, fake_obj, read_only):
        if self.__batch_edit_form__ is None:
            batch_form_columns = self.get_batch_form_columns()
            if isinstance(batch_form_columns, types.DictType):
                batch_form_columns = list(itertools.chain(*batch_form_columns.values()))
            processed_cols = []
            for col in batch_form_columns:
                if isinstance(col, InputColumnSpec):
                    if col.col_name.find(".") == -1:
                        if read_only:
                            col.read_only = True
                        processed_cols.append(col)
                elif col.find(".") == -1:
                    if read_only:
                        processed_cols.append(InputColumnSpec(col, read_only=True))
                    else:
                        processed_cols.append(col)
            self.__batch_edit_form__ = self.scaffold_form(processed_cols)
        return self.__batch_edit_form__(obj=fake_obj)

    def _get_url(self, endpoint, **kwargs):
        if isinstance(self.blueprint, Flask):
            return url_for(endpoint, **kwargs)
        else:
            return url_for(".".join([self.blueprint.name, endpoint]), **kwargs)

    def url_for_list(self, **kwargs):
        return self._get_url(self.list_view_endpoint, **kwargs)

    def url_for_list_json(self, **kwargs):
        return self._get_url(self.list_view_endpoint+"_json", **kwargs)

    def url_for_object(self, model=None, **kwargs):
        if model:
            kwargs["id_"] = self.backend.get_pk_value(model)
        return self._get_url(self.object_view_endpoint, **kwargs)

    def list_view(self):
        """
        the view function of list of models
        """
        if request.method == "GET":
            self.try_view()
            page, order_by, desc = self._parse_args()
            column_filters = self.parse_filters()
            #TODO 通过配置template的css文件实现
            kwargs = {"__list_columns__": self.scaffold_list_columns(order_by, desc),
                      "__filters__": column_filters,
                      "__actions__": self.scaffold_actions()}

            #TODO 直接使用action对象
            kwargs["__action_2_forbidden_message_formats__"] = dict(
                (action["name"], action["forbidden_msg_formats"]) for action in
                kwargs["__actions__"])
            count, data = self.backend.get_list(order_by, desc, column_filters + self._get_default_list_filters(),
                                                (page - 1) * self.data_browser.page_size,
                                                self.data_browser.page_size)
            #TODO 重构：判断action是否可以执行
            kwargs["__rows_action_desc__"] = self.get_rows_action_desc(data)
            kwargs["__count__"] = count
            kwargs["__data__"] = self.scaffold_list(data)
            kwargs["__object_url__"] = self.url_for_object()
            kwargs["__order_by__"] = lambda col_name: col_name == order_by
            try:
                self.try_create()
                kwargs["__can_create__"] = True
            except PermissionDenied:
                kwargs["__can_create__"] = False
            kwargs["__max_col_len__"] = self.__max_col_len__
            kwargs["model_view"] = self
            if desc:
                kwargs["__desc__"] = desc
            kwargs["__pagination__"] = Pagination(None, page, self.data_browser.page_size, count, None)
            kwargs["help_message"] = self.get_list_help()
            for k, v in self._extra_params.get("list_view", {}).items():
                if isinstance(v, types.FunctionType):
                    v = v(self)
                kwargs[k] = v
            return self.render(self.list_template, **kwargs)
        else:  # POST
            action_name = request.form.get("__action__")

            models = self.backend.get_items(request.form.getlist('selected-ids'))

            for action in self._get_customized_actions():
                if action.name == action_name:
                    processed_objs = [self.preprocess(obj) for obj in models]
                    action.try_(processed_objs)
                    try:
                        ret = action.op_upon_list(processed_objs, self)
                        if isinstance(ret, werkzeug.wrappers.BaseResponse) and ret.status_code == 302:
                            if not action.direct:
                                flash(action.success_message(processed_objs), 'success')
                            return ret
                        self.backend.commit()
                        if not action.direct:
                            flash(action.success_message(processed_objs), 'success')
                    except Exception, ex:
                        self.backend.rollback()
                        raise
                    return redirect(request.url)
            else:
                raise ValidationError(
                    _('invalid action %(action)s', action=action_name))

    def list_api(self):

        if request.method == "GET":
            self.try_view()
            offset, limit, order_by, desc = self._parse_args2()
            column_filters = self.parse_filters()
            kwargs = {}
            kwargs["__filters__"] = column_filters
            kwargs["__actions__"] = self.scaffold_actions()
            count, data = self.query_data(order_by, desc, column_filters, offset, limit)
            data = self.scaffold_list(data)
            kwargs["__order_by__"] = lambda col_name: col_name == order_by

            def _get_forbidden_actions(obj):
                ret = []
                for action in self._get_customized_actions():
                    test_code = action.test_enabled(obj)
                    if test_code != 0:
                        ret.append((action.name, test_code))
                return ret

            def _action_to_dict(action):
                return {
                    "name": action.name,
                    "warn_msg": action.warn_msg,
                    "icon": action.data_icon,
                    "forbidden_message_formats": action.get_forbidden_msg_formats(),
                }

                # NOTE!!! direct action shouldn't be passed, they're meaningless to client
            actions = [_action_to_dict(action) for action in self._get_customized_actions() if not action.direct]

            can_create = False
            try:
                self.try_create()
                can_create = True
            except PermissionDenied:
                pass

            def _obj_to_dict(obj):
                ret = {"id": obj["pk"], "repr": obj["repr_"], "forbidden_actions": _get_forbidden_actions(obj["obj"])}
                for col in self.list_column_specs:
                    col_name = col if isinstance(col, basestring) else col.col_name
                    ret[col_name] = unicode(operator.attrgetter(col_name)(obj["obj"]))
                return ret

            return jsonify({
                "has_more": count > (offset or 0) + (limit or sys.maxint),
                "total_cnt": count,
                "data": [_obj_to_dict(obj) for obj in data],
                "actions": actions,
                "can_create": can_create,
                "can_batchly_edit": self.can_batchly_edit
            })

    def filters_api(self):
        ret = []
        self.try_view()
        column_filters = self.parse_filters()
        for filter_ in column_filters:
            default_value = filter_.default_value
            if default_value is not None and not isinstance(default_value, types.ListType) and not isinstance(
                    default_value, types.TupleType):
                default_value = [default_value]
            if filter_.options:
                ret.append({
                    "type": ["select"],
                    "hidden": filter_.hidden,
                    "name": filter_.op.id,
                    "label_extra": filter_.op.name,
                    "label": filter_.label,
                    "default_value": default_value,
                    "options": [(unicode(a), unicode(b)) for a, b in filter_.options],
                    "multiple": filter_.multiple,
                    "notation": filter_.__notation__,
                })
            else:
                ret.append({
                    "name": filter_.op.id,
                    "type": filter_.input_type,
                    "hidden": filter_.hidden,
                    "label_extra": filter_.op.name,
                    "label": filter_.label,
                    "default_value": [int(v) for v in default_value] if isinstance(filter_,
                                                                                   filters.Only) else default_value,
                    "notation": filter_.__notation__,
                })
        return jsonify({"filter_conditions": ret})

    def sort_columns_api(self):
        self.try_view()

        def calc_order(c):
            if self.default_order:
                return self.default_order[1] if c == self.default_order[0] else None
            return None

        return jsonify({"sort_columns": [(c, calc_order(c)) for c in self.sortable_columns]})

    def list_view_json(self):
        """
        this view return a page of items in json format
        """
        self.try_view()
        page, order_by, desc = self._parse_args()
        column_filters = self.parse_filters()
        count, data = self.query_data(order_by, desc, column_filters,
                                      (page - 1) * self.data_browser.page_size,
                                      self.data_browser.page_size)
        ret = {"total_count": count, "data": [],
               "has_next": page * self.data_browser.page_size < count}
        for idx, row in enumerate(self.scaffold_list(data)):
            obj_url = self.url_for_object(row["obj"], url=request.url,
                                          cdx=(
                                                  page - 1) * self.data_browser.page_size + idx + 1)
            ret["data"].append(dict(pk=row["pk"], repr_=row["repr_"],
                                    forbidden_actions=row["forbidden_actions"],
                                    obj_url=obj_url))
        return json.dumps(ret), 200, {'Content-Type': "application/json"}

    def obj_api(self, id_):
        """
        this api handles 2 things:

        * perform actions upon objects
        * get the object itself and edit form
            why we mix the object and edit form together? since whether a column could be altered (eg. not readonly),
            is related to the object
        * get some extra information from preprocessed object
        """
        if isinstance(id_, int):
            id_list = [id_]
        else:
            id_list = [i for i in id_.split(",") if i]

        processed_objs = [self.preprocess(self.get_one(id_)) for id_ in id_list]

        if len(id_list) == 1:
            obj = self.get_one(id_list[0])
            self.try_view([obj])  # first, we test if we could view
            preprocessed_obj = processed_objs[0]
            try:
                self.try_edit([preprocessed_obj])
                read_only = False
            except PermissionDenied:
                read_only = True
        else:
            objs = [self.get_one(id_) for id_ in id_list]
            preprocessed_objs = [self.preprocess(obj) for obj in objs]
            self.try_view(preprocessed_objs) # first, we test if we could view
            obj = None
            if request.method == "GET":
                obj = type("_temp", (object,), {})()
                for prop in self.model.__mapper__.iterate_properties:
                    attr = prop.key
                    default_value = getattr(objs[0], attr)
                    if all(getattr(obj_,
                                   attr) == default_value for obj_ in
                           objs):
                        setattr(obj, attr, default_value)
            try:
                self.try_edit(preprocessed_objs)
                read_only = False
            except PermissionDenied:
                read_only = True

        if request.method == "PUT":

            action_name = request.json.get("__action__")
            if action_name:
                for action in self._get_customized_actions(processed_objs):
                    if not action.direct and action.name == action_name:
                        action.try_(processed_objs)
                        for obj in processed_objs:
                            ret_code = action.test_enabled(obj)
                            if ret_code != 0:
                                return jsonify({
                                    "reason": _(u"can't apply %(action)s due to %(reason)s",
                                                action=action.name,
                                                reason=action.get_forbidden_msg_formats()[ret_code] % unicode(obj))
                                }), 403
                        try:
                            ret = action.op_upon_list(processed_objs, self)
                            self._session.commit()
                            return jsonify({"reason": action.success_message(processed_objs)})
                        except Exception, ex:
                            self._session.rollback()
                            return jsonify({
                                "reason": _('Failed to update %(model_name)s %(objs)s due to %(error)s',
                                            model_name=self._model_name,
                                            objs=",".join(unicode(obj) for obj in processed_objs),
                                            error=unicode(ex))
                            }), 403

                return jsonify({"reason": _('invalid action %(action)s', action=action_name)}), 403
        else: # GET

            form_columns = dict([(k, [c for c in v if isinstance(c, InputColumnSpec) or (
            isinstance(c, PlaceHolderColumnSpec) and c.as_input)])
                                 for k, v in self.form_columns.items()])

            def _not_pk(col_spec):
                if not hasattr(col_spec.property_, "direction"):
                    return not col_spec.property_.columns[0].primary_key
                return True

            def _make_readonly(col):
                col['read_only'] = read_only
                return col

            extra_fields = {}
            if len(id_list) == 1:
                extra_fields = dict([(k, v(preprocessed_obj)) for k, v in self.__extra_fields__.items()])
            return jsonify({
                "fieldsets": [(fieldset_name,
                               [_make_readonly(convert_column(col, get_dict_converter(), self, obj))
                                for col in col_specs if (not self.hidden_pk or _not_pk(col))])
                              for fieldset_name, col_specs in form_columns.items()],
                'extra_fields': extra_fields
            })

    def create_api(self):
        self.try_create()

        if request.method == "GET":
            def _not_pk(col_spec):
                if not hasattr(col_spec.property_, "direction"):
                    return not col_spec.property_.columns[0].primary_key
                return True

            return jsonify({
                "fieldsets": [(fieldset_name,
                               [convert_column(col, get_dict_converter(), self) for col in col_specs if
                                (not self.hidden_pk or _not_pk(col))])
                              for fieldset_name, col_specs in self._get_create_columns().items()]
            })
        else:
            columns = itertools.chain(*self._get_create_columns().values())
            columns = dict((col.col_name, col) for col in columns)
            formdata = MultiDict()
            create_form = self.get_create_form()
            if not create_form.validate():
                return jsonify({
                    "errors": create_form.errors
                }), 403
            obj = self.populate_obj(create_form)
            self.on_model_change(create_form, obj)
            self._session.add(obj)
            self._session.commit()
            return jsonify({
                'id': self.backend.get_pk_value(obj),
                'repr': self.repr_obj(obj)
            })

    def _parse_args(self):
        page = request.args.get("page", 1, type=int)
        order_by = request.args.get("order_by")
        desc = request.args.get("desc", 0, type=int)
        if order_by is None and isinstance(self.default_order, (list, tuple)):
            try:
                order_by, desc = self.default_order
                desc = 1 if desc == "desc" else 0
            except ValueError:
                order_by = self.default_order[0]
        return page, order_by, desc

    def _parse_args2(self):
        limit = request.args.get("__limit__", None, type=int)
        offset = request.args.get("__offset__", None, type=int)
        order_by = request.args.get("order_by")
        desc = request.args.get("desc", 0, type=int)
        if order_by is None and isinstance(self.default_order, (list, tuple)):
            try:
                order_by, desc = self.default_order
                if desc == "desc":
                    desc = 1
                else:
                    desc = 0
            except ValueError:
                order_by = self.default_order[0]
        return offset, limit, order_by, desc

    @property
    def sortable_columns(self):
        return [self.backend.primary_key] if self.backend.primary_key else []

    def scaffold_list_columns(self, order_by, desc):
        """
        collect columns displayed in table
        """
        def _(order_by, desc):
            for c in self.list_column_specs:
                if c.col_name in self.sortable_columns:
                    args = request.args.copy()
                    args["order_by"] = c.col_name
                    if order_by == c.col_name:  # the table is sorted by c, so revert the order
                        if not desc:
                            args["desc"] = 1
                        else:
                            try:
                                del args["desc"]
                            except KeyError:
                                pass
                    sort_url = self.url_for_list(**args)
                else:
                    sort_url = ""
                yield dict(name=c.col_name, label=c.label, doc=c.doc, sort_url=sort_url)

        return list(_(order_by=order_by, desc=desc))

    def scaffold_actions(self):
        return [dict(name=action.name, value=action.name, css_class=action.css_class, data_icon=action.data_icon,
                     forbidden_msg_formats=action.get_forbidden_msg_formats(), warn_msg=action.warn_msg,
                     direct=action.direct) for action in self._get_customized_actions()]

    def query_data(self, order_by, desc, filters, offset, limit):

        q = self.model.query
        joined_tables = []

        for filter_ in self.__list_filters__():
            if not filter_.model_view:
                filter_.model_view = self
            q = filter_.set_sa_criterion(q)
            for t in filter_.joined_tables:
                if t not in joined_tables:
                    joined_tables.append(t)

        for filter_ in filters:
            if filter_.has_value():
                q = filter_.set_sa_criterion(q)
                for t in filter_.joined_tables:
                    if t not in joined_tables:
                        joined_tables.append(t)

        if order_by:
            last_join_model = self.model
            order_by_list = order_by.split(".")
            for order_by in order_by_list[:-1]:
                last_join_model = getattr(last_join_model,
                                          order_by).property.mapper.class_
                if last_join_model not in joined_tables: # not joined before
                    joined_tables.append(last_join_model)
            order_criterion = getattr(last_join_model, order_by_list[-1])
            if hasattr(order_criterion.property, 'direction'):
                order_criterion = order_criterion.property.local_remote_pairs[0][0]
            if desc:
                order_criterion = order_criterion.desc()
            q = q.order_by(order_criterion)
        for t in joined_tables:
            q = q.join(t)
        count = q.count()
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)

        return count, q.all()

    def scaffold_list(self, objs):
        """
        convert the objects to a dict suitable for template renderation
        """

        def g():
            for idx, r in enumerate(objs):
                r = self.preprocess(r)
                converter = ValueConverter(r, self)
                pk = self.backend.get_pk_value(r)
                fields = []
                for c in self.list_column_specs:
                    raw_value = operator.attrgetter(c.col_name)(r)
                    formatted_value = converter(raw_value, c)
                    fields.append(formatted_value)

                yield dict(pk=pk, fields=fields,
                           css=self.patch_row_css(idx, r) or "",
                           attrs=self.patch_row_attr(idx, r),
                           repr_=self.repr_obj(r),
                           obj=r,
                           forbidden_actions=[action.name for action in
                                              self._get_customized_actions() if
                                              action.test_enabled(r) != 0])

        return [] if not objs else list(g())

    def patch_row_css(self, idx, row):
        return ""

    def repr_obj(self, obj):
        """
        this function decide how to represent an object in MOBILE LIST VIEW.
        override to provide your representation. HTML supported
        """
        return unicode(obj)

    def parse_filters(self):
        """
        set filter's value using args
        """
        shadow_column_filters = copy.copy(self._get_column_filters())
        #如果不用copy的话，会修改原来的filter

        op_id_2_filter = dict(
            (fltr.op.id, fltr) for fltr in shadow_column_filters)
        # initialize filter's value with default value
        for op_id, filter in op_id_2_filter.items():
            # clear original value
            filter.value = None
            if filter.default_value is not None:
                filter.value = filter.default_value
            if isinstance(filter, filters.Only) and request.args and not request.args.get(filter.col_name):
                filter.value = False
        for k, v in request.args.lists():
            try:
                op_id_2_filter[k].value = (v[0] if len(v) == 1 else v)
            except KeyError:
                pass
        return shadow_column_filters

    def get_edit_template(self):
        """
        get the real edit template, if you specify option "ModelView.edit_template", 
        it will be used, else "/__data_browser/form.html" will be used
        """
        if self.edit_template is None:
            import posixpath

            self.edit_template = posixpath.join(
                self.data_browser.blueprint.name, "form.html")
        return self.edit_template

    def get_list_columns(self):
        return self.__list_columns__

    def get_form_columns(self, obj=None):
        return self.__form_columns__

    def get_batch_form_columns(self, preprocessed_objs=None):
        return self.__batch_form_columns__

    def get_rows_action_desc(self, models):
        ret = {}
        customized_actions = self._get_customized_actions()
        if customized_actions:
            for model in models:
                id = self.backend.get_pk_value(model)
                preprocessed_model = self.preprocess(model)
                d = {"name": unicode(model), "actions": {}}
                for action in customized_actions:
                    error_code = action.test_enabled(preprocessed_model)
                    if error_code is not None:
                        d["actions"][action.name] = error_code
                ret[id] = d
        return ret

    def patch_row_attr(self, idx, row):
        """
        set html element attributes to each row in list table, take notice to
        attribute 'class', if 'patch_row_css' do return non-empty, it will override
        attribute 'class' returned from here
        """
        return ""

    def add_page_url_rule(self):
        assert self.blueprint
        self.blueprint.add_url_rule(self.list_view_url,
                                    self.list_view_endpoint,
                                    self.list_view,
                                    methods=["GET", "POST"])
        self.blueprint.add_url_rule(self.list_view_url + ".json",
                                    self.list_view_endpoint + "_json",
                                    self.list_view_json,
                                    methods=["GET"])
        self.blueprint.add_url_rule(self.object_view_url,
                                    self.object_view_endpoint,
                                    self.object_view,
                                    methods=["GET", "POST"])
        self.blueprint.add_url_rule(self.object_view_url + "/<id_>",
                                    self.object_view_endpoint,
                                    self.object_view,
                                    methods=["GET", "POST"])

    def add_api_url_rule(self):
        assert self.blueprint
        self.blueprint.add_url_rule(self.list_api_url,
                                    self.list_api_endpoint,
                                    self.list_api,
                                    methods=["GET", "POST"])
        self.blueprint.add_url_rule(self.filters_api_url,
                                    self.filters_api_endpoint,
                                    self.filters_api,
                                    methods=["GET"])
        self.blueprint.add_url_rule(self.sort_columns_api_url,
                                    self.sort_columns_api_endpoint,
                                    self.sort_columns_api,
                                    methods=["GET"])
        self.blueprint.add_url_rule(self.obj_api_url + "/<id_>",
                                    self.obj_api_endpoint,
                                    self.obj_api,
                                    methods=["GET", "PUT", "POST"])
        self.blueprint.add_url_rule(self.obj_api_url,
                                    self.create_api_endpoint,
                                    self.create_api,
                                    methods=["GET", "POST"])

    def _get_extra_params(self, view_name):
        kwargs = self._extra_params.get(view_name, {})
        for k, v in kwargs.items():
            if isinstance(v, types.FunctionType):
                kwargs[k] = v(self)
        return kwargs

    @property
    def _model_name(self):
        return self.backend.model_name

    @property
    def _extra_params(self):
        #TODO 不需要是方法
        if isinstance(self.extra_params, types.FunctionType):
            return self.extra_params()
        elif isinstance(self.extra_params, types.DictType):
            return self.extra_params
        else:
            return {}