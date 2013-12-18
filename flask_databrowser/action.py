# -*- coding: UTF-8 -*-
from flask import redirect, request
from flask.ext.babel import _
from .utils import raised_when

_raised_when_model_view_unset = raised_when(lambda inst, *args, **kwargs: not inst.model_view,
                                       RuntimeError(r'field "model view" unset, you should set it'))


class BaseAction(object):

    readonly = False

    def __init__(self, name, css_class="btn btn-info", data_icon="", warn_msg=""):
        self.name = name
        self.model_view = None
        self.css_class = css_class
        self.data_icon = data_icon
        self.warn_msg = warn_msg

    def op_upon_list(self, objs, model_view):
        for obj in objs:
            self._op(obj, model_view)

    def _op(self, obj, model_view):
        self.op(obj)
        model_view.do_update_log(obj, self.name)

    def op(self, obj):
        return ""

    @property
    def _model_label(self):
        return self.model_view.modell.label

    @_raised_when_model_view_unset
    def success_message(self, models):
        """
        will be called when all operations done
        """
        return _(u"operation %(action)s applied upon %(model_label)s - [%(models)s] successfully",
                 action=self.name, model_label=self._model_label, models=",".join(unicode(model) for model in models))

    @_raised_when_model_view_unset
    def error_message(self, models):
        """
        will be called when operations break
        """
        return _(u"operation %(action)s failed to apply upon %(model_label)s - [%(models)s]",
                 action=self.name, model_label=self._model_label, models=",".join(unicode(model) for model in models))

    def try_(self, processed_objs):
        pass

    def _get_forbidden_msg_formats(self):
        return {}

    def get_forbidden_msg_formats(self):
        ret = self._get_forbidden_msg_formats()
        ret[-1] = self._model_label + _(u'%(action)s can\'t apply upon %(model_label)s [%%s]', action=self.name, model_label=self._model_label) # the default forbidden message
        return ret

    def test_enabled(self, model):
        return 0


class RedirectAction(BaseAction):

    readonly = True

    def __init__(self, name, css_class="btn btn-info", data_icon="",
                 warn_msg=""):
        super(RedirectAction, self).__init__(name, css_class, data_icon,
                                             warn_msg)


class DeleteAction(BaseAction):
    def __init__(self, name=_("remove"), permission=None,
                 css_class="btn btn-danger", data_icon="fa fa-times", warn_msg=""):
        super(DeleteAction, self).__init__(name, css_class, data_icon, warn_msg)
        self.permission = permission

    def op_upon_list(self, objs, model_view):
        for obj in objs:
            self._op(obj, model_view)
        return redirect(request.args.get('url', request.url))

    def op(self, obj):
        # even a model-like object could be deleted
        return self.model_view.modell.delete_record(obj)

    def try_(self, processed_objs):
        if self.permission is not None:
            self.permission.test()
