# -*- coding: UTF-8 -*-
"""
@author: Yangminghua
@version: $
"""

def main():
    from flask.ext import databrowser
    from flask import Blueprint
    from basemain import app
    from models import User
    accounts_bp = Blueprint("accounts", __name__, static_folder="static", 
                            template_folder="templates")
    browser = databrowser.DataBrowser(app)

    class UserModelView(databrowser.ModelView):

        __list_columns__ = ["name"]

    browser.register_model_view(UserModelView(User), accounts_bp)
    app.register_blueprint(accounts_bp, url_prefix="/accounts")

    app.run(debug=True)


if __name__ == "__main__":
    main()
