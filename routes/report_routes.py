"""PDF report endpoints."""

from flask import Blueprint, request

from models.database import db
from routes.allocation_routes import allocation_context
from services.pdf_service import build_pdf
from services.validation_service import validate_allocations
from services.conflict_explainer import explain_conflicts


report_bp = Blueprint("reports", __name__)


@report_bp.get("/api/allocation/export/pdf")
def allocation_pdf():
    run_id, allocations, conflicts = allocation_context(request.args.get("run_id"))
    headers = ["Student ID", "Name", "Class", "Group", "Priority", "Room", "Seat", "Accessible"]
    rows = [[item.get("student_id"), item.get("student_name"), item.get("class_name"), item.get("group_id"), item.get("priority"), item.get("room_name"), item.get("seat_label"), "Yes" if item.get("accessibility_required") else "No"] for item in allocations]
    return build_pdf("Allocation Report", rows, headers, f"Run ID: {run_id or 'None'} | Conflicts: {len(conflicts)}")


@report_bp.get("/api/reports/seating-chart/pdf")
def seating_chart_pdf():
    _, allocations, _ = allocation_context(request.args.get("run_id"))
    headers = ["Room", "Seat", "Row", "Column", "Student ID", "Student", "Group", "Accessibility"]
    rows = [[item.get("room_name"), item.get("seat_label"), item.get("row_number"), item.get("column_number"), item.get("student_id"), item.get("student_name"), item.get("group_id"), "Accessible" if item.get("accessibility_required") else "Standard"] for item in allocations]
    return build_pdf("Room-wise Seating Chart", rows, headers, "Print-friendly seating chart with accessibility indicators")


@report_bp.get("/api/reports/validation/pdf")
def validation_pdf():
    _, allocations, _ = allocation_context(request.args.get("run_id"))
    result = validate_allocations(list(db.collection("students").find({"status": {"$ne": "Inactive"}})), list(db.collection("rooms").find()), list(db.collection("seats").find()), allocations, list(db.collection("classes").find()), list(db.collection("groups").find()))
    headers = ["Check", "Status", "Description"]
    rows = [[item["name"], "PASS" if item["passed"] else ("WARN" if item.get("warning") else "FAIL"), item["description"]] for item in result["checks"]]
    return build_pdf("Validation Report", rows, headers, f"Passed {result['summary']['passed']} of {result['summary']['total']} checks")


@report_bp.get("/api/reports/conflicts/pdf")
def conflicts_pdf():
    _, _, conflicts = allocation_context(request.args.get("run_id"))
    conflicts = explain_conflicts(conflicts)
    headers = ["ID", "Category", "Severity", "Description", "Suggested solution"]
    rows = [[item.get("conflict_id"), item.get("category"), item.get("severity"), item.get("description"), item.get("suggested_solution")] for item in conflicts]
    return build_pdf("Conflict Analysis Report", rows, headers, f"Conflicts: {len(conflicts)}")

