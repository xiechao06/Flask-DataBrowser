# -*- coding: UTF-8 -*-
from flask.ext.babel import gettext, ngettext
from .utils import raised_when, raised

_raised_when_model_view_unset = raised_when(lambda inst, *args, **kwargs: not inst.model_view, 
                                       RuntimeError(r'field "model view" unset, you should set it'))


class BaseAction(object):

    def __init__(self, name):
        self.name = name
        self.model_view = None

    def op(self, obj):
        return ""

    @property
    def model_name(self):
        return self.model_view.model_name

    @_raised_when_model_view_unset
    def success_message(self, models):
        """
        will be called when all operations done 
        """
        return self.model_name + ",".join(unicode(model) for model in models).join(
            ['[', ']']) + gettext(u"被成功%(name)s", name=self.name)

    @_raised_when_model_view_unset
    def error_message(self, models):
        """
        will be called when operations break
        """
        return self.model_name + ','.join(unicode(model) for model in models).join(
            ['[', ']']) + gettext(u"%(name)s失败", name=self.name)

    def try_(self):
        pass

    def _get_forbidden_msg_formats(self):
        return {}

    def get_forbidden_msg_formats(self):
        ret = self._get_forbidden_msg_formats()
        ret[-1] = self.model_name + gettext(u'[%%s]不能被%(name)s', name=self.name) # the default forbidden message
        return ret

    def test_enabled(self, model):
        return 0

class DeleteAction(BaseAction):
    
    def __init__(self, name=gettext("删除"), permission=None):
        super(DeleteAction, self).__init__(name)
        self.permission = permission

    def op(self, obj):
        # even a model-like object could be deleted
        self.model_view.session.delete(obj)

    def try_(self):
        if self.permission is not None:
            self.permission.test()

        
