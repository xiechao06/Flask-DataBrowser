#-*- coding:utf-8 -*-
from flask import request, render_template
from wtforms import ValidationError
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug.exceptions import NotFound

from flask.ext.babel import _
from flask.ext.principal import PermissionDenied


class ErrorHandler(object):
    def __init__(self, data_browser):
        self.data_browser = data_browser

    def __call__(self, error):
        template_fname = self.data_browser.error_template

        if isinstance(error, PermissionDenied):
            permissions = []
            for idx, need in enumerate(error.args[0].needs):
                permissions.append(str(need))
            err_msg = _(
                u'this operation needs the following permissions: %(permissions)s, contact administrator to grant '
                u'them!',
                permissions=";".join(permissions))
        elif isinstance(error, ValidationError):
            err_msg = ",".join("%s: %s" % (k, v) for k, v in error.args[0].items())
        elif isinstance(error, NotFound):
            err_msg = _("Sorry, object doesn't exist!")
        else:
            # we need to log the crime scene
            # note, this is the last line of defence, we must resolve it here!
            traceback = get_current_traceback(skip=1, show_hidden_frames=False,
                                              ignore_system_exceptions=True)
            self.data_browser.app.logger.error("%s %s" % (request.method, request.url))
            self.data_browser.app.logger.error(traceback.plaintext)
            err_msg = _(u'Internal error "%(err)s", please contact us!', err=str(error))

        return render_template(template_fname, hint_message=err_msg, error=error,
                               back_url=request.args.get("url", "/"))
