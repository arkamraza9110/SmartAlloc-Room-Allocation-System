"""Room CRUD, dynamic resizing and seat generation."""

from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from models.database import db, serialize
from models.room_model import normalize_room
from routes.common import get_page_args, handle_db_error, payload, response, with_timestamps
from services.csv_service import csv_response
from services.room_service import generate_seat_documents


room_bp = Blueprint("rooms", __name__)


@room_bp.get("/api/rooms")
def list_rooms():
    query = {}
    if request.args.get("available") in {"true", "false"}:
        query["available"] = request.args["available"] == "true"
    search = request.args.get("search", "").strip()
    if search:
        query["$or"] = [
            {"room_id": {"$regex": search, "$options": "i"}},
            {"room_name": {"$regex": search, "$options": "i"}},
        ]
    page, per_page = get_page_args()
    collection = db.collection("rooms")
    total = collection.count_documents(query)
    rows = []
    for room in collection.find(query).sort("room_id", 1).skip((page - 1) * per_page).limit(per_page):
        room["seat_count"] = db.collection("seats").count_documents({"room_id": room["room_id"]})
        room["occupied_count"] = db.collection("seats").count_documents({"room_id": room["room_id"], "status": "Occupied"})
        rows.append(room)
    return response(data={"items": serialize(rows), "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page}})


@room_bp.post("/api/rooms")
def create_room():
    try:
        room = with_timestamps(normalize_room(payload()))
        db.collection("rooms").insert_one(room)
        seats = generate_seat_documents(room)
        if seats:
            db.collection("seats").insert_many(seats)
        return response(message="Room created and seats generated", data={"room": room, "seats_created": len(seats)}, status=201)
    except DuplicateKeyError as exc:
        return handle_db_error(exc)
    except (ValueError, TypeError) as exc:
        return response(False, "Room validation failed", errors=[str(exc)], status=400)
    except Exception as exc:
        return handle_db_error(exc)


def _update_room(room_id: str, update_data: dict, message: str):
    collection = db.collection("rooms")
    existing = collection.find_one({"room_id": room_id})
    if not existing:
        return response(False, "Room not found", status=404)
    try:
        update_data["room_id"] = room_id
        room = with_timestamps(normalize_room({**existing, **update_data}), existing)
        collection.replace_one({"room_id": room_id}, room)
        previous_seats = {item["seat_id"]: item for item in db.collection("seats").find({"room_id": room_id})}
        seats = generate_seat_documents(room, previous_seats)
        db.collection("seats").delete_many({"room_id": room_id})
        if seats:
            db.collection("seats").insert_many(seats)
        allocations = db.collection("allocations").count_documents({"room_id": room_id})
        warning = f"{allocations} existing allocations should be validated after resizing." if allocations else None
        return response(message=message, data={"room": room, "seats_generated": len(seats), "warning": warning})
    except DuplicateKeyError as exc:
        return handle_db_error(exc)
    except (ValueError, TypeError) as exc:
        return response(False, "Room validation failed", errors=[str(exc)], status=400)
    except Exception as exc:
        return handle_db_error(exc)


@room_bp.put("/api/rooms/<room_id>")
def update_room(room_id):
    return _update_room(room_id, payload(), "Room updated and seats regenerated")


@room_bp.delete("/api/rooms/<room_id>")
def delete_room(room_id):
    result = db.collection("rooms").delete_one({"room_id": room_id})
    if not result.deleted_count:
        return response(False, "Room not found", status=404)
    db.collection("seats").delete_many({"room_id": room_id})
    db.collection("allocations").delete_many({"room_id": room_id})
    return response(message="Room and its seats deleted successfully")


@room_bp.post("/api/rooms/<room_id>/generate-seats")
def generate_room_seats(room_id):
    room = db.collection("rooms").find_one({"room_id": room_id})
    if not room:
        return response(False, "Room not found", status=404)
    return _update_room(room_id, room, "Seats regenerated successfully")


@room_bp.post("/api/rooms/<room_id>/resize")
def resize_room(room_id):
    return _update_room(room_id, payload(), "Room resized successfully")


@room_bp.get("/api/rooms/export-csv")
def export_rooms():
    return csv_response([serialize(item) for item in db.collection("rooms").find().sort("room_id", 1)], "smartalloc_rooms.csv")

