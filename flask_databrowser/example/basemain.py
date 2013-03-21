# -*- coding: UTF-8 -*-
from flask import Flask, Blueprint

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from flask.ext.babel import Babel

Babel(app)


#-*- coding:utf-8 -*-
from datetime import datetime
import logging
from models import Log


class DBHandler(logging.Handler):
    """
    Handler for logging message to the database table "log"
    """

    def emit(self, record):
        log = Log()
        obj = getattr(record, "obj", None)
        if obj:
            log.obj = repr(obj)
        log.actor = getattr(record, "actor", None)
        log.name = record.name
        log.level = record.levelname
        log.module = record.module
        log.func_name = record.funcName
        log.line_no = record.lineno
        log.thread = record.thread
        log.thread_name = record.threadName
        log.process = record.process
        log.message = record.msg
        log.args = str(record.args)
        db.session.add(log)
        db.session.commit()

app.logger.addHandler(DBHandler())