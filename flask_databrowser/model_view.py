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
import os.path

import werkzeug
from werkzeug.utils import secure_filename
from flask import (render_template, flash, request, url_for, redirect, Flask,
                   make_response, jsonify, abort)
from flask.ext.babel import _
from flask.ext.principal import PermissionDenied, Permission
from flask.ext.sqlalchemy import Pagination
from flask_upload2.fields import FileField

from flask.ext.databrowser import filters, extra_fields
from flask.ext.databrowser.col_spec import (ColSpec, InputColSpec,
                                            input_col_spec_from_kolumne)
from flask.ext.databrowser.action import ACTION_OK
from flask.ext.databrowser.exceptions import ValidationError
from flask.ext.databrowser.form import BaseForm
from flask.ext.databrowser.constants import (WEB_SERVICE, WEB_PAGE,
                                             BACK_URL_PARAM)
from .stuffed_field import StuffedField


class ModelView(object):
    """
    changelog v2: remove params: __create_columns__, __sortable_columns__

    现确立如下规则：
    没有"_"开头的属性（包括property）可以重写
    以"_"开头的属性，理论上不应该重写
    """

    # 可以重写的属性
    column_formatters = {}
    __customized_actions__ = []
    __max_col_len__ = 255
    __extra_fields__ = {}

    serv_type = WEB_PAGE | WEB_SERVICE

    language = "en"
    #TODO should rename to hide_backrefs
    column_hide_backrefs = True
    list_template = "data_browser__/list.html"
    create_template = edit_template = "data_browser__/form.html"

    hidden_pk = True
    create_in_steps = False
    step_create_templates = []

    class __metaclass__(type):
        def __init__(cls, name, bases, nmspc):
            type.__init__(cls, name, bases, nmspc)
            if getattr(cls.list_columns.fget, '__fdb_cached__', False):
                cls._list_col_specs = werkzeug.cached_property(
                    cls._list_col_specs.fget)
            if getattr(cls.edit_columns.fget, '__fdb_cached__', False):
                cls._edit_col_specs = werkzeug.cached_property(
                    cls._edit_col_specs.fget)
            if getattr(cls.create_columns.fget, '__fdb_cached__', False):
                cls._create_col_specs = werkzeug.cached_property(
                    cls._create_col_specs.fget)

    @classmethod
    def cached(cls, p):
        p.fget.__fdb_cached__ = True
        return p

    def __init__(self, modell, page_size=16, permission_required=True):
        self.modell = modell
        self.blueprint = None
        self.extra_params = {}
        self.data_browser = None
        self._batch_edit_col_specs = []
        self._create_form = self._edit_form = \
            self._batch_edit_form = None
        self.page_size = page_size
        self.permission_required = permission_required

        self.create_need = (_('create'), self.modell.label)
        self.edit_need = lambda id_: (_('edit'), self.modell.label, id_)
        self.edit_all_need = (_('edit'), _('all'), self.modell.label)
        self.view_all_need = (_('view'), _('all'), self.modell.label)
        self.view_need = lambda id_: (_('view'), self.modell.label, id_)
        self.remove_need = lambda id_: (_('remove'), self.modell.label, id_)
        self.remove_all_need = (_('remove'), _('all'), self.modell.label)

    @property
    def can_batchly_edit(self):
        return False

    @property
    def list_columns(self):
        return [col.name for col in self.modell.columns]

    @property
    def create_columns(self):
        """
        get the create columns. override this method to provide columns you
        want to insert into create form. accepted column types are:

            * basestring - name of the column
            * InputColumnSpec
        besides, all columns could be grouped in field sets, so the return
        value could be an OrderedDict

        note!!! don't put primary key here if only you mean to

        :return: a list of kolumnes returned by modell, or an OrderedDict
        """
        return [input_col_spec_from_kolumne(k) for k in
                self.modell.kolumnes if not k.is_primary_key()]

    @property
    def edit_columns(self):
        """
        get the edit columns. override this method to provide columns you
        want to insert into create form. accepted column types are:

            * basestring - name of the column
            * InputColumnSpec
        besides, all columns could be grouped in field sets, so the return
        value could be an OrderedDict

        note!!! don't put primary key here if only you mean to

        :return: a list of kolumnes returned by modell, or an OrderedDict
        """
        return [input_col_spec_from_kolumne(k) for k in
                self.modell.kolumnes if not k.is_primary_key()]

    @property
    def batch_edit_columns(self):
        """
        get the batch edit columns. override this method to provide columns you
        want to insert into create form. accepted column types are:

            * basestring - name of the column
            * InputColumnSpec
        besides, all columns could be grouped in field sets, so the return
        value could be an OrderedDict

        note!!! don't put primary key here if only you mean to

        :return: a list of kolumnes returned by modell, or an OrderedDict
        """
        return [input_col_spec_from_kolumne(k) for k in
                self.modell.kolumnes if not k.is_primary_key()]

    @property
    def sortable_columns(self):
        return [self.modell.primary_key] if self.modell.primary_key else []

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
                            self.modell.name).lstrip("-")

    @property
    def object_view_endpoint(self):
        return re.sub(r"([A-Z]+)", lambda m: "_" + m.groups()[0].lower(),
                      self.modell.name).lstrip("_")

    def before_request_hook(self):
        pass

    def after_request_hook(self, response):
        return response

    def within_domain(self, url, bp_name):
        url = url.lower()
        path_ = urlparse.urlparse(url).path
        segs = path_.split("/")[1:]
        if len(segs) < 2:
            return False
        if segs[0] != bp_name.lower():
            return False
        return any("/" + seg in {self.object_view_url, self.list_view_url}
                   for seg in segs[1:])

    @property
    def filters(self):
        return []

    @property
    def default_order(self):
        return (self.modell.primary_key, 'desc')

    @property
    def default_filters(self):
        return []

    def expand_model(self, obj):
        '''
        this function is very important if you want your model not just
        include underlying modell's fields
        '''
        return obj

    def do_update_log(self, obj, action):
        from flask.ext.login import current_user

        def _log(obj_):
            self.data_browser.logger.debug(
                _("%(user)s performed %(action)s", user=unicode(current_user),
                  action=action),
                extra={"obj": obj_, "obj_pk": self.modell.get_pk_value(obj_),
                       "action": action, "actor": current_user})

        if isinstance(obj, list) or isinstance(obj, tuple):
            for obj_ in obj:
                _log(obj_)
        else:
            _log(obj)

    def do_create_log(self, obj):
        from flask.ext.login import current_user

        self.data_browser.logger.debug(
            _('%(model_label)s %(model)s was created successfully',
              model_label=self.modell.label, model=unicode(obj)),
            extra={"obj": obj, "obj_pk": self.modell.get_pk_value(obj),
                   "action": _(u"create"), "actor": current_user})

    def batch_edit_hint_message(self, objs, read_only=False):
        if read_only:
            return _(
                u"you are viewing %(model_label)s-[%(obj)s], "
                u"since you have only read permission",
                model_label=self.modell.label,
                obj=",".join(unicode(model) for model in objs))
        else:
            return _(u"edit %(model_label)s-[%(objs)s]",
                     model_label=self.modell.label,
                     objs=",".join(unicode(model) for model in objs))

    def edit_hint_message(self, obj, read_only=False):
        if read_only:
            return _(
                u"you are viewing %(model_label)s-[%(obj)s], "
                u"since you have only read permission",
                model_label=self.modell.label, obj=unicode(obj))
        else:
            return _(u"edit %(model_label)s-[%(obj)s]",
                     model_label=self.modell.label,
                     obj=unicode(obj))

    @property
    def create_hint_message(self):
        return _(u"create %(model_label)s", model_label=self.modell.label)

    def edit_view(self, id_):
        """
            Edit model view
        """
        if isinstance(id_, int):
            id_list = [id_]
        else:
            id_list = [i for i in id_.split(",") if i]

        return_url = request.args.get(BACK_URL_PARAM) or \
            url_for('.' + self.list_view_endpoint)

        if id_list is None:
            return redirect(return_url)

        in_batch_mode = len(id_list) > 1
        if not in_batch_mode:
            record = self._get_one(id_list[0])
            self.try_view([record])  # first, we test if we could view
            preprocessed_record = self.expand_model(record)
            try:
                self.try_edit([preprocessed_record])
                readonly = False
            except PermissionDenied:
                readonly = True
            form = self._compose_edit_form(record, readonly)
            if form.validate_on_submit():  # ON POST
                ret = self._update_objs(form, [record])
                if ret:
                    if isinstance(ret, werkzeug.wrappers.BaseResponse) and \
                       ret.status_code == 302:
                        return ret
                    else:
                        url_parts = list(urlparse.urlparse(request.url))
                        queries = url_parts[4].split('&')
                        queries = '&'.join(q for q in queries if not
                                           q.startswith(BACK_URL_PARAM))
                        url = urlparse.urlunparse(url_parts)
                        return redirect(url)
            hint_message = self.edit_hint_message(preprocessed_record,
                                                  readonly)
            all_customized_actions = self._compose_actions(
                [preprocessed_record])
            help_message = self.get_edit_help(preprocessed_record)
            actions = all_customized_actions
        else:
            records = [self._get_one(_id_) for _id_ in id_list]
            preprocessed_records = [self.expand_model(record) for record in
                                    records]
            self.try_view(preprocessed_records)
            try:
                self.try_edit(preprocessed_records)
                readonly = False
            except PermissionDenied:
                readonly = True
            form = self._compose_batch_edit_form(records, readonly)
            # we must validate batch edit as well
            if form.is_submitted():  # ON POST
                ret = self._update_objs(form, records)
                if ret:
                    if isinstance(ret, werkzeug.wrappers.BaseResponse) and \
                       ret.status_code == 302:
                        return ret
                    else:
                        return redirect(request.url)
                # ON GET
            hint_message = self.batch_edit_hint_message(preprocessed_records,
                                                        readonly)
            all_customized_actions = \
                self._compose_actions(preprocessed_records)
            help_message = self.get_edit_help(preprocessed_records)
            actions = all_customized_actions
        grouper_info = {}
        model_columns = self._edit_col_specs

        for col in model_columns:
            grouper_2_cols = {}
            #TODO why many to one?
            if isinstance(col, InputColSpec) and col.group_by and \
               col.kolumne.direction == "MANYTOONE":
                rows = [row for row in
                        col.filter_(col.kolumne.remote_side.query) if
                        col.opt_filter(row)]
                for row in rows:
                    key = col.group_by.group(row)
                    grouper_2_cols.setdefault(key, []).append(
                        dict(id=row.id, text=unicode(row)))
                grouper_info[col.grouper_input_name] = grouper_2_cols

        #form = compound_form or form
        kwargs = self._get_extra_params("form_view")

        resp = self._render(self._get_edit_template(),
                            form=form,
                            grouper_info=grouper_info,
                            actions=actions,
                            return_url=return_url,
                            hint_message=hint_message,
                            help_message=help_message,
                            model_view=self,
                            __read_only__=readonly,
                            in_batch_mode=in_batch_mode,
                            **kwargs)
        if form.is_submitted():
            # alas! something wrong
            resp = make_response(resp, 403)
            resp.headers["Warning"] = self._compose_warn_msg(form)
        return resp

    @property
    def create_help(self):
        return ""

    def get_edit_help(self, objs):
        return ""

    def get_list_help(self):
        return ""

    def try_view(self, processed_objs=None):
        """
        control if user could view objects list or object
        NOTE!!! don't return anything, if you determine that something
        should't be viewed, throw PermissionDenied

        :param objs: the objs to be viewed, is None, we are in list view
        """
        # note!!! we consider edit permission is stronger than view permission
        if self.permission_required:
            if processed_objs:
                if not Permission(self.edit_all_need).can():
                    if not Permission(self.view_all_need).can():
                        for o in processed_objs:
                            pk = self.modell.get_pk_value(o)
                            if not Permission(self.edit_need(pk)).can():
                                Permission(self.view_need(pk)).test()
            else:
                if not Permission(self.edit_all_need).can():
                    Permission(self.view_all_need).test()

    def try_create(self):
        """
        control if user could create the new object
        """
        if self.permission_required:
            Permission(self.create_need).test()

    def try_edit(self, processed_objs=None):
        if self.permission_required:
            if processed_objs:
                if not Permission(self.edit_all_need).can():
                    for o in processed_objs:
                        pk = self.modell.get_pk_value(o)
                        Permission(self.edit_need(pk)).test()

    def create_view(self):
        self.try_create()

        return_url = request.args.get(BACK_URL_PARAM,
                                      url_for('.' + self.list_view_endpoint))
        on_fly = int(request.args.get("on_fly", 0))
        current_step = int(request.args.get('__step__', 0)) if \
            self.create_in_steps else None

        form = self._compose_create_form(current_step)
        if form.validate_on_submit():
            model = self._create_model(form)
            if model:
                self.do_create_log(model)
                flash(_(u'%(model_label)s %(model)s was created successfully',
                        model_label=self.modell.label, model=unicode(model)))
                if request.form.get("__builtin_action__") == _("add another"):
                    return redirect(self.url_for_object(**{
                        BACK_URL_PARAM: return_url}))
                else:
                    if on_fly:
                        return render_template(
                            "data_browser__/on_fly_result.html",
                            model_cls=self.modell.name,
                            obj=unicode(model),
                            obj_pk=self.modell.get_pk_value(model),
                            target=request.args.get("target"))
                    else:
                        return redirect(return_url)

        kwargs = self._get_extra_params("create_view")
        if self.create_in_steps:
            create_template = self._get_step_create_template(current_step)
            kwargs["last_step"], kwargs["next_step"] = \
                self._get_around_steps(current_step)
        else:
            create_template = self.create_template

        resp = self._render(create_template, form=form, return_url=return_url,
                            help_message=self.create_help,
                            hint_message=self.create_hint_message,
                            **kwargs)

        if form.is_submitted():
            # alas! something wrong
            resp = make_response(resp, 403)
            resp.headers["Warning"] = self._compose_warn_msg(form)
        return resp

    def get_create_form(self):
        create_columns = self._compose_create_col_specs()
        if self._create_form is None:
            if isinstance(create_columns, types.DictType):
                create_columns = list(itertools.chain(
                    *create_columns.values()))
            self._create_form = self._scaffold_form(create_columns)
            # if request specify some fields, then use these fields
        default_args = {}

        for k, v in request.args.iterlists():
            if hasattr(self.model, k):
                col = getattr(self.model, k)
                if hasattr(col.property, 'direction'):  # relationship
                    q = col.property.mapper.class_.query
                    if col.property.direction.name == "MANYTOONE":
                        default_args[k] = q.get(v[0])
                    else:
                        default_args[k] = [q.get(i) for i in v]
                else:
                    default_args[k] = v[0]
        if default_args:
            for prop in self.modell.kolumnes:
                if prop.key not in default_args:
                    default_args[prop.key] = None
            obj = type("_temp", (object, ), default_args)()
            ret = self._create_form(obj=obj, **default_args)
            # set the default args in form, otherwise the last step of
            # creation won't be finished
            for k, v in default_args.items():
                if v and hasattr(ret, k) and k not in request.form:
                    getattr(ret, k).data = v
            return ret
        return self._create_form()

    def url_for_list(self, **kwargs):
        return self._get_url(self.list_view_endpoint, **kwargs)

    def url_for_list_json(self, **kwargs):
        return self._get_url(self.list_view_endpoint + "_json", **kwargs)

    def url_for_object(self, obj=None, **kwargs):
        if obj:
            kwargs["id_"] = self.modell.get_pk_value(obj)
        return self._get_url(self.object_view_endpoint, **kwargs)

    def list_view(self):
        """
        the view function of list of models
        """
        if request.method == "GET":
            self.try_view()
            page, order_by, desc = self._parse_args()
            column_filters = self._parse_filters()
            #TODO 通过配置template的css文件实现
            kwargs = {
                "__list_columns__": self._scaffold_list_columns(order_by,
                                                                desc),
                "__filters__": column_filters,
                "__actions__": self.scaffold_actions()
            }

            #TODO 直接使用action对象
            kwargs["__action_2_forbidden_message_formats__"] = dict(
                (action["name"], action["forbidden_msg_formats"]) for action in
                kwargs["__actions__"])
            filters_ = column_filters + self.default_filters
            count, data = self.modell.get_list(order_by, desc, filters_,
                                               (page - 1) * self.page_size,
                                               self.page_size)
            #TODO 重构：判断action是否可以执行
            kwargs["__rows_action_desc__"] = \
                self._compose_rows_action_desc(data)
            kwargs["__count__"] = count
            kwargs["__data__"] = self._scaffold_list(data)
            kwargs["__object_url__"] = self.url_for_object()
            kwargs["__order_by__"] = lambda col_name: \
                    self._sortable_column_map[col_name] == order_by
            try:
                self.try_create()
                kwargs["__can_create__"] = True
            except PermissionDenied:
                kwargs["__can_create__"] = False
            kwargs["__max_col_len__"] = self.__max_col_len__
            kwargs["model_view"] = self
            if desc:
                kwargs["__desc__"] = desc
            kwargs["__pagination__"] = Pagination(None, page, self.page_size,
                                                  count, None)
            kwargs["help_message"] = self.get_list_help()
            kwargs.update(self._get_extra_params('list_view'))
            return self._render(self.list_template, **kwargs)
        else:  # POST
            action_name = request.form.get("__action__")
            models = self.modell.get_items(
                request.form.getlist('selected-ids'))
            processed_objs = [self.expand_model(obj) for obj in models]
            for action in self._compose_actions(processed_objs):
                if action.name == action_name and \
                   action.test(*processed_objs) == ACTION_OK:
                    try:
                        ret = action.op_upon_list(processed_objs, self)
                        if isinstance(ret, tuple):
                            flash(ret[-1], "error")
                            return redirect(request.url)
                        if not action.readonly:
                            self.modell.commit()
                        if isinstance(ret, werkzeug.wrappers.BaseResponse) \
                           and ret.status_code == 302:
                            if not action.readonly:
                                flash(action.success_message(processed_objs),
                                      'success')
                            return ret
                    except Exception:
                        self.modell.rollback()
                        raise
                    return redirect(request.url)
            else:
                raise ValidationError(
                    _('invalid action %(action)s', action=action_name))

    def list_api(self):

        if request.method == "GET":
            self.try_view()
            offset, limit, order_by, desc = self._parse_args2()
            column_filters = self._parse_filters()
            kwargs = {}
            kwargs["__filters__"] = column_filters
            kwargs["__actions__"] = self.scaffold_actions()
            count, data = self.query_data(order_by, desc, column_filters,
                                          offset, limit)
            data = self._scaffold_list(data)
            kwargs["__order_by__"] = lambda col_name: col_name == order_by

            def _get_forbidden_actions(obj):
                ret = []
                for action in self._compose_actions():
                    test_code = action.test(obj)
                    if test_code != 0:
                        ret.append((action.name, test_code))
                return ret

            def _action_to_dict(action):
                return {
                    "name": action.name,
                    "warn_msg": action.warn_msg,
                    "icon": action.data_icon,
                    "forbidden_message_formats": action.forbidden_msg_formats,
                }

            # NOTE!!! direct action shouldn't be passed, they're
            # meaningless to client
            actions = [_action_to_dict(action) for action in
                       self._compose_actions() if not action.readonly]

            can_create = False
            try:
                self.try_create()
                can_create = True
            except PermissionDenied:
                pass

            def _obj_to_dict(obj):
                ret = {"id": obj["pk"], "repr": obj["repr_"],
                       "forbidden_actions": _get_forbidden_actions(obj["obj"])}
                for col in self._list_col_specs:
                    col_name = col if isinstance(col, basestring) else \
                        col.col_name
                    ret[col_name] = unicode(
                        operator.attrgetter(col_name)(obj["obj"]))
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
        column_filters = self._parse_filters()
        for filter_ in column_filters:
            default_value = filter_.default_value
            if default_value is not None and \
                    not isinstance(default_value, types.ListType) and \
                    not isinstance(default_value, types.TupleType):
                default_value = [default_value]
            if filter_.options:
                ret.append({
                    "type": ["select"],
                    "hidden": filter_.hidden,
                    "name": filter_.op.id,
                    "label_extra": filter_.op.name,
                    "label": filter_.label,
                    "default_value": default_value,
                    "options": [(unicode(a), unicode(b)) for a, b in
                                filter_.options],
                    "multiple": filter_.multiple,
                    "notation": filter_.__notation__,
                })
            else:
                default_value = [int(v) for v in default_value] if \
                    isinstance(filter_, filters.Only) else default_value
                ret.append({
                    "name": filter_.op.id,
                    "type": filter_.input_type,
                    "hidden": filter_.hidden,
                    "label_extra": filter_.op.name,
                    "label": filter_.label,
                    "default_value": default_value,
                    "notation": filter_.__notation__,
                })
        return jsonify({"filter_conditions": ret})

    def sort_columns_api(self):
        self.try_view()

        def calc_order(c):
            if self.default_order and c == self.default_order[0]:
                return self.default_order[1]
            return None

        return jsonify({
            "sort_columns": [(c, calc_order(c)) for c in self.sortable_columns]
        })

    def list_view_json(self):
        """
        this view return a page of items in json format
        """
        self.try_view()
        page, order_by, desc = self._parse_args()
        column_filters = self._parse_filters()
        count, data = self.query_data(order_by, desc, column_filters,
                                      (page - 1) * self.page_size,
                                      self.page_size)
        ret = {"total_count": count, "data": [],
               "has_next": page * self.page_size < count}
        for idx, row in enumerate(self._scaffold_list(data)):
            cdx = (page - 1) * self.page_size + idx + 1
            obj_url = self.url_for_object(row["obj"],
                                          **{BACK_URL_PARAM: request.url,
                                             cdx: cdx})
            ret["data"].append(dict(pk=row["pk"], repr_=row["repr_"],
                                    forbidden_actions=row["forbidden_actions"],
                                    obj_url=obj_url))
        return json.dumps(ret), 200, {'Content-Type': "application/json"}

    def scaffold_actions(self):
        return [dict(name=action.name, value=action.name,
                     css_class=action.css_class, data_icon=action.data_icon,
                     forbidden_msg_formats=action.forbidden_msg_formats,
                     warn_msg=action.warn_msg,
                     direct=action.readonly)
                for action in self._compose_actions()]

    def query_data(self, order_by, desc, filters, offset, limit):

        q = self.modell.query
        joined_tables = []

        for filter_ in self.default_filters:
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
                if last_join_model not in joined_tables:  # not joined before
                    joined_tables.append(last_join_model)
            order_criterion = getattr(last_join_model, order_by_list[-1])
            if hasattr(order_criterion.property, 'direction'):
                order_criterion = \
                    order_criterion.property.local_remote_pairs[0][0]
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

    def patch_row_css(self, idx, row):
        return ""

    def repr_obj(self, obj):
        """
        this function decide how to represent an object in MOBILE LIST VIEW.
        override to provide your representation. HTML supported
        """
        return unicode(obj)

    def patch_row_attr(self, idx, row):
        """
        set html element attributes to each row in list table, take notice to
        attribute 'class', if 'patch_row_css' do return non-empty, it will
        override attribute 'class' returned from here
        """
        return ""

    def add_page_url_rule(self):
        # TODO just compute each url and endpoint
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

    #def add_api_url_rule(self):
    #    assert self.blueprint
    #    self.blueprint.add_url_rule(self.list_api_url,
    #                                self.list_api_endpoint,
    #                                self.list_api,
    #                                methods=["GET", "POST"])
    #    self.blueprint.add_url_rule(self.filters_api_url,
    #                                self.filters_api_endpoint,
    #                                self.filters_api,
    #                                methods=["GET"])
    #    self.blueprint.add_url_rule(self.sort_columns_api_url,
    #                                self.sort_columns_api_endpoint,
    #                                self.sort_columns_api,
    #                                methods=["GET"])
    #    self.blueprint.add_url_rule(self.obj_api_url + "/<id_>",
    #                                self.obj_api_endpoint,
    #                                self.obj_api,
    #                                methods=["GET", "PUT", "POST"])
    #    self.blueprint.add_url_rule(self.obj_api_url,
    #                                self.create_api_endpoint,
    #                                self.create_api,
    #                                methods=["GET", "POST"])

    def grant_all(self, identity):
        identity.provides.add(self.create_need)
        identity.provides.add(self.view_all_need)
        identity.provides.add(self.edit_all_need)
        identity.provides.add(self.remove_all_need)

    def grant_create(self, identity):
        identity.provides.add(self.create_need)

    def grant_remove(self, identity, pk=None):
        if pk is None:
            identity.provides.add(self.remove_all_need)
        else:
            identity.provides.add(self.remove_need(pk))

    def grant_edit(self, identity, pk=None):
        if pk is None:
            need = self.edit_all_need
        else:
            need = self.edit_need(pk)
        identity.provides.add(need)

    def grant_view(self, identity, pk=None):
        if pk is None:
            need = self.view_all_need
        else:
            need = self.view_need(pk)
        identity.provides.add(need)

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

    def _compose_edit_form(self, record, readonly):
        # TODO  reserve order
        edit_col_specs = self._edit_col_specs
        assert isinstance(edit_col_specs, dict)
        if self._edit_form is None:
            col_specs = []
            uneditable_col_specs = []
            for c in itertools.chain(*edit_col_specs.values()):
                if c.as_input:  # some info columnes won't be put here
                    if c.disabled or readonly:
                        uneditable_col_specs.append(c)
                    else:
                        col_specs.append(c)
                # why split into 2 forms, since only _edit_form will be
                # validated and populated
            self._edit_form = self._scaffold_form(col_specs)
            self._uneditable_form = self._scaffold_form(uneditable_col_specs)
            # if request specify some fields, then we override fields with this
        # value
        for k, v in request.args.items():
            if self.modell.has_kolumne(k):
                kol = self.modell.get_kolumne(k)
                if kol.is_relationship():  # relationship
                    setattr(record, k, kol.remote_side.query.get(v))
                else:
                    setattr(record, k, v)
        ret = self._edit_form(obj=record)
        if hasattr(self, '_uneditable_form'):
            uneditable_bound_form = self._uneditable_form(obj=record)
        else:
            uneditable_bound_form = {}
        record = self.expand_model(record)
        # compose bound_field sets, note! bound_field sets are our stuffs
        # other than
        # the standard wtforms.Form, they are ONLY use to generate form
        # in html page
        # actually, there're 2 forms, one for generate html, one for handle
        # data
        ret.fieldsets = OrderedDict()
        focus_set = False
        # only stuff bound fields take effects
        for fs_name, fs_col_specs in edit_col_specs.items():
            for col_spec in fs_col_specs:
                if col_spec.as_input:
                    try:
                        bound_field = ret[col_spec.col_name]
                    except KeyError:
                        bound_field = uneditable_bound_form[col_spec.col_name]
                    bound_field, focus_set = \
                        self._composed_stuffed_field(record,
                                                     bound_field,
                                                     col_spec, focus_set)
                    if readonly:
                        bound_field.__read_only__ = True
                else:  # info fields
                    bound_field = self._compose_pseudo_field(ret, record,
                                                             col_spec)
                ret.fieldsets.setdefault(fs_name, []).append(bound_field)
        return ret

    def _compose_pseudo_field(self, form, record, col_spec):
        value = operator.attrgetter(col_spec.col_name)(record)
        field = col_spec.make_field(record, self)
        bound_field = field.bind(form, col_spec.col_name)
        bound_field.process_data(value)
        if hasattr(col_spec, 'override_widget'):
            bound_field.widget = col_spec.override_widget(record)
        return bound_field

    def _compose_batch_edit_form(self, records, readonly):
        batch_edit_col_specs = self._compose_batch_edit_col_specs()
        assert isinstance(batch_edit_col_specs, dict)
        if self._batch_edit_form is None:
            self._batch_edit_form = self._scaffold_form(
                itertools.chain(*batch_edit_col_specs.values()))
        fake_obj = None
        if request.method == "GET":
            fake_obj = type("_temp", (object,), {})()
            for prop in self.modell.properties:
                attr = prop.key
                pivot_value = getattr(records[0], attr)
                if all(getattr(record, attr) == pivot_value for record in
                       records):
                    setattr(fake_obj, attr, pivot_value)
        if fake_obj is None:
            fake_obj = request.form
        ret = self._batch_edit_form(obj=fake_obj)
        # compose bound_field sets, note! bound_field sets are our stuffs
        # other than
        # the standard wtforms.Form, they are ONLY use to generate form
        # in html page
        ret.fieldsets = OrderedDict()
        focus_set = False
        # only stuff bound fields take effects
        for fs_name, fs_col_specs in batch_edit_col_specs.items():
            for col_spec in fs_col_specs:
                bound_field, focus_set = \
                    self._composed_stuffed_field(fake_obj,
                                                 ret[col_spec.col_name],
                                                 col_spec, focus_set)
                if readonly:
                    bound_field.__read_only__ = True
                ret.fieldsets.setdefault(fs_name, []).append(bound_field)
        return ret

    def _compose_create_col_specs(self, current_step=None):
        """
        get all the *NORMALIZED* create column specs for model view.
        """
        if current_step is None:
            return self._create_col_specs
        else:
            return dict([self._create_col_specs.items()
                         [current_step]])

    @property
    def _create_col_specs(self):
        return self._compose_normalized_col_specs(self.create_columns)

    @property
    def _config(self):
        return self.data_browser.app.config

    def _get_step_create_template(self, step):
        try:
            return self.step_create_templates[step] or \
                'data_browser__/form.html'
        except IndexError:
            return 'data_browser__/form.html'

    def _compose_normalized_col_specs(self, columns):
        """
        this utility function handle the following matters:
            * if columns not defined in fieldsets, add them to one fieldset
                whose name is empty string
            * convert all the column of 'basestring' to InputColumn
            * fill the label and doc of each column
            * if the column is not defined in modell, wipe it
        :return: OrderedDict, the keys are fieldset's name,
        whose values are a list InputColumnSpec (as input).
        """
        normalized_col_specs = OrderedDict()

        if isinstance(columns, types.DictType):
            fieldsets = columns
        else:
            fieldsets = {"": columns}

        for fieldset_name, columns in fieldsets.items():
            for col in columns:
                is_str = isinstance(col, basestring)
                is_input = isinstance(col, ColSpec) and col.as_input
                col_name = col if is_str else col.col_name
                # if the user said the column should be an input, then it will
                # be, only it may not infer column definition from underlying
                # modell
                if (is_str and self.modell.has_kolumne(col_name)) or is_input:
                    kol = self.modell.get_kolumne(col_name)
                    if kol:
                        if is_str:
                            col_spec = input_col_spec_from_kolumne(kol)
                        else:
                            col_spec = col
                            col_spec.kolumne = kol
                        if col_spec.doc is None:
                            col_spec.doc = self.modell.get_column_doc(col_name)
                        col_spec.data_browser = self.data_browser
                        normalized_col_specs.setdefault(fieldset_name,
                                                        []).append(col_spec)
                    else:
                        col.data_browser = self.data_browser
                        normalized_col_specs.setdefault(fieldset_name,
                                                        []).append(col)
                else:
                    col_spec = col
                    if isinstance(col, basestring):
                        col_spec = self._col_spec_from_str(col)
                    normalized_col_specs.setdefault(fieldset_name, []).append(
                        col_spec)
        return normalized_col_specs

    @property
    def _list_col_specs(self):
        list_col_specs = []
        for col in self.list_columns:
            if isinstance(col, basestring):
                col_spec = self._col_spec_from_str(col)
            else:
                col_spec = col
                if col_spec.doc is None:
                    col_spec.doc = self.modell.get_column_doc(
                        col_spec.col_name)
            list_col_specs.append(col_spec)
        return list_col_specs

    def _render(self, template, **kwargs):
        return render_template(template, **kwargs)

    def _get_one(self, id_):
        return self.modell.query.get(id_) or abort(404)

    def _col_spec_from_str(self, col):
        """
        get column specification from string
        """
        return ColSpec(col, doc=self.modell.get_column_doc(col))

    def _create_model(self, form):
        """
            Create obj from form.

            :param form:
                Form instance
        """
        try:
            obj = self._populate_obj(form)
            self.modell.add(obj)
            self.modell.commit()
            self.on_record_created(obj)
            return obj
        except Exception:
            self.modell.rollback()
            raise

    def _populate_obj(self, form):
        obj = self.modell.new_model()
        for name, field in form._fields.iteritems():
            if isinstance(field, FileField):

                if field.has_file():
                    save_paths = []
                    for fs in field.data:
                        if fs.filename and fs.filename != '<fdopen>':
                            filename = secure_filename(fs.filename)
                            save_path = field.save_path
                            if not save_path:
                                save_path = os.path.join(
                                    self.data_browser.upload_folder, filename)
                            if isinstance(save_path, types.FunctionType):
                                save_path = save_path(obj, filename)
                            fs.save(save_path)
                            save_paths.append(save_path)
                    setattr(obj, field.name, save_paths if field.multiple else
                            save_paths[0])
                continue
            if field.raw_data:
                field.populate_obj(obj, name)
        return obj

    def on_record_created(self, obj):
        pass

    def _get_list_filters(self):
        ret = []
        for fltr in self.filters:
            if not fltr.model_view:
                fltr.model_view = self
            ret.append(fltr)
        return ret

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
            (if it has any meaning for a store modell).

            By default do nothing.
        """
        pass

    def get_actions(self, processed_objs=None):
        return []

    def _compose_actions(self, processed_objs=None):
        '''
        compose actions, when in list view, all actions will be returned,
        but in form, only enabled actions will be returned
        :return: a list of BaseAction
        '''
        ret = []
        in_list_view = not processed_objs
        for action in self.get_actions(processed_objs):
            action.model_view = self
            if in_list_view or action.test(*processed_objs) == ACTION_OK:
                ret.append(action)
        return ret

    def _update_objs(self, form, objs):
        """
        Update objs from form.
        :param form:
            Form instance
        :param objs:
            a list of Model instance
        """

        action_name = request.form.get("__action__")
        processed_objs = [self.expand_model(obj) for obj in objs]

        if action_name:
            for action in self._compose_actions(processed_objs):
                if action.name == action_name:
                    for obj in processed_objs:
                        ret_code = action.test(obj)
                        if ret_code != ACTION_OK:
                            flash(
                                _(u"can't apply %(action)s due to %(reason)s",
                                  action=action.name,
                                  reason=
                                  action.forbidden_msg_formats[ret_code] %
                                  {'obj': unicode(obj)}),
                                'error')
                            return False
                    try:
                        ret = action.op_upon_list(processed_objs, self)

                        if isinstance(ret, tuple):
                            flash(ret[-1], "error")
                            return False

                        if not action.readonly:
                            self.modell.commit()
                            flash(action.success_message(processed_objs),
                                  'success')
                        if isinstance(ret, werkzeug.wrappers.BaseResponse) \
                           and ret.status_code == 302:
                            return ret
                        return True
                    except Exception, ex:
                        msg = ('Failed to update %(model_label)s %(objs)s due '
                               'to %(error)s')
                        msg = _(msg,
                                model_label=self.modell.label,
                                objs=",".join(unicode(obj) for obj in
                                              processed_objs),
                                error=unicode(ex))
                        flash(msg, 'error')
                        self.modell.rollback()
                        raise
            raise ValidationError(
                _('invalid action %(action)s', action=action_name))
            # normal update
        try:
            self.try_edit(processed_objs)
            # compute the field should be holded
            untouched_fields = set(name[len("hold-value-"):] for name, field in
                                   request.form.iteritems() if
                                   name.startswith("hold-value-"))
            for obj in processed_objs:
                for name, field in form._fields.iteritems():
                    if isinstance(field, FileField):
                        if field.has_file():
                            save_paths = []
                            for fs in field.data:
                                if fs.filename and fs.filename != '<fdopen>':
                                    filename = secure_filename(fs.filename)
                                    save_path = field.save_path
                                    if not save_path:
                                        save_path = os.path.join(
                                            self.data_browser.upload_folder,
                                            filename)
                                    if isinstance(save_path,
                                                  types.FunctionType):
                                        save_path = save_path(obj, filename)
                                    fs.save(save_path)
                                    save_paths.append(save_path)
                            setattr(obj, field.name, save_paths if
                                    field.multiple else save_paths[0])
                        continue
                    if name not in untouched_fields and field.raw_data:
                        if isinstance(field, extra_fields.URLField) and \
                           getattr(obj, name) is None:
                            field.populate_obj(obj, name)
                            # if not convert field to string, will burst into
                            # error
                            setattr(obj, name, getattr(obj, name).url)
                        else:
                            field.populate_obj(obj, name)

                self.do_update_log(obj, _("update"))
                flash(_(u"%(model_label)s %(obj)s was updated and saved",
                        model_label=self.modell.label, obj=unicode(obj)))
                self.on_model_change(form, obj)
                self.modell.commit()
            return True
        except Exception, ex:
            self.modell.rollback()
            flash(
                _('Failed to update %(model_label)s %(obj)s due to %(error)s',
                  model_label=self.modell.label,
                  obj=",".join([unicode(obj) for obj in objs]),
                  error=unicode(ex)), 'error')
            return False

    def _compose_warn_msg(self, form):
        warn_msg = u"&".join([k + u"-" + u"; ".join(v) for k, v in
                              form.errors.items()]).encode('utf-8')
        return warn_msg

    def _get_around_steps(self, current_step):
        step_names = self._compose_create_col_specs().keys()

        last_step = None
        next_step = None
        if current_step > 0:
            args = request.args.to_dict()
            args['__step__'] = current_step - 1
            last_step = {
                'name': step_names[current_step - 1],
                'url': urlparse.urlunparse(
                    ('', '', request.path, '',
                     '&'.join(k + '=' + unicode(v) for k, v in args.items()),
                     ''))
            }
        if current_step < len(step_names) - 1:
            args = request.args.to_dict()
            args['__step__'] = current_step + 1
            name = self._compose_create_col_specs().keys()[current_step + 1]
            next_step = {
                'name': name,
                'url': urlparse.urlunparse(
                    ('', '', request.path, '',
                     '&'.join(k + '=' + unicode(v) for k, v in args.items()),
                     ''))
            }
        return last_step, next_step

    def _compose_create_form(self, current_step):
        """
        create a form for creation using create columns
        """
        default_args = {}
        for k, v in request.args.iterlists():
            if self.modell.has_kolumne(k):
                kol = self.modell.get_kolumne(k)
                if kol.is_relationship():
                    q = kol.remote_side.query
                    if kol.direction == 'MANYTOONE':
                        v = q.get(v[0])
                        if v is not None:
                            default_args[k] = v
                    else:
                        values = []
                        for i in v:
                            v_ = q.get(i)
                            if v_ is not None:
                                values.append(v_)
                        default_args[k] = values
                else:
                    default_args[k] = kol.coerce_value(v[0]) if v[0] else ''
        obj = None
        if default_args:
            obj = type("_temp", (object, ), default_args)()

        create_col_specs = self._compose_create_col_specs(current_step)
        assert isinstance(create_col_specs, dict)
        if self._create_form is None:
            self._create_form = self._scaffold_form(
                itertools.chain(*create_col_specs.values()))
        ret = self._create_form(obj=obj)
        # set the default args in form, otherwise the last step of
        # creation won't be finished
        for k, v in default_args.items():
            if v and hasattr(ret, k) and k not in request.form:
                getattr(ret, k).data = v
            # compose field sets, note! field sets are our stuffs other than
        # the standard wtforms.Form, they are ONLY use to generate form
        # in html page
        ret.fieldsets = OrderedDict()
        focus_set = False
        # only stuff bound fields take effects
        for fs_name, fs_col_specs in create_col_specs.items():
            for col_spec in fs_col_specs:
                field, focus_set = \
                    self._composed_stuffed_field(obj,
                                                 ret[col_spec.col_name],
                                                 col_spec,
                                                 focus_set)
                ret.fieldsets.setdefault(fs_name, []).append(field)
        return ret

    def _scaffold_form(self, col_specs):
        """
        Create form from the model
        """
        field_dict = dict((col_spec.col_name,
                           col_spec.make_field(model_view=self))
                          for col_spec in col_specs)
        return type(self.modell.name + 'Form', (BaseForm, ), field_dict)

    def _composed_stuffed_field(self, obj, bound_field, col_spec, focus_set):
        # why we stuff our own goods in field here? since it's the
        # framework's duty, not the one who implements other backends

        # if focus not set, then it is determined by if the field is disabled
        field = StuffedField(obj, bound_field, col_spec, focus_set)
        return field, field.__auto_focus__

    @property
    def _edit_col_specs(self):
        return self._compose_normalized_col_specs(self.edit_columns)

    def _get_url(self, endpoint, **kwargs):
        if isinstance(self.blueprint, Flask):
            return url_for(endpoint, **kwargs)
        else:
            return url_for(".".join([self.blueprint.name, endpoint]), **kwargs)

    def _scaffold_list_columns(self, order_by, desc):
        """
        collect columns displayed in table
        """

        def _(order_by, desc):
            for c in self._list_col_specs:
                if c.col_name in self._sortable_column_map:
                    args = request.args.copy()
                    args["order_by"] = self._sortable_column_map[c.col_name]
                    if order_by == args['order_by']:  # the table is sorted by c,
                    # so revert the order
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
                yield dict(name=c.col_name, label=c.label, doc=c.doc,
                           sort_url=sort_url)

        return list(_(order_by=order_by, desc=desc))

    @werkzeug.cached_property
    def _sortable_column_map(self):
        ret = {}
        for c in self.sortable_columns:
            if isinstance(c, basestring):
                ret[c] = c
            else:
                ret[c[0]] = c[1]
        return ret

    def _scaffold_list(self, objs):
        """
        convert the objects to a dict suitable for template renderation
        """

        def g():
            for idx, r in enumerate(objs):
                r = self.expand_model(r)
                #converter = ValueConverter(r, self)
                pk = self.modell.get_pk_value(r)
                fields = []
                for c in self._list_col_specs:
                    raw_value = operator.attrgetter(c.col_name)(r)
                    field = c.make_field(r, self)
                    bound_field = field.bind(None, c.col_name)
                    bound_field.process_data(raw_value)
                    fields.append(bound_field)

                yield dict(pk=pk, fields=fields,
                           css=self.patch_row_css(idx, r) or "",
                           attrs=self.patch_row_attr(idx, r),
                           repr_=self.repr_obj(r),
                           obj=r,
                           forbidden_actions=[action.name for action in
                                              self._compose_actions() if
                                              action.test(r) != ACTION_OK])

        return [] if not objs else list(g())

    def _parse_filters(self):
        """
        set filter's value using args
        """
        shadow_column_filters = copy.copy(self._get_list_filters())
        #如果不用copy的话，会修改原来的filter
        op_id_2_filter = dict(
            (fltr.op.id, fltr) for fltr in shadow_column_filters)
        # initialize filter's value with default value
        for op_id, filter in op_id_2_filter.items():
            # clear original value
            filter.value = None
            if filter.default_value is not None:
                filter.value = filter.default_value
            if isinstance(filter, filters.Only) and request.args and \
                    not request.args.get(filter.col_name):
                filter.value = False
        for k, v in request.args.lists():
            try:
                op_id_2_filter[k].value = (v[0] if len(v) == 1 else v)
            except KeyError:
                pass
        return shadow_column_filters

    def _get_edit_template(self):
        """
        get the real edit template, if you specify option
        "ModelView.edit_template",
        it will be used, else "/__data_browser/form.html" will be used
        """
        if self.edit_template is None:
            self.edit_template = os.path.join(
                self.data_browser.blueprint.name, "form.html")
        return self.edit_template

    def _compose_batch_edit_col_specs(self, preprocessed_objs=None):
        if not self._batch_edit_col_specs:
            self._batch_edit_col_specs = \
                self._compose_normalized_col_specs(self.batch_edit_columns)
        return self._batch_edit_col_specs

    def _compose_rows_action_desc(self, models):
        ret = {}
        customized_actions = self._compose_actions()
        if customized_actions:
            for model in models:
                id = self.modell.get_pk_value(model)
                preprocessed_model = self.expand_model(model)
                d = {"name": unicode(model), "actions": {}}
                for action in customized_actions:
                    error_code = action.test(preprocessed_model)
                    if error_code != ACTION_OK:
                        d["actions"][action.name] = error_code
                ret[id] = d
        return ret

    def _get_extra_params(self, view_name):
        kwargs = self.extra_params.get(view_name, {})
        ret = {}
        for k, v in kwargs.items():
            if isinstance(v, types.FunctionType):
                ret[k] = v(self)
            else:
                ret[k] = v
        return ret
