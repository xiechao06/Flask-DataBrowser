# -*- coding: UTF-8 -*-
from flask import redirect, request
from flask.ext.babel import _
from flask.ext.principal import PermissionDenied, Permission
from .constants import BACK_URL_PARAM
from .utils import raised_when


_runtime_error = RuntimeError('field "model view" unset, you should set it')
_raised_when_model_view_unset = raised_when(lambda inst, *args, **kwargs:
                                            not inst.model_view,
                                            _runtime_error)

ACTION_IMPERMISSIBLE = -1
ACTION_OK = 0


class BaseAction(object):

    readonly = False

    def __init__(self, name, css_class="btn btn-info", data_icon="",
                 warn_msg=""):
        self.name = name
        self.model_view = None
        self.css_class = css_class
        self.data_icon = data_icon
        self.warn_msg = warn_msg
        self._model_view = None

    def op_upon_list(self, objs, model_view):

        for obj in objs:
            self._op(obj, model_view)

    def _op(self, obj, model_view):
        self.op(obj)
        model_view.do_update_log(obj, self.name)

    def op(self, obj):
        return ""

    @property
    def model_view(self):
        return self._model_view

    @model_view.setter
    def model_view(self, value):
        self._model_view = value

    @property
    def _model_label(self):
        return self.model_view.modell.label

    @_raised_when_model_view_unset
    def success_message(self, records):
        """
        will be called when all operations done
        """
        return _(u"operation %(action)s applied upon %(model_label)s - "
                 "[%(records)s] successfully", action=self.name,
                 model_label=self._model_label,
                 records=",".join(unicode(record) for record in records))

    def extract_error_message(self, exception_, records):
        if isinstance(exception_, PermissionDenied):
            s = (u'no permission to apply operation %(action)s upon'
                 '%(model_label)s - [%(records)s]')
        else:
            s = (u'can\'t apply operation %(action)s upon'
                 '%(model_label)s - [%(records)s]')
        return _(s, action=self.name,
                 model_label=self._model_label,
                 records=",".join(unicode(record) for record in records))

    def test(self, *records):
        if self._model_view.permission_required:
            def _get_edit_need(obj):
                pk = self._model_view.modell.get_pk_value(obj)
                return self._model_view.edit_need(pk)
            needs = [_get_edit_need(record) for record in records]
            perm = Permission(*needs).union(Permission(
                self._model_view.edit_all_need))
            return 0 if perm.can() else ACTION_IMPERMISSIBLE

    @property
    def forbidden_msg_formats(self):
        s = _(u'no permission to apply %(action)s upon %(model_label)s [%%s]',
              action=self.name, model_label=self._model_label)
        return {ACTION_IMPERMISSIBLE: s}


class RedirectAction(BaseAction):

    readonly = True

    def __init__(self, name, css_class="btn btn-info", data_icon="",
                 warn_msg=""):
        super(RedirectAction, self).__init__(name, css_class, data_icon,
                                             warn_msg)

    def test(self, *records):
        return 0

    @property
    def forbidden_msg_formats(self):
        return {}


class DeleteAction(BaseAction):
    def __init__(self, name=_("remove"),
                 css_class="btn btn-danger", data_icon="fa fa-times",
                 warn_msg=""):
        super(DeleteAction, self).__init__(name, css_class, data_icon,
                                           warn_msg)

    def op_upon_list(self, objs, model_view):
        for obj in objs:
            self._op(obj, model_view)
        return redirect(request.args.get(BACK_URL_PARAM, request.url))

    def op(self, obj):
        # even a model-like object could be deleted
        return self.model_view.modell.delete_record(obj)

    def test(self, *records):
        if self._model_view.permission_required:
            def _get_remove_need(obj):
                pk = self._model_view.modell.get_pk_value(obj)
                return self._model_view.remove_need(pk)
            needs = [_get_remove_need(record) for record in records]
            perm = Permission(*needs).union(Permission(
                self._model_view.remove_all_need))
            return 0 if perm.can() else ACTION_IMPERMISSIBLE
