#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import json
from collections import namedtuple, OrderedDict
from wtforms import validators
from flask import Flask, Blueprint, url_for
from flask.ext.databrowser.sa import SAModell
from flask.ext.databrowser.test import basetest
from flask.ext.databrowser import ModelView, DataBrowser
from flask.ext.databrowser.col_spec import InputColumnSpec


class TestCreateAPI(basetest.BaseTest):
    def setup_models(self):
        db = self.db

        class Group(db.Model):
            __tablename__ = "TB_GROUP"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(32), nullable=False, unique=True, doc=u"用户组名称")

            def __unicode__(self):
                return self.name


        class User(db.Model):
            __tablename__ = "TB_USER"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(32), nullable=False, unique=True, doc=u"姓名")
            title = db.Column(db.Enum("Ms", "Mr", "Mrs"))
            group_id = db.Column(db.Integer, db.ForeignKey("TB_GROUP.id"), default=1, nullable=False)
            group = db.relationship("Group", backref="users")
            age = db.Column(db.Integer, default=100)

            def __unicode__(self):
                return self.name

        self.__tables = namedtuple("foo", ["User", "Group"])(User, Group)

    def setup(self):
        super(TestCreateAPI, self).setup()
        self.browser = DataBrowser(self.app, self.db)
        group1 = self.__tables.Group(name="group1")
        group2 = self.__tables.Group(name="group2")
        self.db.session.add(group1)
        self.db.session.add(group2)
        user1 = self.__tables.User(name='user1')
        user2 = self.__tables.User(name='user2')
        self.db.session.add(user1)
        self.db.session.add(user2)
        self.db.session.commit()

    def test_with_no_create_columns(self):
        # we assert when no create columns are defined, creat api return correctly
        model_view = ModelView(SAModell(self.__tables.User, self.db))
        blueprint = Blueprint("foo0", __name__, static_folder="static", template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo0")

        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo0/apis/user")
                fieldset_list = json.loads(rv.data)["fieldsets"]
                fields = dict((f["name"], f) for f in fieldset_list[0][1])
                assert len(fields) == 4
                assert 'name' in fields
                assert 'group' in fields
                assert 'age' in fields
                assert 'title' in fields

                field = fields['name']
                assert field['type'] == 'string'
                assert field['label'] is None
                assert field['doc'] == u'姓名'
                assert not field['read_only']
                assert field['default'] is None
                assert field['group_by'] is None
                assert len(field['validators']) == 2
                validator_map = dict((v['name'], v) for v in field['validators'])
                assert 'length' in validator_map
                assert 'required' in validator_map
                validator = validator_map['length']
                assert validator['max'] == 32

                field = fields['group']
                assert field['type'] == 'select'
                assert field['label'] is None
                assert field['doc'] is None
                assert field['default'] == 1
                assert not field['read_only']
                assert field['group_by'] is None
                assert len(field['validators']) == 1
                assert field['validators'][0]['name'] == 'required'
                assert len(field['options']) == 2
                options = dict(field['options'])
                assert options[1] == 'group1'
                assert options[2] == 'group2'

                field = fields['age']
                assert field['type'] == 'integer'
                assert field['label'] is None
                assert field['doc'] is None
                assert not field['read_only']
                assert field['group_by'] is None
                assert not field['validators']

                field = fields['title']
                assert field['type'] == 'select'
                assert field['label'] is None
                assert field['doc'] is None
                assert not field['read_only']
                assert field['group_by'] is None
                assert len(field['validators']) == 1
                assert field['validators'][0]['name'] == 'anyof'
                assert len(field['options']) == 3
                options = dict(field['options'])
                assert options['Ms'] == 'Ms'
                assert options['Mr'] == 'Mr'
                assert options['Mrs'] == 'Mrs'

    def test_not_hidden_pk(self):
        ## we assert primary key isn't hidden when we meant to
        class UserModelView(ModelView):
            hidden_pk = False

        model_view = UserModelView(self.__tables.User)
        blueprint = Blueprint("foo1", __name__, static_folder="static",
                              template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo1")

        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/apis/user")
                fieldset_list = json.loads(rv.data)["fieldsets"]
                fields = dict((f["name"], f) for f in fieldset_list[0][1])
                assert len(fields) == 5
                assert 'id' in fields
                assert 'name' in fields
                assert 'group' in fields
                assert 'age' in fields

    def test_many_to_one(self):
        ## we test many to one relationship
        class GroupModelView(ModelView):
            column_hide_backrefs = False

        model_view = GroupModelView(self.__tables.Group)
        blueprint = Blueprint("foo2", __name__, static_folder="static",
                              template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo2")
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo2/apis/group")
                fieldset_list = json.loads(rv.data)["fieldsets"]
                fields = dict((f["name"], f) for f in fieldset_list[0][1])
                assert len(fields) == 2
                assert 'name' in fields
                assert 'users' in fields

                field = fields['users']
                assert field['type'] == 'select'
                assert len(field['options']) == 2
                options = dict(field['options'])
                assert options[1] == 'user1'
                assert options[2] == 'user2'

    def test_extra_validators(self):
        class UserModelView(ModelView):
            __create_columns__ = [InputColumnSpec("age", validators=[validators.NumberRange(18, 101)])]

        model_view = UserModelView(self.__tables.User)
        blueprint = Blueprint("foo3", __name__, static_folder="static",
                              template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo3")
        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo3/apis/user")
                fieldset_list = json.loads(rv.data)["fieldsets"]
                fields = dict((f["name"], f) for f in fieldset_list[0][1])
                assert len(fields) == 1
                assert 'age' in fields

                field = fields['age']
                assert field['type'] == 'integer'
                assert len(field['validators']) == 1
                validator = field['validators'][0]
                assert validator['name'] == 'range'
                assert validator['min'] == 18
                assert validator['max'] == 101

                # TODO more validators should be tested here


    def test_many_to_many(self):
        # TODO untested
        pass

    def test_commit(self):
        class UserModelView(ModelView):
            __create_columns__ = ['name', 'title', 'group',
                                  InputColumnSpec("age", validators=[validators.NumberRange(18, 101)])]

        model_view = UserModelView(self.__tables.User)
        blueprint = Blueprint("foo5", __name__, static_folder="static",
                              template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo5")
        with self.app.test_request_context():
            with self.app.test_client() as c:
                data = {
                    "name": "foo",
                    "title": "Mr",
                    "group": '1',
                    "age": 22,
                }
                headers = [('Content-Type', 'application/json')]
                rv = c.post("/foo5/apis/user", content_type='application/json', data=json.dumps(data))
                assert rv.status_code == 200
                rsp = json.loads(rv.data)
                assert rsp['repr'] == 'foo'
                data = {
                    "name": 'foo',
                    'title': 'Mr',
                    'group': '3',
                    'age': 1
                }
                rv = c.post("/foo5/apis/user", content_type='application/json', data=json.dumps(data))
                assert rv.status_code == 403
                rsp = json.loads(rv.data)
                assert len(rsp['errors']) == 3
                print rsp
                assert 'name' in rsp['errors']
                assert 'group' in rsp['errors']
                assert 'age' in rsp['errors']

        self.db.session.delete(self.__tables.User.query.filter(self.__tables.User.name == 'foo').one())
        self.db.session.commit()


if __name__ == "__main__":
    TestCreateAPI().run_plainly()
