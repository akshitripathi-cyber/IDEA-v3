

from routes import mandatory
from flask import Blueprint, jsonify, send_file, make_response
from utils.memory_store import memory_store
from utils.api_client import fetch_issues, fetch_issues_with_chunking
import csv
import os
from datetime import datetime, timezone
import json
import tempfile
import threading

export_bp = Blueprint("export", __name__)

BASE_HEADERS = [
    "domain","app_publish_id","application-version","application-name","application-identifier","app_id", "id","author_name","author_email","created_at", "changed_at", "platform",
    "message_history", "tag", "title", "device_model", "feedback_comment",
    "feedback_rating", "custom_fields", "os_version", "network_type", "language",
    "carrier_name", "country_code", "status", "assignee"
]


def to_humandate(epochtime):
    try:
        if not epochtime:
            return ""
        return datetime.fromtimestamp(epochtime / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return ""

def split_custom_fields(cf, split_keys):
    """
    Removes selected keys from custom_fields and returns:
    (remaining_json, extracted_values)
    """
    if not isinstance(cf, dict):
        return {}, {}

    remaining = {}
    extracted = {}

    for k, v in cf.items():
        if k in split_keys:
            # unwrap Helpshift typed fields (date, number, etc)
            if isinstance(v, dict) and "value" in v:
                extracted[k] = v["value"]
            else:
                extracted[k] = v
        else:
            remaining[k] = v

    return remaining, extracted


@export_bp.route("/progress", methods=["GET"])
def export_progress():
    """Return current export progress."""
    progress = memory_store.get_progress()
    return jsonify(progress), 200


@export_bp.route("/", methods=["POST"])
def export_csv():

    mandatory = memory_store.get("mandatory_data")
    optional = memory_store.get("optional_data", {})

    meta_columns = optional.get("metadata_columns", [])

    if not mandatory:
        return jsonify({"success": False, "message": "Mandatory data missing"}), 400

    cf_config = optional.get("custom_fields", {})
    cf_split = cf_config.get("split", False)
    cf_columns = cf_config.get("columns", [])

   
    final_headers = BASE_HEADERS.copy()

    if cf_split and cf_columns:
        for key in cf_columns:
            col = f"cif_{key}"
            if col not in final_headers:
                final_headers.append(col)

    # METADATA split columns 
    for key in meta_columns:
        col = f"meta_{key}"
        if col not in final_headers:
            final_headers.append(col)

    try:
        start_dt = datetime.strptime(mandatory["start_datetime"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        end_dt = datetime.strptime(mandatory["end_datetime"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)

        start_ts_ms = start_ts
        end_ts_ms = end_ts

        print("UTC start:", start_dt)
        print("Epoch ms:", start_ts)

    except:
        return jsonify({"success": False, "message": "Invalid date format"}), 400

    api_params = {
        "created-since": start_ts,
        "created-until": end_ts,
        "includes": ["meta", "feedback", "custom_fields", "private_notes", "smart_intents"]

    }

    for k, v in optional.items():
    
        if k in ("custom_fields", "metadata_columns"):
            if k == "custom_fields":
                filters = v.get("filters")
                if filters:
                    api_params["custom_fields"] = filters
            continue
        
        if v in (None, "", [], {}):
            continue
        
        if isinstance(v, dict) and all(not x for x in v.values()):
            continue
        
        api_params[k] = v
    
        if isinstance(v, dict):
            if all(not vals for vals in v.values()):
                continue

        if v in (None, "", [], {}):
            continue

        api_params[k] = v

    all_issues = []

    # Reset and initialize progress tracking
    memory_store.reset_progress()
    
    # Get initial page count to calculate total issues
    initial_params = api_params.copy()
    initial_params["created-since"] = start_ts
    initial_params["created-until"] = end_ts
    
    try:
        initial_response = fetch_issues(mandatory["api_key"], mandatory["domain"], initial_params)
        total_pages = int(initial_response.get("total-pages", 1))
        page_size = int(initial_params.get("page-size", 1000))
        total_issues = total_pages * page_size
        print(f"[Export] Total pages: {total_pages}, Page size: {page_size}, Estimated total: {total_issues} issues")
        memory_store.set_progress(status="fetching", total=total_issues, fetched=0)
    except Exception as e:
        print(f"[Export] Warning: Could not calculate total issues: {e}")
        memory_store.set_progress(status="fetching", total=0, fetched=0)

    # Callback to update progress as issues are fetched
    def update_progress(fetched_count):
        memory_store.set_progress(fetched=fetched_count)

    # Use smart chunking for large date ranges
    try:
        fetch_issues_with_chunking(
            api_key=mandatory["api_key"],
            domain=mandatory["domain"],
            api_params=api_params,
            all_issues=all_issues,
            start_ts_ms=start_ts_ms,
            end_ts_ms=end_ts_ms,
            threshold_pages=50,
            granularity_days=7,
            progress_callback=update_progress
        )
    except Exception as e:
        print(f"Error during chunked fetch: {e}")
        memory_store.set_progress(status="failed", error=str(e))
        return jsonify({"success": False, "message": f"Failed to fetch issues: {str(e)}"}), 500

    if not all_issues:
        return jsonify({"success": False, "message": "No issues found"}), 200

    # write csv
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8")
    tmp_path = tmp.name

    try:
        writer = csv.DictWriter(tmp, fieldnames=final_headers)
        writer.writeheader()

        for issue in all_issues:
            row = {}

            cf = issue.get("custom_fields", {}) or {}

            if cf_split and cf_columns:
                remaining_cf, extracted_cf = split_custom_fields(cf, cf_columns)
            else:
                remaining_cf = cf
                extracted_cf = {}

            for h in BASE_HEADERS:

                if h == "custom_fields":
                    row[h] = "" if not remaining_cf else json.dumps(remaining_cf, ensure_ascii=False)
                    
                elif h == "application-version":
                    row[h] = issue.get("meta", {}).get("application", {}).get("application-version", "")
                
                elif h == "application-name":
                    row[h] = issue.get("meta", {}).get("application", {}).get("application-name", "")
                
                elif h == "application-identifier":
                    row[h] = issue.get("meta", {}).get("application", {}).get("application-identifier", "")

                elif h == "status":
                    row[h] = issue.get("state_data", {}).get("state", "")

                elif h == "tag":
                    row[h] = "; ".join(issue.get("tags", []))

                elif h == "created_at":
                    row[h] = to_humandate(issue.get("created_at"))

                elif h == "changed_at":
                    row[h] = to_humandate(issue.get("state_data", {}).get("changed_at"))

                elif h == "device_model":
                    row[h] = issue.get("meta", {}).get("hardware", {}).get("device-model", "")

                elif h == "os_version":
                    row[h] = issue.get("meta", {}).get("other", {}).get("os-version", "")

                elif h == "network_type":
                    row[h] = issue.get("meta", {}).get("other", {}).get("network-type", "")

                elif h == "carrier_name":
                    row[h] = issue.get("meta", {}).get("other", {}).get("carrier-name", "")

                elif h == "country_code":
                    row[h] = issue.get("meta", {}).get("other", {}).get("country-code", "")

                elif h == "language":
                    row[h] = issue.get("meta", {}).get("other", {}).get("language", "")

                elif h == "platform":
                    try:
                        row[h] = issue.get("meta", {}).get("other", {})["platform"]
                    except:
                        other = issue.get("meta", {}).get("other", {})
                        row[h] = "Webchat" if "browser-version" in other else "Web/Email"

                elif h == "feedback_comment":
                    row[h] = issue.get("feedback_comment", "")

                elif h == "feedback_rating":
                    row[h] = issue.get("feedback_rating", "")

                elif h == "message_history":
                    msgs = issue.get("messages", [])
                    row[h] = " || ".join([f"{m.get('origin')}: {m.get('body')}" for m in msgs])

                elif h == "assignee":
                    row[h] = issue.get("assignee_name", "")

                elif h == "author_name":
                    row[h] = issue.get("author_name", "")

                elif h == "author_email":
                    row[h] = issue.get("author_email", "")
                else:
                    row[h] = issue.get(h, "")

            if cf_split and cf_columns:
                for key in cf_columns:
                    cif_name = f"cif_{key}"
                    val = extracted_cf.get(key, "")
            
                    if isinstance(val, (dict, list)):
                        row[cif_name] = json.dumps(val, ensure_ascii=False)
                    else:
                        row[cif_name] = val
            
            meta = issue.get("meta", {}) or {}
            
            for key in meta_columns:
                col_name = f"meta_{key}"
                val = meta.get(key, "")
            
                if isinstance(val, dict) and "value" in val:
                    row[col_name] = val["value"]
                elif isinstance(val, (dict, list)):
                    row[col_name] = json.dumps(val, ensure_ascii=False)
                else:
                    row[col_name] = val
            
            
            writer.writerow(row)
            

        tmp.close()

        filename = f"issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        resp = make_response(send_file(tmp_path, as_attachment=True, download_name=filename))
        resp.headers["Content-Length"] = str(os.path.getsize(tmp_path))

        threading.Timer(600, lambda: os.remove(tmp_path)).start()
        return resp

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

