# -*- coding: UTF-8 -*-
from datetime import datetime
from basemain import db

user_and_group_table = db.Table('TB_ASSOCIATION',
                                db.Column('user_id', db.Integer,
                                          db.ForeignKey('TB_USER.id')),
                                db.Column('group_id', db.Integer,
                                          db.ForeignKey('TB_GROUP.id')))

class NewObject(object):
    """
    example:
        >> class A(object):
                c = "c"
        >> class B(NewObject):
                a = A()
        >> b= B()
        >> getattr(b, "a.c") # same as b.a.c
        will return "c"
    """
    def __getattr__(self, item):
        return reduce(lambda x, y: x.__getattribute__(y),
                      [self] + item.split("."))

class User(db.Model, NewObject):
    __tablename__ = "TB_USER"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("TB_GROUP.id"))
    group = db.relationship("Group", backref="users")
    create_time = db.Column(db.DateTime, default=datetime.now)
    roll_called = db.Column(db.Boolean, default=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<User %s>" % self.name

    def roll_call(self):
        self.roll_called = True

class Group(db.Model):
    __tablename__ = "TB_GROUP"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)

    def __unicode__(self):
        return u"<Group: %s>" % self.name

    def __repr__(self):
        return unicode(self).encode("utf-8")
