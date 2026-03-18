
from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

USER = {"username": "admin", "password": "Helpshift@2026"}

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if username == USER["username"] and password == USER["password"]:
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401
