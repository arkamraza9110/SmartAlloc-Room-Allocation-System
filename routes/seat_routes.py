"""Seat and bed management endpoints."""

from flask import Blueprint, request

from models.database import db, serialize
from routes.common import handle_db_error, payload, response, with_timestamps
from services.csv_service import csv_response


seat_bp = Blueprint("seats", __name__)


@seat_bp.get("/api/seats")
def list_seats():
    query = {}
    for field in ("room_id", "status"):
        if request.args.get(field):
            query[field] = request.args[field]
    if request.args.get("accessible") in {"true", "false"}:
        query["is_accessible"] = request.args["accessible"] == "true"
    rows = list(db.collection("seats").find(query).sort([("room_id", 1), ("row_number", 1), ("column_number", 1)]))
    return response(data=serialize(rows))


@seat_bp.get("/api/rooms/<room_id>/seats")
def list_room_seats(room_id):
    rows = list(db.collection("seats").find({"room_id": room_id}).sort([("row_number", 1), ("column_number", 1)]))
    return response(data=serialize(rows))


@seat_bp.put("/api/seats/<seat_id>")
def update_seat(seat_id):
    collection = db.collection("seats")
    existing = collection.find_one({"seat_id": seat_id})
    if not existing:
        return response(False, "Seat or bed not found", status=404)
    allowed = {"is_accessible", "near_door", "near_lift", "is_blocked", "status", "occupant_id"}
    changes = {key: value for key, value in payload().items() if key in allowed}
    if changes.get("is_blocked"):
        changes["status"] = "Blocked"
        changes["occupant_id"] = None
    elif existing.get("status") == "Blocked" and changes.get("is_blocked") is False:
        changes["status"] = "Available"
    changes["updated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    try:
        collection.update_one({"seat_id": seat_id}, {"$set": changes})
        return response(message="Seat updated successfully", data=collection.find_one({"seat_id": seat_id}))
    except Exception as exc:
        return handle_db_error(exc)


@seat_bp.get("/api/seats/export-csv")
def export_seats():
    return csv_response([serialize(item) for item in db.collection("seats").find().sort("seat_id", 1)], "smartalloc_seats.csv")

