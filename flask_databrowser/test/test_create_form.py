#! /usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import namedtuple

from flask import Blueprint
from flask.ext.principal import PermissionDenied
from flask.ext.databrowser.sa import SAModell
from flask.ext.databrowser.test import basetest
from flask.ext.databrowser import ModelView, DataBrowser
from collections import OrderedDict


class TestCreate(basetest.BaseTest):
    def setup(self):
        super(TestCreate, self).setup()
        self.browser = DataBrowser(self.app, self.db)

        @self.app.errorhandler(Exception)
        def error_handler(error):
            if isinstance(error, RuntimeError):
                return error.message, 401

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

        user_model_view = UserModelView(SAModell(self.__tables.User, self.db))
        group_model_view = GroupModelView(SAModell(self.__tables.Group, self.db))
        blueprint = Blueprint("foo1", __name__, static_folder="static", template_folder="templates")
        self.browser.register_model_view(user_model_view, blueprint)
        self.browser.register_model_view(group_model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo1")

    def test_permissions(self):
        """
        when try_create raise exception, can't GET or POST
        """

        class UserModelView(ModelView):
            def try_create(self):
                raise PermissionDenied("can't create")

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user")
                assert rv.status_code == 401
                assert rv.data == "can't create"

                rv = c.post("/foo1/user", data={
                    'name': 'foo',
                })
                assert rv.status_code == 401
                assert rv.data == "can't create"

    def test_no_configuration(self):
        self.register()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user")
                assert rv.status_code == 200
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                controls = [i for i in d(".form-group").items()]
                assert len(controls) == 3
                labels = [i("label").text() for i in controls]
                assert "Group" in labels
                assert "Name *" in labels
                assert "Id *" in labels

    def test_simple_create(self):
        # we assert the form generated correctly
        # we assert the submit ok
        self.register()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.post("/foo1/group", data={"id": 1, "name": "foo"})
                assert 302 == rv.status_code
                rv = c.get("/foo1/user")
                assert rv.status_code == 200
                rv = c.post("/foo1/user", data={"group": 1, "name": "foo", "id": 1})
                assert 302 == rv.status_code
                rv = c.get("/foo1/user/1")
                assert rv.status_code == 200

    def test_create_in_fieldsets(self):

        class UserModelView(ModelView):
            @property
            def create_columns(self):
                ret = OrderedDict()
                ret["Group"] = ["group"]
                ret["name"] = ["name"]
                return ret

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user")
                assert rv.status_code == 200
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                fieldsets = [i for i in d("[data-role=fieldset-body]").items()]
                assert len(fieldsets) == 2

    def test_create_in_steps(self):

        class UserModelView(ModelView):
            create_in_steps = True

            @property
            def create_columns(self):
                ret = OrderedDict()
                ret["Group"] = ["group"]
                ret["name"] = ["name"]
                return ret

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user")
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                fieldsets = [i for i in d("fieldset").items()]
                assert len(fieldsets) == 1
                assert len(d("[data-role=next-step]")) == 1

    def test_actions(self):
        self.register()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user")
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                group = d("[data-role=trivial-control-group]")
                assert len(group) == 1
                assert len(group("#submit-btn")) == 1
                assert len(group("#reset-btn")) == 1
                #TODO actions

    def test_create_on_fly(self):
        self.register()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.post("/foo1/group", data={"id": 1, "name": "foo"})
                assert 302 == rv.status_code
                rv = c.post("/foo1/user?on_fly=1", data={"group": 1, "name": "foo", "id": 1})
                assert 200 == rv.status_code
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                assert len(d("#my-modal")) == 1

    def test_input_column_spec(self):
        class UserModelView(ModelView):
            @property
            def create_columns(self):
                ret = OrderedDict()
                from flask.ext.databrowser.col_spec import InputColumnSpec

                ret["group"] = ["group"]
                ret["name"] = [InputColumnSpec("name", disabled=True)]
                return ret

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user")
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                assert d("[name=name]").attr("disabled")

    def test_place_holder_column_spec(self):
        class UserModelView(ModelView):
            @property
            def create_columns(self):
                from flask.ext.databrowser.col_spec import InputColumnSpec

                return ["name", InputColumnSpec("group", label="group")]

        self.register(UserModelView)
        with self.app.test_request_context():
            with self.app.test_client() as c:
                c.post("/foo1/group", data={"id": 1, "name": "foo"})

                rv = c.get("/foo1/user")
                from pyquery import PyQuery as pq

                d = pq(rv.data)
                assert len(d("[data-role=select2blank]")) == 1


if __name__ == "__main__":
    TestCreate().run_plainly()
