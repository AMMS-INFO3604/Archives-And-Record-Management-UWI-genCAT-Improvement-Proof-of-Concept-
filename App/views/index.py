from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
)

from App.controllers import create_user, initialize

index_views = Blueprint("index_views", __name__, template_folder="../templates")


@index_views.route("/", methods=["GET"])
def index_page():
    return render_template("index.html")


@index_views.route("/init", methods=["GET"])
def init():
    initialize()
    return jsonify(message="db initialized!")


@index_views.route("/health", methods=["GET"])
@index_views.route("/healthcheck", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})
