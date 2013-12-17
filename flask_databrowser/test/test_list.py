#-*- coding:utf-8 -*-
from collections import namedtuple
from flask import Blueprint
from flask.ext.principal import PermissionDenied
from .basetest import BaseTest
from flask.ext.databrowser import DataBrowser, ModelView, filters, action
from pyquery import PyQuery as pq
from flask.ext.databrowser.sa import SABackend


class TestList(BaseTest):
    def setup(self):
        super(TestList, self).setup()
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

    def init_db(self):
        group1 = self.__tables.Group(name="foo1")
        group2 = self.__tables.Group(name="foo2")
        user1 = self.__tables.User(name="foo1", group=group1)
        user2 = self.__tables.User(name="foo2", group=group2)
        self.db.session.add_all([group1, group2, user1, user2])
        self.db.session.commit()

    def register_model(self, UserModelView=None):
        if not UserModelView:
            class UserModelView(ModelView):
                pass

        class GroupModelView(ModelView):
            pass
        user_model_view = UserModelView(SABackend(self.__tables.User, self.db))
        group_model_view = GroupModelView(SABackend(self.__tables.Group, self.db))
        blueprint = Blueprint(import_name="foo1", name=__name__, static_folder="static", template_folder="templates")
        self.browser.register_model_view(user_model_view, blueprint=blueprint)
        self.browser.register_model_view(group_model_view, blueprint=blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo1")

    def test_default_list(self):
        self.register_model()
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                assert 200 == rv.status_code
                d = pq(rv.data)
                assert len(d("#create-btn")) == 1
                assert len(d("#batch-edit")) == 1
                assert len(d("#list-table-body [type=checkbox]")) == 2
                assert len(d("table")) == 1
                assert len(d("#list-table-body tr")) == 2

    def test_filter(self):
        class UserModelView(ModelView):
            __column_filters__ = [filters.Contains("name")]
        self.register_model(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("#filter")) == 1
                assert len(d("input[name=name__contains]")) == 1
                rv = c.get("/foo1/user-list?name__contains=%s" % "foo1")
                d = pq(rv.data)
                assert len(d("#list-table-body tr")) == 1

    def test_actions(self):
        class UserModelView(ModelView):
            __customized_actions__ = [action.DeleteAction()]

        self.register_model(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert d("[name=__action__]").val() == "remove"

    def test_action_permission(self):
        class UserModelView(ModelView):
            def get_customized_actions(self, processed_objs=None):
                if not processed_objs:
                    return [action.RedirectAction("test")]
                else:
                    return [action.DeleteAction()]

        self.register_model(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("[name=__action__]")) == 1
                assert d("[name=__action__]").val() == "test"

    def test_uncreateable(self):
        class UserModelView(ModelView):
            def try_create(self):
                raise PermissionDenied

        self.register_model(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("#create-btn")) == 0

    def test_unbatchabled(self):
        class UserModelView(ModelView):
            can_batchly_edit = False

        self.register_model(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("[type=checkbox]")) == 0
                assert len(d("#batch-edit")) == 0

    def test_unbatchabled_2(self):
        class UserModelView(ModelView):
            can_batchly_edit = False
            __customized_actions__ = [action.DeleteAction()]

        self.register_model(UserModelView)
        self.init_db()
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/user-list")
                d = pq(rv.data)
                assert len(d("[type=checkbox]")) == 0
                assert len(d("[type=radio]")) == 2
                assert len(d("#batch-edit")) == 0

    def test_columns(self):
        #TODO
        pass

    def test_sort(self):
        #TODO
        pass

    def test_default_filter(self):
        #TODO
        pass
