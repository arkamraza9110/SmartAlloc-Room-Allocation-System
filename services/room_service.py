"""Dynamic room geometry and seat generation."""

from models.database import utc_now


def generate_seat_documents(room: dict, preserve: dict | None = None) -> list[dict]:
    preserve = preserve or {}
    rows = max(1, int(room.get("rows", 1)))
    columns = max(1, int(room.get("columns", 1)))
    capacity = min(max(1, int(room.get("capacity", rows * columns))), rows * columns)
    accessible_count = min(max(0, int(room.get("accessible_count", 0))), capacity)
    documents = []
    for index in range(capacity):
        row = index // columns + 1
        column = index % columns + 1
        seat_id = f"{room['room_id']}-S{row:02d}{column:02d}"
        label = f"R{row}-C{column}"
        old = preserve.get(seat_id, {})
        near_door = column == 1 if room.get("door_position", "first-column") == "first-column" else column == columns
        near_lift = column == 1 if room.get("lift_position", "last-column") == "first-column" else column == columns
        # Room geometry is authoritative after a resize. Preserve only
        # user-controlled state while recalculating accessibility markers.
        is_accessible = index < accessible_count
        documents.append(
            {
                "seat_id": seat_id,
                "room_id": room["room_id"],
                "seat_label": label,
                "row_number": row,
                "column_number": column,
                "is_accessible": bool(is_accessible),
                "near_door": bool(old.get("near_door", near_door)),
                "near_lift": bool(old.get("near_lift", near_lift)),
                "is_blocked": bool(old.get("is_blocked", False)),
                "status": old.get("status", "Available"),
                "occupant_id": old.get("occupant_id"),
                "created_at": old.get("created_at", utc_now()),
                "updated_at": utc_now(),
            }
        )
    return documents

