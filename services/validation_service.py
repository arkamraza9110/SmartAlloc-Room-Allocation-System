"""Validation of persisted allocation records against current MongoDB data."""

from services.constraint_manager import horizontally_adjacent, vertically_adjacent


def validate_allocations(students: list[dict], rooms: list[dict], seats: list[dict], allocations: list[dict], classes: list[dict] | None = None, groups: list[dict] | None = None) -> dict:
    student_map = {item["student_id"]: item for item in students}
    room_map = {item["room_id"]: item for item in rooms}
    seat_map = {item["seat_id"]: item for item in seats}
    checks = []
    conflicts = []
    allocated_student_ids = [item.get("student_id") for item in allocations]
    allocated_seat_ids = [item.get("seat_id") for item in allocations]

    def check(name, passed, description, category, affected_students=None, affected_rooms=None, warning=False):
        checks.append({"name": name, "passed": passed, "description": description, "warning": warning})
        if not passed:
            conflicts.append(
                {
                    "category": category,
                    "severity": "Warning" if warning else "Critical",
                    "description": description,
                    "affected_students": affected_students or [],
                    "affected_rooms": affected_rooms or [],
                    "responsible_constraint": name,
                }
            )

    duplicate_students = sorted({sid for sid in allocated_student_ids if allocated_student_ids.count(sid) > 1})
    duplicate_seats = sorted({sid for sid in allocated_seat_ids if allocated_seat_ids.count(sid) > 1})
    missing = sorted(set(student_map) - set(allocated_student_ids))
    check("Every active student is assigned", not missing, f"{len(missing)} students are missing assignments.", "missing", missing)
    check("No duplicate student assignments", not duplicate_students, f"Duplicate student assignments: {', '.join(duplicate_students)}", "duplicate-student", duplicate_students)
    check("No duplicate seat assignments", not duplicate_seats, f"Duplicate seat assignments: {', '.join(duplicate_seats)}", "duplicate-seat", [], [seat_map.get(sid, {}).get("room_id") for sid in duplicate_seats])

    invalid_students = [sid for sid in allocated_student_ids if sid not in student_map]
    invalid_rooms = [item.get("room_id") for item in allocations if item.get("room_id") not in room_map]
    invalid_seats = [item.get("seat_id") for item in allocations if item.get("seat_id") not in seat_map]
    check("Student references are valid", not invalid_students, f"Invalid student IDs: {', '.join(invalid_students)}", "invalid-student", invalid_students)
    check("Room references are valid", not invalid_rooms, f"Invalid room IDs: {', '.join(invalid_rooms)}", "invalid-room", [], invalid_rooms)
    check("Seat references are valid", not invalid_seats, f"Invalid seat IDs: {', '.join(invalid_seats)}", "invalid-seat", [], invalid_rooms)

    room_over_capacity = []
    for room_id, room in room_map.items():
        count = sum(1 for item in allocations if item.get("room_id") == room_id)
        if count > int(room.get("capacity", 0)):
            room_over_capacity.append(room_id)
    check("Room capacity is not exceeded", not room_over_capacity, f"Room capacity exceeded: {', '.join(room_over_capacity)}", "capacity", [], room_over_capacity)

    if classes is not None:
        class_names = {item.get("name") for item in classes}
        invalid_classes = sorted({student.get("student_id") for student in students if student.get("class_name") not in class_names})
        check("Class references are valid", not invalid_classes, f"Students reference unknown classes: {', '.join(invalid_classes)}", "invalid-class", invalid_classes)
    if groups is not None:
        group_ids = {item.get("group_id") for item in groups}
        invalid_groups = sorted({student.get("student_id") for student in students if student.get("group_id") not in group_ids})
        check("Group references are valid", not invalid_groups, f"Students reference unknown groups: {', '.join(invalid_groups)}", "invalid-group", invalid_groups)

    blocked = [item.get("student_id") for item in allocations if seat_map.get(item.get("seat_id"), {}).get("is_blocked")]
    unavailable = [item.get("student_id") for item in allocations if not room_map.get(item.get("room_id"), {}).get("available", False)]
    accessible = [
        item.get("student_id")
        for item in allocations
        if student_map.get(item.get("student_id"), {}).get("accessibility_required")
        and not seat_map.get(item.get("seat_id"), {}).get("is_accessible")
    ]
    check("Blocked seats are unused", not blocked, f"Blocked seats are used by: {', '.join(blocked)}", "blocked-seat", blocked)
    check("Available rooms only", not unavailable, f"Unavailable rooms are used by: {', '.join(unavailable)}", "unavailable-room", unavailable)
    check("Accessibility requirements are met", not accessible, f"Inaccessible assignments: {', '.join(accessible)}", "accessibility", accessible)

    horizontal = []
    vertical = []
    valid_allocations = [item for item in allocations if item.get("student_id") in student_map and item.get("seat_id") in seat_map]
    for index, left in enumerate(valid_allocations):
        for right in valid_allocations[index + 1 :]:
            if student_map[left["student_id"]].get("group_id") != student_map[right["student_id"]].get("group_id"):
                continue
            a, b = seat_map[left["seat_id"]], seat_map[right["seat_id"]]
            if horizontally_adjacent(a, b):
                horizontal.extend([left["student_id"], right["student_id"]])
            if vertically_adjacent(a, b):
                vertical.extend([left["student_id"], right["student_id"]])
    horizontal = sorted(set(horizontal))
    vertical = sorted(set(vertical))
    check("Same-group horizontal adjacency", not horizontal, f"Same-group students sit horizontally adjacent: {', '.join(horizontal)}", "group-separation", horizontal)
    check("Same-group vertical adjacency", not vertical, f"Same-group students sit vertically adjacent: {', '.join(vertical)}", "vertical-adjacency", vertical, warning=True)

    passed = sum(1 for item in checks if item["passed"])
    return {
        "valid": not any(not item["passed"] and not item.get("warning") for item in checks),
        "checks": checks,
        "conflicts": conflicts,
        "summary": {"total": len(checks), "passed": passed, "failed": len(checks) - passed, "violations": len(conflicts)},
    }

