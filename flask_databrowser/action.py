# -*- coding: UTF-8 -*-
from flask.ext.babel import gettext, ngettext

class BaseAction(object):

    def __init__(self, name):
        self.name = name

    def op(self, model):
        return ""

    def success_message(self, models):
        try: 
            model_name = getattr(models[0], "__modelname__")
        except AttributeError:
            model_name = models[0].__class__.__name__ + ' '
        return model_name + ",".join(unicode(model) for model in models).join(['[', ']']) + gettext(u"被成功%(name)s", name=self.name)

    def error_message(self, models):
        try: 
            model_name = getattr(models[0], "__modelname__")
        except AttributeError:
            model_name = models[0].__class__.__name__ + ' '
        return model_name + ','.join(unicode(model) for model in models).join(['[', ']']) + gettest(u"%(name))s失败", name=self.name)

    def enabled(self, model):
        return True

    def disabled_tooltip(self, model):
        try: 
            model_name = getattr(model, "__modelname__")
        except AttributeError:
            model_name = model.__class__.__name__ + ' '
        return model_name + gettext(u'[%(object)s]不能被%(name)s', object=unicode(model), name=self.name)  
