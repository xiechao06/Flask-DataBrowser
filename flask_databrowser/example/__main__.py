# -*- coding: UTF-8 -*-
"""
@author: Yangminghua
@version: $
"""

def main():
    from flask.ext import databrowser
    from flask import Blueprint

    from basemain import app, db
    from models import User
    accounts_bp = Blueprint("accounts", __name__, static_folder="static", 
                            template_folder="templates")
    browser = databrowser.DataBrowser(app)

    class UserModelView(databrowser.ModelView):

        __list_columns__ = ["name"]


    browser.register_model_view(UserModelView(User,db.session), accounts_bp)
    app.register_blueprint(accounts_bp, url_prefix="/accounts")
    app.config["CSRF_ENABLED"] = False

    app.run(debug=True, port=5001)


if __name__ == "__main__":
    main()
