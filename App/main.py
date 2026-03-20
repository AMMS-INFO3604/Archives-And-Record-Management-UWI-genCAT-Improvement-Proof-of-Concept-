import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_uploads import DOCUMENTS, IMAGES, TEXT, UploadSet, configure_uploads
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

from App.database import init_db
from App.config import load_config

from App.controllers import (
    setup_jwt,
    add_auth_context
)

from App.views import views, setup_admin



def add_views(app):
    for view in views:
        app.register_blueprint(view)

def create_app(overrides={}):
    app = Flask(__name__, static_url_path='/static')
    load_config(app, overrides)
    CORS(app)
    add_auth_context(app)
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)
    add_views(app)
    init_db(app)
    jwt = setup_jwt(app)
    setup_admin(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith('/api/'):
            return jsonify({"msg": "Token has expired"}), 401
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for('auth_views.staff_login_page'))

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        if request.path.startswith('/api/'):
            return jsonify({"msg": str(error)}), 401
        return redirect(url_for('auth_views.staff_login_page'))

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        if request.path.startswith('/api/'):
            return jsonify({"msg": str(error)}), 401
        return redirect(url_for('auth_views.staff_login_page'))

    app.app_context().push()
    return app