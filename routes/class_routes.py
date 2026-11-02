"""Class and department endpoints."""

from flask import Blueprint
from pymongo.errors import DuplicateKeyError

from models.database import db, serialize
from models.class_model import normalize_class
from routes.common import handle_db_error, now, payload, response, with_timestamps


class_bp = Blueprint("classes", __name__)


@class_bp.get("/api/classes")
def list_classes():
    classes = []
    student_collection = db.collection("students")
    for item in db.collection("classes").find().sort("name", 1):
        item["student_count"] = student_collection.count_documents({"class_name": item.get("name")})
        classes.append(item)
    return response(data=classes)


@class_bp.post("/api/classes")
def create_class():
    try:
        document = with_timestamps(normalize_class(payload()))
        db.collection("classes").insert_one(document)
        return response(message="Class created successfully", data=document, status=201)
    except DuplicateKeyError as exc:
        return handle_db_error(exc)
    except (ValueError, TypeError) as exc:
        return response(False, "Class validation failed", errors=[str(exc)], status=400)


@class_bp.put("/api/classes/<class_id>")
def update_class(class_id):
    collection = db.collection("classes")
    existing = collection.find_one({"class_id": class_id})
    if not existing:
        return response(False, "Class not found", status=404)
    try:
        data = payload()
        data["class_id"] = class_id
        document = with_timestamps(normalize_class({**existing, **data}), existing)
        collection.replace_one({"class_id": class_id}, document)
        return response(message="Class updated successfully", data=document)
    except Exception as exc:
        return handle_db_error(exc)


@class_bp.delete("/api/classes/<class_id>")
def delete_class(class_id):
    result = db.collection("classes").delete_one({"class_id": class_id})
    if not result.deleted_count:
        return response(False, "Class not found", status=404)
    return response(message="Class deleted successfully")


@class_bp.get("/api/departments")
def list_departments():
    return response(data=serialize(list(db.collection("departments").find().sort("name", 1))))

