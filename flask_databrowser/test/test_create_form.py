#! /usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import namedtuple

from flask import Blueprint
from flask.ext.databrowser.test import basetest
from flask.ext.databrowser import ModelView, DataBrowser

class TestCreate(basetest.BaseTest):

    def setup(self):
        super(TestCreate, self).setup()
        self.browser = DataBrowser(self.app, self.db)
        @self.app.errorhandler(RuntimeError)
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

    def test_permissions(self):
        '''
        when try_create raise exception, can't GET or POST
        '''
        class UserModelView(ModelView):
            
            def try_create(self):
                raise RuntimeError, "can't create"

        model_view = UserModelView(self.__tables.User)
        blueprint = Blueprint("foo1", __name__, static_folder="static", 
                            template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo1")
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
        pass

    def test_simple_create(self):
        # we assert the form generated correctly
        # we assert the submit ok
        pass

    def test_create_in_fieldsets(self):
        pass

    def test_create_in_steps(self):
        pass

    def test_actions(self):
        pass
    
    def test_create_on_fly(self):
        pass

    def test_input_column_spec(self):
        pass

    def test_place_holder_column_spec(self):
        pass

if __name__ == "__main__":
    TestCreate().run_plainly()
