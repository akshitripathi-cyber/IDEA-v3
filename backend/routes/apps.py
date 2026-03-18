from flask import Blueprint, jsonify
from utils.api_client import fetch_apps
from utils.memory_store import memory_store

apps_bp = Blueprint("apps", __name__)

@apps_bp.route("/", methods=["GET"])
def get_apps():
    mandatory = memory_store.get("mandatory_data")

    if not mandatory:
        return jsonify({"success": False, "message": "Mandatory data missing"}), 400

    domain = mandatory.get("domain")
    api_key = mandatory.get("api_key")

    if not all([domain, api_key]):
        return jsonify({"success": False, "message": "Domain or API key missing"}), 400

    try:
        apps = fetch_apps(domain, api_key)
        return jsonify({"success": True, "apps": apps}), 200

    except Exception as e:
        print("Error fetching apps:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500
