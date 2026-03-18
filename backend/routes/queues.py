from flask import Blueprint, jsonify
from utils.api_client import fetch_queues
from utils.memory_store import memory_store

queues_bp = Blueprint("queues", __name__)

@queues_bp.route("/", methods=["GET"])
def get_queues():
    mandatory = memory_store.get("mandatory_data")

    if not mandatory:
        return jsonify({"success": False, "message": "Mandatory data missing"}), 400

    domain = mandatory.get("domain")
    api_key = mandatory.get("api_key")

    if not all([domain, api_key]):
        return jsonify({"success": False, "message": "Domain or API key missing"}), 400

    try:
        queues = fetch_queues(domain, api_key)
        return jsonify({"success": True, "queues": queues}), 200

    except Exception as e:
        print("Error fetching queues:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500
