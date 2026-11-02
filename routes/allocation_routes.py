"""Allocation generation, validation, history and export endpoints."""

import json
from datetime import datetime, timezone

from flask import Blueprint, Response, request

from models.allocation_model import allocation_payload
from models.database import db, serialize
from routes.common import now, payload, response, with_timestamps
from services.conflict_explainer import explain_conflicts
from services.csv_service import csv_response
from services.csp_solver import CSPAllocationSolver
from services.validation_service import validate_allocations


allocation_bp = Blueprint("allocation", __name__)


def latest_run():
    return db.collection("allocation_runs").find_one(sort=[("created_at", -1)])


def allocation_context(run_id=None):
    if not run_id:
        run = latest_run()
        run_id = run.get("run_id") if run else None
    allocations = list(db.collection("allocations").find({"run_id": run_id}).sort("student_id", 1)) if run_id else []
    conflicts = list(db.collection("conflicts").find({"run_id": run_id}).sort("conflict_id", 1)) if run_id else []
    return run_id, allocations, conflicts


@allocation_bp.post("/api/allocation/generate")
def generate_allocation():
    options = payload()
    students = list(db.collection("students").find({"status": {"$ne": "Inactive"}}))
    rooms = list(db.collection("rooms").find({"available": True}))
    room_ids = options.get("room_ids") or []
    if room_ids:
        rooms = [room for room in rooms if room.get("room_id") in room_ids]
    seats = list(db.collection("seats").find({"room_id": {"$in": [room["room_id"] for room in rooms]}})) if rooms else []
    if not students:
        return response(False, "No active students are available for allocation", status=400)

    # A new run starts from a clean current allocation while preserving run history.
    db.collection("allocations").delete_many({})
    db.collection("seats").update_many({"status": "Occupied"}, {"$set": {"status": "Available", "occupant_id": None}})

    solver = CSPAllocationSolver(students, seats, rooms)
    result = solver.solve()
    run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"
    conflicts = explain_conflicts(result.get("conflicts", []))
    run = with_timestamps(
        {
            "run_id": run_id,
            "mode": options.get("mode", "Examination Seating"),
            "success": result["success"],
            "student_count": len(students),
            "allocated_count": len(result.get("assignments", {})),
            "nodes_explored": result.get("nodes", 0),
            "conflict_count": len(conflicts),
        }
    )
    db.collection("allocation_runs").insert_one(run)
    if not result["success"]:
        if conflicts:
            db.collection("conflicts").insert_many([with_timestamps({"run_id": run_id, **conflict}) for conflict in conflicts])
        return response(False, "Allocation failed; review the conflict analysis", data={"run": run, "conflicts": conflicts}, status=422)

    room_map = {room["room_id"]: room for room in rooms}
    student_map = {student["student_id"]: student for student in students}
    seat_map = {seat["seat_id"]: seat for seat in seats}
    allocations = [
        with_timestamps(allocation_payload(student_map[student_id], seat_map[seat_id], room_map[seat_map[seat_id]["room_id"]], run_id))
        for student_id, seat_id in result["assignments"].items()
    ]
    db.collection("allocations").insert_many(allocations)
    for item in allocations:
        db.collection("seats").update_one({"seat_id": item["seat_id"]}, {"$set": {"status": "Occupied", "occupant_id": item["student_id"], "updated_at": now()}})
    return response(
        True,
        "Allocation generated successfully",
        data={"run": run, "allocations": allocations, "conflicts": [], "nodes": result.get("nodes", 0)},
    )


@allocation_bp.get("/api/allocation/latest")
def get_latest_allocation():
    run_id, allocations, conflicts = allocation_context()
    run = db.collection("allocation_runs").find_one({"run_id": run_id}) if run_id else None
    return response(data={"run": run, "allocations": allocations, "conflicts": conflicts})


@allocation_bp.get("/api/allocation/history")
def allocation_history():
    rows = list(db.collection("allocation_runs").find().sort("created_at", -1).limit(50))
    return response(data=rows)


@allocation_bp.post("/api/allocation/validate")
def validate_current_allocation():
    run_id, allocations, _ = allocation_context(payload().get("run_id"))
    students = list(db.collection("students").find({"status": {"$ne": "Inactive"}}))
    rooms = list(db.collection("rooms").find())
    seats = list(db.collection("seats").find())
    result = validate_allocations(students, rooms, seats, allocations, list(db.collection("classes").find()), list(db.collection("groups").find()))
    conflicts = explain_conflicts(result["conflicts"])
    if run_id:
        db.collection("conflicts").delete_many({"run_id": run_id})
        if conflicts:
            db.collection("conflicts").insert_many([with_timestamps({"run_id": run_id, **item}) for item in conflicts])
        db.collection("allocation_runs").update_one({"run_id": run_id}, {"$set": {"validation": result["summary"], "updated_at": now()}})
    return response(result["valid"], "Validation completed", data={**result, "conflicts": conflicts, "run_id": run_id}, status=200)


@allocation_bp.delete("/api/allocation/reset")
def reset_allocation():
    db.collection("allocations").delete_many({})
    db.collection("seats").update_many({"status": "Occupied"}, {"$set": {"status": "Available", "occupant_id": None, "updated_at": now()}})
    return response(message="Current allocation reset; history was preserved")


@allocation_bp.get("/api/allocation/conflicts")
def get_conflicts():
    run_id = request.args.get("run_id")
    if not run_id:
        latest = latest_run()
        run_id = latest.get("run_id") if latest else None
    conflicts = list(db.collection("conflicts").find({"run_id": run_id}).sort("conflict_id", 1)) if run_id else []
    return response(data={"run_id": run_id, "conflicts": conflicts})


@allocation_bp.get("/api/allocation/export/csv")
def export_allocation_csv():
    _, allocations, _ = allocation_context(request.args.get("run_id"))
    return csv_response([serialize(item) for item in allocations], "smartalloc_allocation.csv")


@allocation_bp.get("/api/allocation/export/json")
def export_allocation_json():
    run_id, allocations, conflicts = allocation_context(request.args.get("run_id"))
    data = {"run_id": run_id, "allocations": serialize(allocations), "conflicts": serialize(conflicts)}
    return Response(json.dumps(data, indent=2), mimetype="application/json", headers={"Content-Disposition": "attachment; filename=smartalloc_allocation.json"})

