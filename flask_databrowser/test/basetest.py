# -*- coding: UTF-8 -*-
import types
import tempfile
import os
from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel
from flask.ext.login import LoginManager

class BaseTest(object):
    def setup(self):
        self.config()

        self.db_fd, self.db_fname = tempfile.mkstemp()
        os.close(self.db_fd)
        dbstr = "sqlite:///" + self.db_fname + ".db"

        self.app = Flask(__name__)
        Babel(self.app)
        LoginManager(self.app)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = dbstr
        self.app.config["CSRF_ENABLED"] = False
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app.config["SECRET_KEY"] = "D8123;d;"
        self.db = SQLAlchemy(self.app)
        self.setup_models()
        self.db.create_all()
        try:
            self.db.init_app(self.app)
        except:
            # 第二次执行init_app时，由于app已经执行过request，将导致app无法再次初始化。
            pass
        self.prepare_data()

    def teardown(self):
        self.db.drop_all()
        os.unlink(self.db_fname)

    def prepare_data(self):
        pass

    def config(self):
        self.ECHO_DB = False

    def setup_models(self):
        """
        all the sub classes should setup models here
        """
        pass

    def run_plainly(self, tests=None):
        self.setup()
        for k, v in self.__class__.__dict__.items():
            if k.startswith("test") and isinstance(v, types.FunctionType):
                if not tests or (k in tests):
                    v(self)
        self.teardown()
