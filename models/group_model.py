"""Group document helpers."""


def normalize_group(payload: dict) -> dict:
    if not str(payload.get("group_id", "")).strip() or not str(payload.get("name", "")).strip():
        raise ValueError("group_id and name are required")
    return {
        "group_id": str(payload["group_id"]).strip(),
        "name": str(payload["name"]).strip(),
        "class_name": str(payload.get("class_name", "")).strip(),
        "description": str(payload.get("description", "")).strip(),
    }

