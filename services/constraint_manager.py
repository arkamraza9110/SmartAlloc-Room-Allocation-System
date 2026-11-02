"""Pure constraint predicates shared by the solver and validator."""


PRIORITY_RANK = {"Critical": 4, "High": 3, "Normal": 2, "Low": 1}


def same_room(a: dict, b: dict) -> bool:
    return a.get("room_id") == b.get("room_id")


def horizontally_adjacent(a: dict, b: dict) -> bool:
    return same_room(a, b) and a.get("row_number") == b.get("row_number") and abs(
        a.get("column_number", 0) - b.get("column_number", 0)
    ) == 1


def vertically_adjacent(a: dict, b: dict) -> bool:
    return same_room(a, b) and a.get("column_number") == b.get("column_number") and abs(
        a.get("row_number", 0) - b.get("row_number", 0)
    ) == 1


def violates_hard_group_rule(student: dict, candidate_seat: dict, assignments: list[dict]) -> bool:
    return any(
        other.get("group_id") == student.get("group_id")
        and horizontally_adjacent(candidate_seat, other.get("seat", {}))
        for other in assignments
    )


def soft_penalty(student: dict, candidate_seat: dict, assignments: list[dict]) -> int:
    penalty = 0
    for other in assignments:
        other_student = other.get("student", {})
        other_seat = other.get("seat", {})
        if other_student.get("group_id") == student.get("group_id") and vertically_adjacent(
            candidate_seat, other_seat
        ):
            penalty += 4
        if other_student.get("class_name") == student.get("class_name") and other_seat.get(
            "room_id"
        ) == candidate_seat.get("room_id"):
            penalty += 1
    if student.get("accessibility_required") and not (
        candidate_seat.get("near_door") or candidate_seat.get("near_lift")
    ):
        penalty += 2
    return penalty

