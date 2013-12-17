#-*- coding:utf-8 -*-
from wtforms import fields, Form
from flask.ext.databrowser.col_spec import InputColumnSpec
from flask.ext.databrowser.sa import SAKolumne
from flask.ext.databrowser.sa_test import BaseTest, ClassModel


class KolumneTest(BaseTest):
    def testInputColumnSpec(self):
        SAKolumne.hidden_pk = False
        input_column = InputColumnSpec("id_", kolumne=SAKolumne(ClassModel.id_, self._db))
        form = type("TestForm", (Form,), {input_column.col_name: input_column.field})
        a_f = form()._fields
        assert len(a_f) == 1
        field = a_f.values()[0]
        assert isinstance(field, fields.IntegerField)

    def testInputColumnSpec2(self):
        obj = ClassModel(id_=123, name="ttttest")
        SAKolumne.hidden_pk = False
        input_column = InputColumnSpec("name", kolumne=SAKolumne(ClassModel.name, self._db), disabled=True)
        form = type("TestForm", (Form,), {input_column.col_name: input_column.field})
        a_f = form(obj=obj)._fields
        assert len(a_f) == 1
        field = a_f.values()[0]
        assert isinstance(field, fields.StringField)
        assert field.default == "test"
        assert field._value() == obj.name

    def testGrouperColumnSpec(self):
        obj = ClassModel(id_=123, name="tadsf")
        SAKolumne.hidden_pk = False
        input_column = InputColumnSpec("")