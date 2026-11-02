"""Seat or bed document helpers."""


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_seat(payload: dict) -> dict:
    required = ("seat_id", "room_id", "seat_label")
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing required seat fields: {', '.join(missing)}")
    return {
        "seat_id": str(payload["seat_id"]).strip(),
        "room_id": str(payload["room_id"]).strip(),
        "seat_label": str(payload["seat_label"]).strip(),
        "row_number": int(payload.get("row_number", 1)),
        "column_number": int(payload.get("column_number", 1)),
        "is_accessible": _as_bool(payload.get("is_accessible", False)),
        "near_door": _as_bool(payload.get("near_door", False)),
        "near_lift": _as_bool(payload.get("near_lift", False)),
        "is_blocked": _as_bool(payload.get("is_blocked", False)),
        "status": str(payload.get("status", "Available")).strip() or "Available",
        "occupant_id": payload.get("occupant_id"),
    }

