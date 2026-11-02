"""Student CRUD, import and export endpoints."""

from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from models.database import db, serialize
from models.student_model import normalize_student
from routes.common import get_page_args, handle_db_error, now, payload, response, with_timestamps
from services.csv_service import csv_response, parse_csv


student_bp = Blueprint("students", __name__)


@student_bp.get("/api/students")
def list_students():
    collection = db.collection("students")
    query = {}
    for field in ("class_name", "section", "group_id", "department", "priority", "status"):
        if request.args.get(field):
            query[field] = request.args[field]
    if request.args.get("accessibility_required") in {"true", "false"}:
        query["accessibility_required"] = request.args["accessibility_required"] == "true"
    search = request.args.get("search", "").strip()
    if search:
        query["$or"] = [
            {"student_id": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    page, per_page = get_page_args()
    total = collection.count_documents(query)
    rows = list(collection.find(query).sort("student_id", 1).skip((page - 1) * per_page).limit(per_page))
    return response(data={"items": serialize(rows), "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page}})


@student_bp.post("/api/students")
def create_student():
    try:
        document = with_timestamps(normalize_student(payload()))
        db.collection("students").insert_one(document)
        return response(message="Student created successfully", data=document, status=201)
    except DuplicateKeyError as exc:
        return handle_db_error(exc)
    except (ValueError, TypeError) as exc:
        return response(False, "Student validation failed", errors=[str(exc)], status=400)
    except Exception as exc:
        return handle_db_error(exc)


@student_bp.get("/api/students/<student_id>")
def get_student(student_id):
    student = db.collection("students").find_one({"student_id": student_id})
    if not student:
        return response(False, "Student not found", status=404)
    return response(data=student)


@student_bp.put("/api/students/<student_id>")
def update_student(student_id):
    collection = db.collection("students")
    existing = collection.find_one({"student_id": student_id})
    if not existing:
        return response(False, "Student not found", status=404)
    try:
        data = payload()
        data["student_id"] = student_id
        document = with_timestamps(normalize_student({**existing, **data}), existing)
        collection.replace_one({"student_id": student_id}, document)
        return response(message="Student updated successfully", data=document)
    except (ValueError, TypeError) as exc:
        return response(False, "Student validation failed", errors=[str(exc)], status=400)
    except Exception as exc:
        return handle_db_error(exc)


@student_bp.delete("/api/students/<student_id>")
def delete_student(student_id):
    result = db.collection("students").delete_one({"student_id": student_id})
    if not result.deleted_count:
        return response(False, "Student not found", status=404)
    db.collection("allocations").delete_many({"student_id": student_id})
    return response(message="Student deleted successfully")


@student_bp.post("/api/students/import-csv")
def import_students():
    file = request.files.get("file")
    if not file:
        return response(False, "Choose a CSV file first", status=400)
    inserted, errors = 0, []
    for row_number, row in enumerate(parse_csv(file), start=2):
        try:
            db.collection("students").insert_one(with_timestamps(normalize_student(row)))
            inserted += 1
        except Exception as exc:
            errors.append({"row": row_number, "error": str(exc)})
    return response(not errors, f"Imported {inserted} students", data={"inserted": inserted, "errors": errors}, status=200 if inserted else 400)


@student_bp.get("/api/students/export-csv")
def export_students():
    rows = [serialize(item) for item in db.collection("students").find().sort("student_id", 1)]
    return csv_response(rows, "smartalloc_students.csv")

