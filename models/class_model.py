"""Class document helpers."""


def normalize_class(payload: dict) -> dict:
    if not str(payload.get("class_id", "")).strip() or not str(payload.get("name", "")).strip():
        raise ValueError("class_id and name are required")
    return {
        "class_id": str(payload["class_id"]).strip(),
        "name": str(payload["name"]).strip(),
        "sections": list(payload.get("sections", [])),
        "semesters": list(payload.get("semesters", [])),
        "department": str(payload.get("department", "")).strip(),
    }

