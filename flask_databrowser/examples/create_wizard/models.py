# -*- coding: UTF-8 -*-
from datetime import datetime
from db import db

class User(db.Model):
    __tablename__ = "TB_USER"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    birthday = db.Column(db.Date, default=datetime.today().date())

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<User %s>" % self.name

