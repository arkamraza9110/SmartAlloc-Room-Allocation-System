"""Room document helpers."""


def _as_bool(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_room(payload: dict) -> dict:
    if not str(payload.get("room_id", "")).strip() or not str(payload.get("room_name", "")).strip():
        raise ValueError("room_id and room_name are required")
    rows = max(1, int(payload.get("rows", 4)))
    columns = max(1, int(payload.get("columns", 5)))
    capacity = max(1, int(payload.get("capacity", rows * columns)))
    return {
        "room_id": str(payload["room_id"]).strip(),
        "room_name": str(payload["room_name"]).strip(),
        "room_type": str(payload.get("room_type", "Examination")).strip(),
        "allocation_mode": str(payload.get("allocation_mode", "Examination Seating")).strip(),
        "floor": str(payload.get("floor", "Ground")).strip(),
        "capacity": capacity,
        "rows": rows,
        "columns": columns,
        "accessible_count": max(0, int(payload.get("accessible_count", 0))),
        "door_position": str(payload.get("door_position", "first-column")).strip(),
        "lift_position": str(payload.get("lift_position", "last-column")).strip(),
        "is_accessible": _as_bool(payload.get("is_accessible", False)),
        "near_lift": _as_bool(payload.get("near_lift", False)),
        "available": _as_bool(payload.get("available", True), default=True),
        "notes": str(payload.get("notes", "")).strip(),
    }

