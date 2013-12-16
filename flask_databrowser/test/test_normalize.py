#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from collections import namedtuple, OrderedDict
from datetime import datetime
from flask.ext.databrowser.test import basetest
from flask.ext.databrowser import ModelView
from flask.ext.databrowser.col_spec import InputColumnSpec, PlaceHolderColumnSpec, TableColumnSpec


class TestNormalize(basetest.BaseTest):
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

    def test_normalize_create_columns(self):

        # we assert that all create columns are correct created when no
        # create columns defined
        model_view = ModelView(self.__tables.User)

        columns = dict((col_spec.col_name, col_spec) for col_spec in model_view.create_columns[""])
        for column in columns.values():
            assert isinstance(column, InputColumnSpec)

        col_spec = columns["id"]
        assert col_spec.col_name == "id"
        assert col_spec.label is None
        assert col_spec.doc is None
        assert col_spec.property_ == self.__tables.User.id.property

        col_spec = columns["name"]
        assert col_spec.col_name == "name"
        assert col_spec.label is None
        assert col_spec.doc == u"姓名"
        assert col_spec.property_ == self.__tables.User.name.property

        col_spec = columns["group"]
        assert col_spec.col_name == "group"
        assert col_spec.label is None
        assert col_spec.doc is None
        assert col_spec.property_ == self.__tables.User.group.property

        class UserModelView(ModelView):

            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        assert len(model_view.create_columns) == 1
        columns = dict((col_spec.col_name, col_spec) for col_spec in model_view.create_columns[""])
        assert len(columns) == 3

        for column in columns.values():
            assert isinstance(column, InputColumnSpec)

        col_spec = columns["id"]
        assert col_spec.col_name == "id"
        assert col_spec.label == u"号码"
        assert col_spec.doc == u"编号"
        assert col_spec.property_ == self.__tables.User.id.property

        col_spec = columns["name"]
        assert col_spec.col_name == "name"
        assert col_spec.label == u"姓名"
        assert col_spec.doc == u"名称"
        assert col_spec.property_ == self.__tables.User.name.property

        # we assert that the columns not defined in model are purged
        class UserModelView(ModelView):

            __create_columns__ = ["id", PlaceHolderColumnSpec("name", template_fname="foo.html"), "field_inexistent"]
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        assert len(model_view.create_columns) == 1
        col_spec0 = model_view.create_columns[""][0]
        assert col_spec0.col_name == "id"

        # we assert that the create columns will be converted correctly
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == u"号码"
        assert col_spec0.doc == u"编号"
        assert col_spec0.property_ == self.__tables.User.id.property

        # we assert that the input column spec and place holder column spec are 
        # normalized
        class UserModelView(ModelView):

            __create_columns__ = [InputColumnSpec("id"),
                                  PlaceHolderColumnSpec("name", template_fname="foo.html", as_input=True)]
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        columns = dict((col_spec.col_name, col_spec) for col_spec in model_view.create_columns[""])

        col_spec0 = columns["id"]
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == u"号码"
        assert col_spec0.doc == u"编号"
        assert col_spec0.property_ == self.__tables.User.id.property

        col_spec1 = columns["name"]
        assert col_spec1.label == u"姓名"
        assert col_spec1.doc == u"名称"
        assert col_spec1.property_ == self.__tables.User.name.property

        class UserModelView(ModelView):

            __create_columns__ = [InputColumnSpec("id", label="id", doc="identity"),
                                  PlaceHolderColumnSpec("name", label="name", doc="username",
                                                        template_fname="foo.html", as_input=True)]
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        columns = model_view.create_columns[""]

        col_spec0 = columns[0]
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == "id"
        assert col_spec0.doc == "identity"
        assert col_spec0.property_ == self.__tables.User.id.property

        col_spec1 = columns[1]
        assert col_spec1.label == u"name"
        assert col_spec1.doc == u"username"
        assert col_spec1.property_ == self.__tables.User.name.property


        # we assert that the fieldset are kept
        create_columns = OrderedDict()
        create_columns["primary"] = [InputColumnSpec("id")]
        create_columns["secondary"] = [PlaceHolderColumnSpec("name", template_fname="foo.html", as_input=True)]

        class UserModelView(ModelView):

            __create_columns__ = create_columns
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)

        col_spec0 = model_view.create_columns["primary"][0]
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == u"号码"
        assert col_spec0.doc == u"编号"
        assert col_spec0.property_ == self.__tables.User.id.property

        col_spec1 = model_view.create_columns["secondary"][0]
        assert col_spec1.label == u"姓名"
        assert col_spec1.doc == u"名称"
        assert col_spec1.property_ == self.__tables.User.name.property

        # we assert that back reference are removed by default
        model_view = ModelView(self.__tables.Group)
        columns = dict((col.col_name, col) for col in model_view.create_columns[""])
        assert len(columns) == 2

        assert "id" in columns
        assert "name" in columns

    def test_normalize_form_columns(self):

        # we assert that all columns are correct created when no
        # columns defined
        model_view = ModelView(self.__tables.User)

        columns = dict((col_spec.col_name, col_spec) for col_spec in model_view.form_columns[""])
        for column in columns.values():
            assert isinstance(column, InputColumnSpec)

        col_spec = columns["id"]
        assert col_spec.col_name == "id"
        assert col_spec.label is None
        assert col_spec.doc is None
        assert col_spec.property_ == self.__tables.User.id.property

        col_spec = columns["name"]
        assert col_spec.col_name == "name"
        assert col_spec.label is None
        assert col_spec.doc == u"姓名"
        assert col_spec.property_ == self.__tables.User.name.property

        col_spec = columns["group"]
        assert col_spec.col_name == "group"
        assert col_spec.label is None
        assert col_spec.doc is None
        assert col_spec.property_ == self.__tables.User.group.property

        class UserModelView(ModelView):

            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        assert len(model_view.form_columns) == 1
        columns = dict((col_spec.col_name, col_spec) for col_spec in model_view.form_columns[""])
        assert len(columns) == 3

        for column in columns.values():
            assert isinstance(column, InputColumnSpec)

        col_spec = columns["id"]
        assert col_spec.col_name == "id"
        assert col_spec.label == u"号码"
        assert col_spec.doc == u"编号"
        assert col_spec.property_ == self.__tables.User.id.property

        col_spec = columns["name"]
        assert col_spec.col_name == "name"
        assert col_spec.label == u"姓名"
        assert col_spec.doc == u"名称"
        assert col_spec.property_ == self.__tables.User.name.property

        # we assert that the columns not defined in model are purged
        class UserModelView(ModelView):

            __form_columns__ = ["id", PlaceHolderColumnSpec("name", template_fname="foo.html"), "field_inexistent"]
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        assert len(model_view.form_columns) == 1
        col_spec0 = model_view.form_columns[""][0]
        assert col_spec0.col_name == "id"

        # we assert that the columns will be converted correctly
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == u"号码"
        assert col_spec0.doc == u"编号"
        assert col_spec0.property_ == self.__tables.User.id.property

        # we assert that the input column spec and place holder column spec are 
        # normalized
        class UserModelView(ModelView):

            __form_columns__ = [InputColumnSpec("id"),
                                PlaceHolderColumnSpec("name", template_fname="foo.html", as_input=True)]
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        columns = dict((col_spec.col_name, col_spec) for col_spec in model_view.form_columns[""])

        col_spec0 = columns["id"]
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == u"号码"
        assert col_spec0.doc == u"编号"
        assert col_spec0.property_ == self.__tables.User.id.property

        col_spec1 = columns["name"]
        assert col_spec1.label == u"姓名"
        assert col_spec1.doc == u"名称"
        assert col_spec1.property_ == self.__tables.User.name.property

        class UserModelView(ModelView):

            __form_columns__ = [InputColumnSpec("id", label="id", doc="identity"),
                                PlaceHolderColumnSpec("name", label="name", doc="username", template_fname="foo.html",
                                                      as_input=True)]
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)
        columns = model_view.form_columns[""]

        col_spec0 = columns[0]
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == "id"
        assert col_spec0.doc == "identity"
        assert col_spec0.property_ == self.__tables.User.id.property

        col_spec1 = columns[1]
        assert col_spec1.label == u"name"
        assert col_spec1.doc == u"username"
        assert col_spec1.property_ == self.__tables.User.name.property

        # we assert that the fieldset are kept
        form_columns = OrderedDict()
        form_columns["primary"] = [InputColumnSpec("id")]
        form_columns["secondary"] = [PlaceHolderColumnSpec("name", template_fname="foo.html", as_input=True)]

        class UserModelView(ModelView):

            __form_columns__ = form_columns
            __column_labels__ = {"id": u"号码", "name": u"姓名"}
            __column_docs__ = {"id": u"编号", "name": u"名称"}

        model_view = UserModelView(self.__tables.User)

        col_spec0 = model_view.form_columns["primary"][0]
        assert isinstance(col_spec0, InputColumnSpec)
        assert col_spec0.label == u"号码"
        assert col_spec0.doc == u"编号"
        assert col_spec0.property_ == self.__tables.User.id.property

        col_spec1 = model_view.form_columns["secondary"][0]
        assert col_spec1.label == u"姓名"
        assert col_spec1.doc == u"名称"
        assert col_spec1.property_ == self.__tables.User.name.property

        # we assert that back reference are removed by default
        model_view = ModelView(self.__tables.Group)
        columns = dict((col.col_name, col) for col in model_view.form_columns[""])
        assert len(columns) == 2

        assert "id" in columns
        assert "name" in columns

        # we assert that other column specification like TableColumnSpec are reserved
        class GroupModelView(ModelView):

            __form_columns__ = [
                TableColumnSpec("users", css_class="table table-striped table-hover table-condensed table-bordered")]
            __column_labels__ = {'users': u"用户列表"}
            __column_docs__ = {'users': u"所属用户"}
            column_hide_backrefs = False

        model_view = GroupModelView(self.__tables.Group)
        col_spec0 = model_view.form_columns[""][0]
        assert isinstance(col_spec0, TableColumnSpec)
        assert col_spec0.label == u"用户列表"
        assert col_spec0.doc == u"所属用户"


if __name__ == "__main__":
    TestNormalize().run_plainly()
