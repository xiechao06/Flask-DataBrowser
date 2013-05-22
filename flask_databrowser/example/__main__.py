# -*- coding: UTF-8 -*-
"""
@author: Yangminghua
@version: $
"""

from flask import redirect, Blueprint, request, abort
from flask.ext.login import LoginManager
from flask.ext.principal import Permission, RoleNeed, PermissionDenied
from flask.ext.databrowser import filters
from brownie.datastructures import OrderedDict

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
    from flask.ext.databrowser.action import DeleteAction, ReadOnlyAction

    from models import User, Car
    accounts_bp = Blueprint("accounts", __name__, static_folder="static", 
                            template_folder="templates")
    browser = databrowser.DataBrowser(app, db, page_size=4)

    from flask.ext.databrowser.utils import ErrorHandler
    error_handler = ErrorHandler(browser)
    if not app.config["DEBUG"]:
        app.errorhandler(Exception)(error_handler)
        app.errorhandler(404)(error_handler)

    class UserModelView(databrowser.ModelView):

        list_template = "accounts/list.html"
        edit_template = create_template = "accounts/form.html"
        can_batchly_edit = True
        #as_radio_group = True

        def patch_row_css(self, idx, row):
            if row.roll_called == 1:
                return "box warning"

        #def try_edit(self, objs):
            #raise PermissionDenied()

        from flask.ext.databrowser.column_spec import ImageColumnSpec, TableColumnSpec, PlaceHolderColumnSpec, InputColumnSpec
        def get_create_help(self):
            return "<h3>this is create view</h3>"
        
        def get_edit_help(self, objs):
            return "<h3>this is edit view</h3>"

        def get_list_help(self):
            return "<h3>this is list view</h3>"

        from flask.ext.databrowser.column_spec import ImageColumnSpec, TableColumnSpec, PlaceHolderColumnSpec
        __list_columns__ = ["id", "name", "group", "password", "roll_called", "group.name", "create_time", ImageColumnSpec("avatar", alt=u"头像", 
            formatter=lambda v, model: "http://farm9.staticflickr.com/8522/8478415115_152c6f5e55_m.jpg", doc=u"头像，^_^！"), "good"]
        __create_columns__ = OrderedDict()
        __create_columns__["secondary"] = [PlaceHolderColumnSpec("age", template_fname="/accounts/age-snippet.html", as_input=True), "roll_called"]
        __create_columns__["primary"] = ["name", "group", "password"]

        __form_columns__ = OrderedDict()
        __form_columns__[u"主要的"] = ["id", "name", "group", "password"]
        __form_columns__[u"次要的"] = ["roll_called", "good", PlaceHolderColumnSpec("age", template_fname="/accounts/age-snippet.html", as_input=True), "create_time", ImageColumnSpec("avatar", alt=u"头像", 
                                            formatter=lambda v, model: "http://farm9.staticflickr.com/8522/8478415115_152c6f5e55_m.jpg", doc=u"头像， ^_^!")]
        __form_columns__[u"额外的"] = [TableColumnSpec("dogs", css_class="table table-striped table-hover table-condensed table-bordered"),
                            TableColumnSpec("car_list", css_class="table table-striped table-hover table-condensed table-bordered", col_specs=["id", "model"])
                            ]

        __batch_form_columns__ = OrderedDict()
        __batch_form_columns__["primary"] = ["name", InputColumnSpec("group", read_only=True)]
        __batch_form_columns__["secondary"] = ["age", "roll_called"]

        __column_formatters__ = {
            "create_time": lambda v, model: v.strftime("%Y-%m-%d %H") + u"点",
            "avatar": lambda v, model: "http://farm9.staticflickr.com/8522/8478415115_152c6f5e55_m.jpg",
            "group": lambda v, model: v.name if v else "",
        }

        __column_docs__ = {
            "password": u"md5值",
        }

        __sortable_columns__ = ["id", "name", "group"]

        __column_labels__ = {
            "age": u"年龄",
            "name": u"姓名",
            "create_time": u"创建于", 
            "group": u"用户组",
            "roll_called": u"点名过", 
            "group.name": u"用户组名称",
        }

        __default_order__ = ("name", "desc")


        from datetime import datetime, timedelta
        today = datetime.today()
        yesterday = today.date()
        week_ago = (today - timedelta(days=7)).date()
        _30days_ago = (today - timedelta(days=30)).date()


        __column_filters__ = [filters.In_("group", name=u"是", opt_formatter=lambda opt: opt.name),
                              filters.BiggerThan("create_time", name=u"在", 
                                                 options=[(yesterday, u'一天内'),
                                                          (week_ago, u'一周内'), 
                                                          (_30days_ago, u'30天内')], default_value=str(_30days_ago)), 
                              filters.EqualTo("name", name=u"是"),
                              filters.Contains("name", name=u"包含"),
                              filters.Only("roll_called", display_col_name=u"仅展示点名", test=lambda col: col==True, notation="__roll_called", default_value=False),
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

        class _ReadOnlyAction(ReadOnlyAction):

            def op_upon_list(self, model, model_view):
                return redirect("http://www.u148.com")

        __customized_actions__ = [MyDeleteAction(u"删除", None), RollCall(u"点名", warn_msg=u"点名后就是弱智！"), RollCall(u"点名", warn_msg=u"点名后就是弱智！"),RollCall(u"点名", warn_msg=u"点名后就是弱智！"),RollCall(u"点名", warn_msg=u"点名后就是弱智！"),RollCall(u"点名", warn_msg=u"点名后就是弱智！"),RollCall(u"点名", warn_msg=u"点名后就是弱智！"),RollCall(u"点名", warn_msg=u"点名后就是弱智！"),_ReadOnlyAction(u"打酱油的")]

    user_model_view = UserModelView(User, u"用户")
    browser.register_model_view(user_model_view, accounts_bp, extra_params={"form_view": {"age_hint": "modify your age here"}, "create_view": {"age_hint": "input your age here"}})

    class CarModelView(databrowser.ModelView):

        __form_columns__ = ["id", "model"]

    browser.register_model_view(CarModelView(Car, u"汽车"), accounts_bp, extra_params={"form_view": {"company": "xc"}})
    app.register_blueprint(accounts_bp, url_prefix="/accounts")

    @app.route("/")
    def index():
        return redirect(user_model_view.url_for_list())
    app.config["SECRET_KEY"] = "JHdkj1;"
    app.config["CSRF_ENABLED"] = False
    app.run(debug=True, port=5001, host="0.0.0.0")

if __name__ == "__main__":
    main()
