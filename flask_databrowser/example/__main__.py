# -*- coding: UTF-8 -*-
"""
@author: Yangminghua
@version: $
"""

from flask.ext.principal import Permission, RoleNeed, PermissionDenied

admin_permission = Permission(RoleNeed("Admin"))

from collections import namedtuple

roll_call_perm = Permission(namedtuple("foo", ["method"])('roll_call'))

def main():
    from flask import Blueprint, request
    from basemain import app, db

    from flask.ext.principal import Principal

    principal = Principal(app)

    @app.errorhandler(PermissionDenied)
    def permission_denied(error):
        permissions = []
        for idx, need in enumerate(error.args[0].needs):
            if need.method == "role":
                s = '角色是' + need.value
            else:
                s = need.method
            permissions.append(s)
        return '该操作(' + request.url + ')被拒绝需要的访问权限为:' + ";".join(permissions)

    from flask.ext import databrowser
    from flask.ext.databrowser.action import DeleteAction

    from models import User
    accounts_bp = Blueprint("accounts", __name__, static_folder="static", 
                            template_folder="templates")
    browser = databrowser.DataBrowser(app, db, page_size=4)

    class UserModelView(databrowser.ModelView):

        list_template = "accounts/list.haml"

        def patch_row_css(self, idx, row):
            if row.roll_called == 1:
                return "box warning"

        from flask.ext.databrowser.column_spec import ImageColumnSpec, TableColumnSpec, PlaceHolderColumnSpec
        __list_columns__ = ["id", "name", "group", "password", "roll_called", "group.name", "create_time", ImageColumnSpec("avatar", alt=u"头像", 
            formatter=lambda v, model: "http://farm9.staticflickr.com/8522/8478415115_152c6f5e55_m.jpg"), "good"]
        __form_columns__ = ["id", "name", "group", "password", "roll_called", "good", 
                            ImageColumnSpec("avatar", alt=u"头像", 
                                            formatter=lambda v, model: "http://farm9.staticflickr.com/8522/8478415115_152c6f5e55_m.jpg"),
                            PlaceHolderColumnSpec("dogs", "dogs", "accounts/dogs.html"),
                            TableColumnSpec("dogs", css_class="table table-striped table-hover table-condensed table-bordered"), 
                            ]

        __batch_form_columns__ = ["name", "group"]

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
            "name": u"姓名",
            "create_time": u"创建于", 
            "group": u"用户组",
            "roll_called": u"点名过", 
            "group.name": u"用户组名称",
        }

        __default_order__ = ("name", "desc")

        from flask.ext.databrowser import filters
        from datetime import datetime, timedelta
        today = datetime.today()
        yesterday = today.date()
        week_ago = (today - timedelta(days=7)).date()
        _30days_ago = (today - timedelta(days=30)).date()


        __column_filters__ = [filters.In_("group", name=u"是", opt_formatter=lambda opt: opt.name),
                             filters.BiggerThan("create_time", name=u"在", 
                                                options=[(yesterday, u'一天内'),
                                                        (week_ago, u'一周内'), 
                                                        (_30days_ago, u'30天内')]), 
                             filters.EqualTo("name", name=u"是"),
                             filters.Contains("name", name=u"包含")
                             ]

        __list_filters__ = [filters.NotEqualTo("name", value=u"Type")]


        from flask.ext.databrowser.action import BaseAction

        class RollCall(BaseAction):

            def op(self, model):
                model.roll_call()

            def test_enabled(self, model):
                if model.roll_called:
                    return -1
                return 0

            def try_(self):
                roll_call_perm.test()

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

        __customized_actions__ = [MyDeleteAction(u"删除", admin_permission), RollCall(u"点名")]

    browser.register_model_view(UserModelView(User, u"用户"), accounts_bp, extra_params={"form_view": {"company": "xc"}})
    app.register_blueprint(accounts_bp, url_prefix="/accounts")
    app.config["SECRET_KEY"] = "JHdkj1;"
    app.config["CSRF_ENABLED"] = False

    app.run(debug=True, port=5001, host="0.0.0.0")

if __name__ == "__main__":
    main()
