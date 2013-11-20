#-*- coding:utf-8 -*-
import unittest
import flask
from flask.ext.sqlalchemy import SQLAlchemy

app = flask.Flask("test")

db = SQLAlchemy(app)


class ClassModel(db.Model):
    __tablename__ = "TB_CLASSROOM"
    id_ = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, default="test")


class UserModel(db.Model):
    __tablename__ = "TB_USER"
    id_ = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    class_id = db.Column(db.Integer, db.ForeignKey("TB_CLASSROOM.id_"), nullable=False)
    class_ = db.relationship("ClassModel")


class BaseTest(unittest.TestCase):
    _db = db

    def setUp(self):
        self._db.create_all()

    def tearDown(self):
        pass


