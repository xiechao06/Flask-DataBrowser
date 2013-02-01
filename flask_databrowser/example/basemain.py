# -*- coding: UTF-8 -*-
from flask import Flask, Blueprint

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from flask.ext.babel import Babel

Babel(app)


