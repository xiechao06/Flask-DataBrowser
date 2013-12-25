# -*- coding: UTF-8 -*-
from flask import request, jsonify
from werkzeug.security import generate_password_hash


def setup(data_browser):
    @data_browser.blueprint.route('/gen-password/<raw_pwd>')
    def gen_password(raw_pwd):
        method = request.args.get('method')
        return jsonify({'password': generate_password_hash(raw_pwd, method)})
