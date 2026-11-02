"""Student document helpers."""

STUDENT_PRIORITIES = ("Critical", "High", "Normal", "Low")


def _as_bool(value) -> bool:
    """Accept JSON booleans and common CSV text values safely."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_student(payload: dict) -> dict:
    required = ("student_id", "name", "class_name", "group_id", "department")
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing required student fields: {', '.join(missing)}")
    priority = payload.get("priority", "Normal")
    if priority not in STUDENT_PRIORITIES:
        raise ValueError("priority must be Critical, High, Normal or Low")
    return {
        "student_id": str(payload["student_id"]).strip(),
        "name": str(payload["name"]).strip(),
        "email": str(payload.get("email", "")).strip(),
        "phone": str(payload.get("phone", "")).strip(),
        "class_name": str(payload["class_name"]).strip(),
        "section": str(payload.get("section", "")).strip(),
        "semester": str(payload.get("semester", "")).strip(),
        "group_id": str(payload["group_id"]).strip(),
        "department": str(payload["department"]).strip(),
        "gender": str(payload.get("gender", "Unspecified")).strip(),
        "accessibility_required": _as_bool(payload.get("accessibility_required", False)),
        "accessibility_type": str(payload.get("accessibility_type", "")).strip(),
        "priority": priority,
        "status": str(payload.get("status", "Active")).strip() or "Active",
        "notes": str(payload.get("notes", "")).strip(),
    }

