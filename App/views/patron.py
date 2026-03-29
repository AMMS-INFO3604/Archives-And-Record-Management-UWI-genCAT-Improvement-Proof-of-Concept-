from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from App.controllers import create_user
from App.controllers.patron import get_all_patrons
from App.database import db
from App.models.patron import Patron

patron_views = Blueprint('patron_views', __name__, template_folder='../templates')


# ── GET /api/patrons ───────────────────────────────────────────────────────────
@patron_views.route('/api/patrons', methods=['GET'])
@jwt_required()
def api_get_all_patrons():
    patrons = get_all_patrons()
    return jsonify([
        {
            'patronID': p.patronID,
            'userID':   p.userID,
            'username': p.user.username if p.user else None,
        }
        for p in patrons
    ]), 200


# ── POST /api/patrons ──────────────────────────────────────────────────────────
# Creates a User + Patron in one step.
# Patrons don't log in, so a random internal password is generated.
@patron_views.route('/api/patrons', methods=['POST'])
@jwt_required()
def api_create_patron():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()

    if not username:
        return jsonify({'error': 'username is required'}), 400

    # Check for duplicate username
    from App.models.user import User
    if User.query.filter_by(username=username).first():
        return jsonify({'error': f"Username '{username}' is already taken."}), 409

    # Generate a secure random password — patron never needs to log in
    import secrets
    password = secrets.token_hex(16)

    user = create_user(username, password)
    if not user:
        return jsonify({'error': 'Failed to create user account.'}), 500

    patron = Patron(userID=user.userID)
    db.session.add(patron)
    db.session.commit()

    return jsonify({
        'patronID': patron.patronID,
        'userID':   user.userID,
        'username': user.username,
    }), 201