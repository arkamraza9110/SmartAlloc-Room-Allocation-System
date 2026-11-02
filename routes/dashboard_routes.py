"""Dashboard statistics and analytics endpoints."""

from collections import Counter

from flask import Blueprint

from models.database import db, serialize
from routes.common import response


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/api/dashboard/stats")
def stats():
    students = db.collection("students")
    rooms = db.collection("rooms")
    seats = db.collection("seats")
    active_students = students.count_documents({"status": {"$ne": "Inactive"}})
    allocated = db.collection("allocations").count_documents({})
    total_seats = seats.count_documents({})
    available_seats = seats.count_documents({"status": "Available", "is_blocked": False})
    accessible_seats = seats.count_documents({"is_accessible": True, "is_blocked": False})
    blocked_seats = seats.count_documents({"$or": [{"is_blocked": True}, {"status": "Blocked"}]})
    latest = db.collection("allocation_runs").find_one(sort=[("created_at", -1)])
    success_rate = round((allocated / active_students) * 100, 1) if active_students else 0
    utilization = round((allocated / total_seats) * 100, 1) if total_seats else 0
    data = {
        "total_students": active_students,
        "total_classes": db.collection("classes").count_documents({}),
        "total_groups": db.collection("groups").count_documents({}),
        "total_rooms": rooms.count_documents({}),
        "total_seats": total_seats,
        "available_seats": available_seats,
        "allocated_students": allocated,
        "unallocated_students": max(0, active_students - allocated),
        "accessible_seats": accessible_seats,
        "blocked_seats": blocked_seats,
        "allocation_success_rate": success_rate,
        "room_utilization": utilization,
        "latest_allocation_run": latest,
        "validation_errors": (latest or {}).get("validation", {}).get("violations", 0),
        "warnings": len(list(db.collection("conflicts").find({"severity": "Warning"}))),
    }
    return response(data=data)


@dashboard_bp.get("/api/dashboard/room-utilization")
def room_utilization():
    rows = []
    for room in db.collection("rooms").find().sort("room_id", 1):
        total = db.collection("seats").count_documents({"room_id": room["room_id"]})
        occupied = db.collection("seats").count_documents({"room_id": room["room_id"], "status": "Occupied"})
        rows.append({"room_id": room["room_id"], "room_name": room["room_name"], "total": total, "occupied": occupied, "utilization": round(occupied / total * 100, 1) if total else 0})
    return response(data=rows)


@dashboard_bp.get("/api/dashboard/group-distribution")
def group_distribution():
    students = list(db.collection("students").find({"status": {"$ne": "Inactive"}}, {"group_id": 1, "department": 1, "class_name": 1, "priority": 1, "accessibility_required": 1}))
    data = {
        "groups": dict(Counter(item.get("group_id", "Unassigned") for item in students)),
        "classes": dict(Counter(item.get("class_name", "Unassigned") for item in students)),
        "departments": dict(Counter(item.get("department", "Unassigned") for item in students)),
        "priority": dict(Counter(item.get("priority", "Normal") for item in students)),
        "accessibility": {"Required": sum(1 for item in students if item.get("accessibility_required")), "Standard": sum(1 for item in students if not item.get("accessibility_required"))},
    }
    return response(data=data)

