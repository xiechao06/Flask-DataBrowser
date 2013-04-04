# -*- coding: UTF-8 -*-
from datetime import datetime
from basemain import db

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
    group_id = db.Column(db.Integer, db.ForeignKey("TB_GROUP.id"))
    group = db.relationship("Group", backref="users")
    create_time = db.Column(db.DateTime, default=datetime.now, doc=u"创建于")
    roll_called = db.Column(db.Boolean, default=False)
    age = db.Column(db.Integer)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<User %s>" % self.name

    def roll_call(self):
        self.roll_called = True

    @property
    def good(self):
        return (self.id & 1) == 0

    @property
    def avatar(self):
        return "%d.jpg" % self.id

    @property
    def dogs(self):
        from collections import namedtuple
        Dog = namedtuple("Dog", ["name", "color", "age"])
        a = Dog("a", "red", 1)
        b = Dog("b", "black", 2)
        c = Dog("c", "white", 3)
        return [a, b, c]

class Group(db.Model):
    __tablename__ = "TB_GROUP"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True, doc=u"用户组名称")

    def __unicode__(self):
        return u"<Group: %s>" % self.name

    def __repr__(self):
        return unicode(self).encode("utf-8")

class Car(db.Model):
    __tablename__ = "TB_CAR"

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(32))
    owner_id = db.Column(db.Integer, db.ForeignKey("TB_USER.id"))
    owner = db.relationship(User, backref="car_list")

class Log(db.Model):

    __tablename__ = "TB_LOG"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    level = db.Column(db.String)
    module = db.Column(db.String)
    func_name = db.Column(db.String)
    line_no = db.Column(db.Integer)
    thread = db.Column(db.Integer)
    thread_name = db.Column(db.String)
    process = db.Column(db.Integer)
    message = db.Column(db.String)
    args = db.Column(db.String)
    obj = db.Column(db.String(256))
    action = db.Column(db.String(256))
    extra = db.Column(db.String(256))
    create_time = db.Column(db.DateTime, default=datetime.now)
