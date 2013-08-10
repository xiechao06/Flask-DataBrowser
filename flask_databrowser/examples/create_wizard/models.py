# -*- coding: UTF-8 -*-
from datetime import datetime
from db import db

user_and_group_table = db.Table('TB_ASSOCIATION',
                                db.Column('user_id', db.Integer,
                                          db.ForeignKey('TB_USER.id')),
                                db.Column('group_id', db.Integer,
                                          db.ForeignKey('TB_GROUP.id')))

class User(db.Model):
    __tablename__ = "TB_USER"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    birthday = db.Column(db.Date, default=datetime.today().date())
    group_id = db.Column(db.Integer, db.ForeignKey("TB_GROUP.id"), nullable=False)
    group = db.relationship("Group", backref="users")

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<User %s>" % self.name

class Group(db.Model):
    __tablename__ = "TB_GROUP"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True, doc=u"用户组名称")

    def __unicode__(self):
        return self.name

