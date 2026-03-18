from flask import Blueprint, request, jsonify
from utils.memory_store import memory_store

mandatory_bp = Blueprint("mandatory", __name__)

@mandatory_bp.route("/", methods=["POST"])
def save_mandatory():
    """
    Expects JSON from frontend:
    { domain, api_key, sdate, edate, download_path }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    memory_store.save("mandatory_data", data)
    return jsonify({"success": True, "message": "Mandatory data saved successfully"}), 200
