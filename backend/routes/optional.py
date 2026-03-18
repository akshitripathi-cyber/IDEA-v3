
from flask import Blueprint, request, jsonify, Response
from utils.memory_store import memory_store
import io
import csv
import json
import requests
from datetime import datetime
from urllib.parse import urlparse

optional_bp = Blueprint("optional", __name__)

@optional_bp.route("/lookup", methods=["POST"])
def lookup_field():
    """
    Simulated dynamic lookup for optional fields.
    """
    data = request.get_json() or {}
    field_name = data.get("field_name")
    if not field_name:
        return jsonify({"success": False, "message": "field_name missing"}), 400

    # Example dynamic values
    DYNAMIC_FIELDS = {
        "app-ids": ["APP001", "APP002", "APP003"],
        "state": ["new", "in-progress", "resolved"],
        "platform-types": ["ios", "android", "web"]
    }
    values = DYNAMIC_FIELDS.get(field_name, [])
    return jsonify({"success": True, "values": values}), 200

def ensure_full_url(url):
    """Ensure the URL has a scheme. Default to https:// if missing."""
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    return url

@optional_bp.route("/", methods=["POST"])
def save_optional():
    """
    Expects JSON from frontend:
    { domain, api_key, other_optional_fields... }
    """
    data = request.get_json()
    

    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    # domain url bnega
    if "domain" in data and data["domain"]:
        data["domain"] = ensure_full_url(data["domain"])

    # Save to memory
    try:
        memory_store.save("optional_data", data)
        print("Optional data saved 😁 :", data)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save optional data: {e}"}), 500

    return jsonify({"success": True, "message": "Optional data saved successfully"}), 200

