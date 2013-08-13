#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import json
from collections import namedtuple
from flask import Blueprint
from flask.ext.databrowser.test import basetest
from flask.ext.databrowser import ModelView, DataBrowser


class TestObjectAPI(basetest.BaseTest):
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
        super(TestObjectAPI, self).setup()
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

    def test_with_no_form_columns(self):
        model_view = ModelView(self.__tables.User)
        blueprint = Blueprint("foo0", __name__, static_folder="static", template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo0")

        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo0/apis/user/1")
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
                assert field['value'] == 'user1'
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
                assert field['value'] == 1
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
                assert field['value'] == 100
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
                assert field['value'] is None

    def test_batch_edit(self):
        model_view = ModelView(self.__tables.User)
        blueprint = Blueprint("foo1", __name__, static_folder="static",
                              template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo1")

        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo1/apis/user/1,2")

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
                assert field['value'] is None
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
                assert field['value'] == 1
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
                assert field['value'] == 100
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
                assert field['value'] is None

    def test_extra_fields(self):
        class UserModelView(ModelView):
            __extra_fields__ = {
                'old': lambda preprocessed_obj: preprocessed_obj.age > 65
            }

        model_view = UserModelView(self.__tables.User)
        blueprint = Blueprint("foo2", __name__, static_folder="static", template_folder="templates")
        self.browser.register_model_view(model_view, blueprint)
        self.app.register_blueprint(blueprint, url_prefix="/foo2")

        with self.app.test_request_context():
            with self.app.test_client() as c:
                rv = c.get("/foo2/apis/user/1")
                fieldset_list = json.loads(rv.data)["fieldsets"]
                fields = dict((f["name"], f) for f in fieldset_list[0][1])
                assert len(fields) == 4
                assert 'name' in fields
                assert 'group' in fields
                assert 'age' in fields
                assert 'title' in fields

                extra_fields = json.loads(rv.data)['extra_fields']
                assert len(extra_fields) == 1
                assert extra_fields['old'] is True

            with self.app.test_client() as c:
                rv = c.get("/foo2/apis/user/1,2")
                fieldset_list = json.loads(rv.data)["fieldsets"]
                fields = dict((f["name"], f) for f in fieldset_list[0][1])
                assert len(fields) == 4
                assert 'name' in fields
                assert 'group' in fields
                assert 'age' in fields
                assert 'title' in fields

                extra_fields = json.loads(rv.data)['extra_fields']
                assert not extra_fields


if __name__ == "__main__":
    TestObjectAPI().run_plainly()
