# -*- coding: UTF-8 -*-
from collections import namedtuple

from flask import Blueprint
from flask.ext.principal import PermissionDenied
from flask.ext.databrowser.test import basetest
from flask.ext.databrowser import ModelView, DataBrowser
from collections import OrderedDict
from pyquery import PyQuery as pq


class TestEdit(basetest.BaseTest):
    def setup(self):
        super(TestEdit, self).setup()
        self.browser = DataBrowser(self.app, self.db)

    def setup_models(self):
        db = self.db

        class Group(db.Model):
            __tablename__ = "TB_GROUP"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(32), nullable=False, unique=True, doc=u"用户组名称")

        class User(db.Model):
            __tablename__ = "TB_USER"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(32), nullable=False, unique=True, doc=u"姓名")
            group_id = db.Column(db.Integer, db.ForeignKey("TB_GROUP.id"))
            group = db.relationship("Group", backref="users")

        self.__tables = namedtuple("foo", ["User", "Group"])(User, Group)

    def register(self, UserModelView=None):
        if not UserModelView:
            class UserModelView(ModelView):
                pass

        class GroupModelView(ModelView):
            pass

        user_model_view = UserModelView(self.__tables.User)
        group_model_view = GroupModelView(self.__tables.Group)
        blueprint = Blueprint("foo1", __name__, static_folder="static", template_folder="templates")
        self.browser.register_model_view(user_model_view, blueprint)
        self.browser.register_model_view(group_model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo1")

    def init_db(self):
        group = self.__tables.Group(name="foo")
        self.db.session.add(group)
        user1 = self.__tables.User(name="foo1", group=group)
        user2 = self.__tables.User(name="foo2", group=group)
        self.db.session.add_all([user1, user2])
        self.db.session.commit()

    def test_permissions(self):
        """
        when try_create raise exception, can't GET or POST
        """

        class UserModelView(ModelView):
            def try_edit(self, processed_objs=None):
                raise PermissionDenied

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user/1")
                assert rv.status_code == 404
                self.init_db()
                rv = c.get("/foo1/user/1")
                assert rv.status_code == 200
                d = pq(rv.data)
                inputs = [i for i in d("input").items()]
                assert all(
                    i.attr("disabled") == "disabled" for i in inputs if i.attr("type") not in ["button", "hidden"])

    def test_buttons(self):
        class UserModelView(ModelView):
            from flask.ext.databrowser.action import DeleteAction

            __customized_actions__ = [DeleteAction()]

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                self.init_db()
                rv = c.get("/foo1/user/1")
                assert 200 == rv.status_code
                d = pq(rv.data)
                assert len(d("[name=__action__]")) == 1
                rv = c.post("/foo1/user/1", data={"__action__": "remove", "name": "foo"})
                print rv.data
                assert 302 == rv.status_code
                rv = c.get("/foo1/user/1")
                assert 404 == rv.status_code

    def test_cant_batch_edit(self):
        class UserModelView(ModelView):
            can_batchly_edit = False

        self.register(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("#batch-edit")) == 0

    def test_batch_edit(self):
        self.register()
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("#batch-edit")) == 1
                rv = c.get("/foo1/user/1,2")
                d = pq(rv.data)
                assert len(d("[data-role=hold_value]")) == 1  # only group
                rv = c.post("/foo1/user/1,2",
                            data={"__builtin_action__": "commit", "hold-value-group": "on", "hold-value-name": "on"})
                assert 302 == rv.status_code


if __name__ == "__main__":
    TestEdit().run_plainly()
