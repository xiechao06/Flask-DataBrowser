# -*- coding: UTF-8 -*-
"""
SYNOPSIS
    python basemain.py [options]
OPTIONS
    -h 
        show this help
    -p  <port>
        the port of server runs on
    -s  <host>
        the ip of the server runs on
"""
import sys
from getopt import getopt
from flask import Flask, Blueprint, redirect
from flask.ext import databrowser
from collections import OrderedDict
from flask.ext.login import LoginManager
from flask.ext.principal import PermissionDenied
from flask.ext.databrowser.action import DeleteAction

app = Flask(__name__)
LoginManager(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"
app.config['SQLALCHEMY_ECHO'] = False
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "JHdkj1;"
app.config["CSRF_ENABLED"] = False

from flask.ext.babel import Babel
Babel(app)

from flask.ext.databrowser.col_spec import PlaceHolderColumnSpec


class UserModelView(databrowser.ModelView):

    can_create = True
    create_in_steps = True
    __customized_actions__ = [DeleteAction()]
    __create_columns__ = OrderedDict()
    __create_columns__[u'设置群组'] = ["group"]
    __create_columns__[u"取名"] = ["name"]
    __create_columns__[u"设置密码"] = [PlaceHolderColumnSpec('password', template_fname='/accounts/password-snippet.html', as_input=True)]
    __create_columns__[u'设置生日'] = ['birthday']

    __column_labels__ = {'name': u'用户名', 'group': u'用户组'}

accounts_bp = Blueprint("accounts", __name__, static_folder="static", 
                        template_folder="templates")

@app.route("/")
def index():
    return redirect(user_model_view.url_for_list())

if __name__ == "__main__":

    opts, _ = getopt(sys.argv[1:], "hp:s:")
    for o, v in opts:
        if o == '-h':
            print __doc__
            sys.exit(0)
        elif o == '-p':
            port = v 
        elif o == '-s':
            host = v
        else:
            print 'unkown option: ' + v
            print __doc__
            sys.exit(-1)
        
    try:
        port
    except NameError:
        port = 5000

    try:
        host
    except NameError:
        host = '0.0.0.0'

    from models import User
    from db import db

    data_browser = databrowser.DataBrowser(app, db, page_size=4)
    user_model_view = UserModelView(User, u"用户")
    data_browser.register_model_view(user_model_view, accounts_bp)

    app.register_blueprint(accounts_bp, url_prefix="/accounts")
    app.run(port=port, host = host)
