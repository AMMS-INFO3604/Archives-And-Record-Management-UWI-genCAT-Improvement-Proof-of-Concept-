from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_jwt_extended import current_user as jwt_current_user
from flask_jwt_extended import jwt_required

from App.controllers import create_user, get_all_users, get_all_users_json, jwt_required

from .index import index_views

user_views = Blueprint("user_views", __name__, template_folder="../templates")


@user_views.route("/users", methods=["GET"])
def get_user_page():
    users = get_all_users()
    return render_template("users.html", users=users)


@user_views.route("/users", methods=["POST"])
def create_user_action():
    data = request.form
    flash(f"User {data['username']} created!")
    create_user(data["username"], data["password"])
    return redirect(url_for("user_views.get_user_page"))


@user_views.route("/api/users", methods=["GET"])
def get_users_action():
    users = get_all_users_json()
    return jsonify(users)


@user_views.route("/api/users", methods=["POST"])
def create_user_endpoint():
    data = request.json
    user = create_user(data["username"], data["password"])
    return jsonify({"message": f"user {user.username} created with id {user.userID}"})


@user_views.route("/static/users", methods=["GET"])
def static_user_page():
    return send_from_directory("static", "static-user.html")
