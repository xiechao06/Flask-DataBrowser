# -*- coding: UTF-8 -*-
import types
from flask import request,url_for, render_template, flash, redirect, g
from flask.ext.principal import PermissionDenied
from flask.ext.babel import ngettext, gettext as _
from flask.ext.databrowser.exceptions import ValidationError


def get_primary_key(model):
    """
        Return primary key name from a model

        :param model:
            Model class
    """
    from sqlalchemy.schema import Table
    if isinstance(model, Table):
        for idx, c in enumerate(model.columns):
            if c.primary_key:
                return c.key
    else:
        props = model._sa_class_manager.mapper.iterate_properties

        for p in props:
            if hasattr(p, 'columns'):
                for c in p.columns:
                    if c.primary_key:
                        return p.key

    return None


def url_for_other_page(page):
    """
    generate the other page's url
    """
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args) # pylint: disable=W0142


class TemplateParam(object):
    """A class intends to be templates parameter should inherit this class"""
   
    def as_dict(self, *fields):
        items = []
        for field in fields:
            if isinstance(field, types.StringType):
                if field == "values":
                    raise ValueError(u'you can\'t use "values" as the key, since it is the method of dict type')
                v = getattr(self, field)
                if v is None:
                    v = ""
            elif isinstance(field, types.TupleType):
                if field[0] == "values":
                    raise ValueError(u'you can\'t use "values" as the key, since it is the method of dict type')
                v = getattr(self, field[0])
                if v is None:
                    v = ""
            items.append((field, v))
        return dict(items)

named_actions = set()

from functools import wraps


def raised_when(test, assertion):
    def decorator(f):
        @wraps(f)
        def f_(*args, **kwargs):
            if test(*args, **kwargs):
                raise assertion
            return f(*args, **kwargs)
        return f_
    
    return decorator


def raised(E, test, *args, **kwargs):
    try:
        test(*args, **kwargs)
        return True
    except E:
        return False


def make_disabled_field(field):
    class FakeField(field.field_class):

        def __call__(self, **kwargs):
            kwargs["disabled"] = True
            return super(FakeField, self).__call__(**kwargs)

        def validate(self, form, extra_validators=()):
            return True

        # dirty trick
        @property
        def read_only(self):
            return True

    field.field_class = FakeField
    return field


def fslice(iterable, predict):
    a = []
    b = []
    for i in iterable:
        if predict(i):
            a.append(i)
        else:
            b.append(i)
    return a, b


def get_description(view, col_name, obj, col_spec=None):
    if col_spec and col_spec.doc:
            return col_spec.doc
    # TODO this model should be the one registered in model view
    if view.__column_docs__:
        ret = view.__column_docs__.get(col_name)
        if ret:
            return ret
    # if this model is actually a model
    if obj and hasattr(obj.__class__, "_sa_class_manager"):
        return get_doc_from_table_def(obj.__class__, col_name)
    return ""


def get_doc_from_table_def(model, col_name):
    doc = ""
    attr_name_list = col_name.split('.')
    last_model = model
    for attr_name in attr_name_list[:-1]:
        attr = getattr(last_model, attr_name)
        if hasattr(attr, "property"):
            last_model = attr.property.mapper.class_
        else:
            last_model = None
            break
    if last_model:
        if hasattr(last_model, attr_name_list[-1]):
            from operator import attrgetter
            try:
                doc = attrgetter(attr_name_list[-1] + ".property.doc")(last_model)
            except AttributeError:
                pass
    return doc

import re
reg_b = re.compile(r"(android|bb\\d+|meego).+mobile|avantgo|bada\\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino", re.I|re.M)
reg_v = re.compile(r"1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\\-(n|u)|c55\\/|capi|ccwa|cdm\\-|cell|chtm|cldc|cmd\\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\\-s|devi|dica|dmob|do(c|p)o|ds(12|\\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\\-|_)|g1 u|g560|gene|gf\\-5|g\\-mo|go(\\.w|od)|gr(ad|un)|haie|hcit|hd\\-(m|p|t)|hei\\-|hi(pt|ta)|hp( i|ip)|hs\\-c|ht(c(\\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\\-(20|go|ma)|i230|iac( |\\-|\\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\\/)|klon|kpt |kwc\\-|kyo(c|k)|le(no|xi)|lg( g|\\/(k|l|u)|50|54|\\-[a-w])|libw|lynx|m1\\-w|m3ga|m50\\/|ma(te|ui|xo)|mc(01|21|ca)|m\\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\\-2|po(ck|rt|se)|prox|psio|pt\\-g|qa\\-a|qc(07|12|21|32|60|\\-[2-7]|i\\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\\-|oo|p\\-)|sdk\\/|se(c(\\-|0|1)|47|mc|nd|ri)|sgh\\-|shar|sie(\\-|m)|sk\\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\\-|v\\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\\-|tdg\\-|tel(i|m)|tim\\-|t\\-mo|to(pl|sh)|ts(70|m\\-|m3|m5)|tx\\-9|up(\\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\\-|your|zeto|zte\\-", re.I|re.M)


def request_from_mobile():
    """
    test if request from mobile, thanks http://detectmobilebrowsers.com/mobile
    """
    user_agent = request.headers.get('User-Agent', None)
    if user_agent:
        b = reg_b.search(user_agent)
        v = reg_v.search(user_agent[0:4])
        return b or v
    return False

class ErrorHandler(object):

    def __init__(self, data_browser):
        self.data_browser = data_browser

    def __call__(self, error):
        from werkzeug.exceptions import NotFound
        template_fname = self.data_browser.error_template

        if isinstance(error, PermissionDenied):
            permissions = []
            for idx, need in enumerate(error.args[0].needs):
                permissions.append(str(need))
            err_msg = _(u'this operation needs the following permissions: %(permissions)s, contact administrator to grant them!', permissions=";".join(permissions))
        elif isinstance(error, ValidationError):
            err_msg = ",".join("%s: %s" % (k, v) for k, v in error.args[0].items())
        elif isinstance(error, NotFound):
            err_msg = _("Sorry, object doesn't exist!")
        else:
            # we need to log the crime scene
            # note, this is the last line of defence, we must resolve it here!
            from werkzeug.debug.tbtools import get_current_traceback

            traceback = get_current_traceback(skip=1, show_hidden_frames=False,
                                              ignore_system_exceptions=True)
            self.data_browser.app.logger.error("%s %s" % (request.method, request.url))
            self.data_browser.app.logger.error(traceback.plaintext)
            err_msg = _(u'Internal error "%(err)s", please contact us!', err=str(error))

        return render_template(template_fname, hint_message=err_msg, error=error, back_url=request.args.get("url", "/"), model_view={"request_from_mobile": g.request_from_mobile}) 


def test_request_type():
    from flask import g
    g.request_from_mobile = request_from_mobile()
