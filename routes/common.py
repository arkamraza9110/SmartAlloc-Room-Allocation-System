"""Shared route helpers."""

from datetime import datetime, timezone

from flask import jsonify, request
from pymongo.errors import DuplicateKeyError

from models.database import serialize


def response(success=True, message="Operation completed successfully", data=None, errors=None, status=200):
    return jsonify({"success": success, "message": message, "data": serialize(data or {}), "errors": errors or []}), status


def payload() -> dict:
    return request.get_json(silent=True) or {}


def now():
    return datetime.now(timezone.utc)


def with_timestamps(document: dict, existing=None) -> dict:
    timestamp = now()
    if existing:
        document["created_at"] = existing.get("created_at", timestamp)
    else:
        document["created_at"] = timestamp
    document["updated_at"] = timestamp
    return document


def handle_db_error(exc: Exception):
    if isinstance(exc, DuplicateKeyError):
        return response(False, "A record with this identifier already exists.", errors=[str(exc)], status=409)
    return response(False, "The operation could not be completed.", errors=[str(exc)], status=500)


def get_page_args():
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    except ValueError:
        page, per_page = 1, 25
    return page, per_page

