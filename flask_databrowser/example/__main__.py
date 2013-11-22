# -*- coding: UTF-8 -*-
"""
@author: Yangminghua
@version: $
"""

from flask import redirect, Blueprint,url_for, send_from_directory
from flask.ext.login import LoginManager
from flask.ext.principal import Permission, RoleNeed
from flask.ext.databrowser import filters
from collections import OrderedDict
from flask.ext.databrowser.column_spec import FileColumnSpec, InputPlaceHolderColumnSpec
from flask.ext.databrowser.grouper import SAPropertyGrouper
from flask.ext.databrowser.sa import SAModell
from flask.ext.databrowser.column_spec import ImageColumnSpec, TableColumnSpec, PlaceHolderColumnSpec, InputColumnSpec

admin_permission = Permission(RoleNeed("Admin"))

from collections import namedtuple

roll_call_perm = Permission(namedtuple("foo", ["method"])('roll_call'))


def main():
    from basemain import app, db

    from flask.ext.principal import Principal

    login_manager = LoginManager()
    login_manager.setup_app(app)
    principal = Principal(app)

    @app.route("/favicon.ico")
    def favicon():
        return ""

    @login_manager.user_loader
    def load_user(userid):
        return User.get(userid)


    from flask.ext import databrowser
    from flask.ext.databrowser.action import DeleteAction, DirectAction

    from models import User, Car

    accounts_bp = Blueprint("accounts", __name__, static_folder="static",
                            template_folder="templates")
    browser = databrowser.DataBrowser(app)


    from flask.ext.databrowser.error_handle import ErrorHandler

    error_handler = ErrorHandler(browser)
    if not app.config["DEBUG"]:
        app.errorhandler(Exception)(error_handler)
        app.errorhandler(404)(error_handler)

    class UserModelView(databrowser.ModelView):

        column_hide_backrefs = False
        list_template = "accounts/list.html"
        edit_template = create_template = "accounts/form.html"
        can_create = True
        #can_batchly_edit = False
        on_fly = False

        def preprocess(self, obj):
            class _Proxy(object):

                def __init__(self, obj):
                    self.obj = obj
                    self.foo = 1

                @property
                def pic_url(self):
                    if self.pic_path:
                        return url_for("serv_pic", filename=self.pic_path)
                    else:
                        return ""

                def __getattr__(self, attr):
                    return getattr(self.obj, attr)

            return _Proxy(obj)

        def repr_obj(self, obj):
            return obj.name

        def patch_row_css(self, idx, row):
            if row.roll_called == 1:
                return "box warning"

                #def try_edit(self, objs):
                #raise PermissionDenied()

        def get_create_help(self):
            return "<h3>this is create view</h3>"

        def get_edit_help(self, objs):
            return "<h3>this is edit view</h3>"

        def get_list_help(self):
            return "<h3>this is list view</h3>"

        @property
        def list_columns(self):
            return ["id", "name", "group", "password", "roll_called", "group.name", "create_time",
                            ImageColumnSpec("avatar", alt=u"头像",
                                            formatter=lambda v,
                                                             model: "http://farm9.staticflickr"
                                                                    ".com/8522/8478415115_152c6f5e55_m.jpg",
                                            doc=u"头像，^_^！"), "good"]
        @property
        def create_columns(self):
            ret = OrderedDict()
            ret["primary"] = ["name", "group", "password"]
            ret["secondary"] = [
                InputPlaceHolderColumnSpec("age", template_fname="/accounts/age-snippet.html"),
                "roll_called", "birthday", "create_time", "car_list"]
            return ret

        def get_form_columns(self, obj=None):
            ret = OrderedDict()
            ret[u"主要的"] = ["id", InputColumnSpec("name", disabled=True),
                           PlaceHolderColumnSpec("group", template_fname="/accounts/group-snippet.html",
                                                 form_width_class="col-lg-3")
                , "password",
                                        PlaceHolderColumnSpec("foo", template_fname="/accounts/foo-snippet.html")]
            ret[u"次要的"] = ["roll_called", "good",
                                        PlaceHolderColumnSpec("age", template_fname="/accounts/age-snippet.html"), "create_time",
                                        ImageColumnSpec("avatar", alt=u"头像",
                                                        formatter=lambda v,
                                                                         model: "http://farm9.staticflickr"
                                                                                ".com/8522/8478415115_152c6f5e55_m.jpg",
                                                        doc=u"头像， ^_^!")]
            ret[u"额外的"] = [
                TableColumnSpec("dogs", css_class="table table-striped table-hover table-condensed table-bordered"),
                InputColumnSpec("car_list", css_class="alert alert-info", group_by=lambda x: x.model[0],
                                disabled=False),
                # "car_list"
            ]

            ret[u"头像"] = [
                ImageColumnSpec("pic_url", label=u"头像"),
                FileColumnSpec("pic_path", label=u"上传")
            ]
            return ret

        #__batch_form_columns__ = OrderedDict()
        #__batch_form_columns__["primary"] = ["name", InputColumnSpec("group", read_only=True)]
        #__batch_form_columns__["secondary"] = ["age", "roll_called"]

        column_formatters = {
            "create_time": lambda v, model: v.strftime("%Y-%m-%d %H") + u"点",
            "avatar": lambda v, model: "http://farm9.staticflickr.com/8522/8478415115_152c6f5e55_m.jpg",
            "group": lambda v, model: v.name if v else "",
        }

        column_docs = {
            "password": u"md5值",
            "roll_called": u"点名过",
        }

        #__sortable_columns__ = ["id", "name", "group"]

        column_labels = {
            "age": u"年龄",
            "name": u"姓名",
            "create_time": u"创建于",
            "group": u"用户组",
            "roll_called": u"点名过",
            "group.name": u"用户组名称",
        }

        default_order = ("name", "desc")

        @property
        def list_filters(self):
            from datetime import datetime, timedelta

            today = datetime.today()
            yesterday = today.date()
            week_ago = (today - timedelta(days=7)).date()
            _30days_ago = (today - timedelta(days=30)).date()
            return [filters.In_("group", name=u"是", opt_formatter=lambda opt: opt.name),
                              filters.BiggerThan("create_time", name=u"在",
                                                 options=[(yesterday, u'一天内'),
                                                          (week_ago, u'一周内'),
                                                          (_30days_ago, u'30天内')], default_value=str(_30days_ago)),
                              filters.EqualTo("name", name=u"是"),
                              filters.Contains("name", name=u"包含"),
                              filters.Only("roll_called", display_col_name=u"仅展示点名", test=lambda col: col == True,
                                           notation="__roll_called", default_value=False),
                              filters.Between("create_time")
        ]

        #def __list_filters__(self):
        #return [filters.NotEqualTo("name", value=u"Type")]


        from flask.ext.databrowser.action import BaseAction

        class RollCall(BaseAction):

            def op(self, model):
                model.roll_call()

            def test_enabled(self, model):
                if model.roll_called:
                    return -1
                return 0

                #def try_(self):
                #roll_call_perm.test()

        class MyDeleteAction(DeleteAction):

            def test_enabled(self, model):
                if model.name == "Spock":
                    return -3
                elif model.name == "Tyde":
                    return -2
                return 0

            def get_forbidden_msg_formats(self):
                return {-3: "[%s]是我的偶像, 不要删除他们",
                        -2: "[%s]是好狗，不要伤害他们"}

        def patch_row_attr(self, idx, row):
            if row.name == "Tyde":
                return {"title": u"测试"}

        class _ReadOnlyAction(DirectAction):

            def op_upon_list(self, model, model_view):
                return redirect("http://www.u148.com")

        __customized_actions__ = [MyDeleteAction(u"删除", None, data_icon="fa fa-times"),
                                  RollCall(u"点名", warn_msg=u"点名后就是弱智！"), RollCall(u"点名", warn_msg=u"点名后就是弱智！"),
                                  RollCall(u"点名", warn_msg=u"点名后就是弱智！"), RollCall(u"点名", warn_msg=u"点名后就是弱智！"),
                                  RollCall(u"点名", warn_msg=u"点名后就是弱智！"), RollCall(u"点名", warn_msg=u"点名后就是弱智！"),
                                  RollCall(u"点名", warn_msg=u"点名后就是弱智！"), _ReadOnlyAction(u"打酱油的")]

    user_model_view = UserModelView(SAModell(User, db, u"用户"))
    browser.register_model_view(user_model_view, accounts_bp,
                                extra_params={"form_view": {"age_hint": "modify your age here"},
                                              "create_view": {"age_hint": "input your age here"}})

    class CarModelView(databrowser.ModelView):

        __form_columns__ = ["id", "model"]

    browser.register_model_view(CarModelView(SAModell(Car, db, u"汽车")), accounts_bp,
                                extra_params={"form_view": {"company": "xc"}})
    app.register_blueprint(accounts_bp, url_prefix="/accounts")

    @app.route("/")
    def index():
        return redirect(user_model_view.url_for_list())

    @app.route("/serv-pic/<filename>")
    def serv_pic(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    app.config["SECRET_KEY"] = "JHdkj1;"
    app.config["CSRF_ENABLED"] = False
    app.config["UPLOAD_FOLDER"] = r"e:\uploads"
    app.run(debug=True, port=5001, host="0.0.0.0")


if __name__ == "__main__":
    main()
