"""Group management endpoints."""

from flask import Blueprint
from pymongo.errors import DuplicateKeyError

from models.database import db, serialize
from models.group_model import normalize_group
from routes.common import handle_db_error, payload, response, with_timestamps


group_bp = Blueprint("groups", __name__)


@group_bp.get("/api/groups")
def list_groups():
    groups = []
    students = db.collection("students")
    for item in db.collection("groups").find().sort("group_id", 1):
        item["student_count"] = students.count_documents({"group_id": item.get("group_id")})
        groups.append(item)
    return response(data=groups)


@group_bp.post("/api/groups")
def create_group():
    try:
        document = with_timestamps(normalize_group(payload()))
        db.collection("groups").insert_one(document)
        return response(message="Group created successfully", data=document, status=201)
    except DuplicateKeyError as exc:
        return handle_db_error(exc)
    except (ValueError, TypeError) as exc:
        return response(False, "Group validation failed", errors=[str(exc)], status=400)


@group_bp.put("/api/groups/<group_id>")
def update_group(group_id):
    collection = db.collection("groups")
    existing = collection.find_one({"group_id": group_id})
    if not existing:
        return response(False, "Group not found", status=404)
    try:
        data = payload()
        data["group_id"] = group_id
        document = with_timestamps(normalize_group({**existing, **data}), existing)
        collection.replace_one({"group_id": group_id}, document)
        return response(message="Group updated successfully", data=document)
    except Exception as exc:
        return handle_db_error(exc)


@group_bp.delete("/api/groups/<group_id>")
def delete_group(group_id):
    result = db.collection("groups").delete_one({"group_id": group_id})
    if not result.deleted_count:
        return response(False, "Group not found", status=404)
    return response(message="Group deleted successfully")

