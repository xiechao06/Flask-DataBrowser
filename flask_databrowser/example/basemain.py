# -*- coding: UTF-8 -*-
from flask import Flask, Blueprint

app = Flask(__name__)

app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"
app.config["DEBUG"] = True
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

from flask.ext.babel import Babel

Babel(app)

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
            log.obj = unicode(obj)
        log.name = unicode(record.name)
        log.level = unicode(record.levelname)
        log.module = unicode(record.module)
        log.func_name = unicode(record.funcName)
        log.line_no = unicode(record.lineno)
        log.thread = unicode(record.thread)
        log.thread_name = unicode(record.threadName)
        log.process = unicode(record.process)
        log.message = unicode(record.msg)
        log.args = unicode(record.args)
        db.session.add(log)
        db.session.commit()


app.logger.addHandler(DBHandler())
