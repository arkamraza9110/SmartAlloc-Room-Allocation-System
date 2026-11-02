"""Normalize solver and validation conflicts into user-facing explanations."""


SUGGESTIONS = {
    "capacity": "Add another room, increase room capacity, unblock seats, or select fewer students.",
    "accessibility": "Add accessible seats near doors or lifts, or enable an accessible room.",
    "domain": "Review room availability, blocked seats and accessibility settings.",
    "group-separation": "Add more seats, use another room, or relax the horizontal group rule.",
    "validation": "Review the affected records and regenerate the allocation.",
}


def explain_conflicts(conflicts: list[dict]) -> list[dict]:
    explained = []
    for index, conflict in enumerate(conflicts, start=1):
        item = dict(conflict)
        item["conflict_id"] = item.get("conflict_id", f"C{index:03d}")
        item["suggested_solution"] = item.get("suggested_solution") or SUGGESTIONS.get(
            item.get("category"), "Review the active data and constraints."
        )
        item["severity"] = item.get("severity", "Warning")
        item["affected_students"] = item.get("affected_students", [])
        item["affected_rooms"] = item.get("affected_rooms", [])
        explained.append(item)
    return explained

