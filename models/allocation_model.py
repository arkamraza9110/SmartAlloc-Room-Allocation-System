"""Allocation document helpers."""


def allocation_payload(student: dict, seat: dict, room: dict, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "student_id": student["student_id"],
        "student_name": student["name"],
        "class_name": student.get("class_name", ""),
        "section": student.get("section", ""),
        "semester": student.get("semester", ""),
        "group_id": student.get("group_id", ""),
        "department": student.get("department", ""),
        "priority": student.get("priority", "Normal"),
        "accessibility_required": student.get("accessibility_required", False),
        "room_id": room["room_id"],
        "room_name": room["room_name"],
        "seat_id": seat["seat_id"],
        "seat_label": seat["seat_label"],
        "row_number": seat.get("row_number", 0),
        "column_number": seat.get("column_number", 0),
    }

