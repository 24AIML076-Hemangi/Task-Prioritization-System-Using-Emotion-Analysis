import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity


logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs.txt")


def _parse_line(line):
    # Expected format:
    # [YYYY-MM-DD HH:MM:SS] | USER: user_email | ACTION: description | DETAILS: optional
    try:
        parts = [p.strip() for p in line.split("|")]
        ts_part = parts[0]
        user_part = parts[1] if len(parts) > 1 else ""
        action_part = parts[2] if len(parts) > 2 else ""
        details_part = parts[3] if len(parts) > 3 else ""

        timestamp = ts_part.strip()[1:-1] if ts_part.startswith("[") else ts_part
        user = user_part.replace("USER:", "").strip()
        action = action_part.replace("ACTION:", "").strip()
        details = details_part.replace("DETAILS:", "").strip()

        dt = None
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            dt = None

        return {
            "timestamp": timestamp,
            "user": user,
            "action": action,
            "details": details,
            "raw": line.strip(),
            "_dt": dt,
        }
    except Exception:
        return {
            "timestamp": "",
            "user": "",
            "action": "",
            "details": "",
            "raw": line.strip(),
            "_dt": None,
        }


@logs_bp.route("", methods=["GET"])
@jwt_required()
def get_logs():
    """Return parsed log entries with filters and pagination."""
    current_user = get_jwt_identity()

    # Filters
    user_filter = (request.args.get("user") or "").strip()
    action_filter = (request.args.get("action") or "").strip().lower()
    contains = (request.args.get("contains") or "").strip().lower()
    date_from = (request.args.get("from") or "").strip()
    date_to = (request.args.get("to") or "").strip()

    # Pagination
    try:
        limit = max(1, min(int(request.args.get("limit", "50")), 500))
    except Exception:
        limit = 50
    try:
        offset = max(0, int(request.args.get("offset", "0")))
    except Exception:
        offset = 0

    # Scope control
    scope = (request.args.get("scope") or "self").strip().lower()
    allow_all = os.getenv("ALLOW_LOGS_SCOPE_ALL", "0") == "1"
    if scope != "all" or not allow_all:
        user_filter = user_filter or current_user

    if not os.path.exists(LOG_PATH):
        return jsonify({
            "entries": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "scope": "self" if scope != "all" or not allow_all else "all",
            "log_file": LOG_PATH,
        }), 200

    with open(LOG_PATH, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    entries = [_parse_line(line) for line in lines if line.strip()]

    # Apply filters
    if user_filter:
        entries = [e for e in entries if e["user"] == user_filter]
    if action_filter:
        entries = [e for e in entries if e["action"].lower() == action_filter]
    if contains:
        entries = [e for e in entries if contains in e["raw"].lower()]

    if date_from:
        try:
            from_dt = datetime.fromisoformat(date_from)
            entries = [e for e in entries if e["_dt"] and e["_dt"] >= from_dt]
        except Exception:
            pass
    if date_to:
        try:
            to_dt = datetime.fromisoformat(date_to)
            entries = [e for e in entries if e["_dt"] and e["_dt"] <= to_dt]
        except Exception:
            pass

    total = len(entries)
    sliced = entries[offset: offset + limit]

    for e in sliced:
        e.pop("_dt", None)

    return jsonify({
        "entries": sliced,
        "total": total,
        "limit": limit,
        "offset": offset,
        "scope": "self" if scope != "all" or not allow_all else "all",
        "log_file": LOG_PATH,
    }), 200
