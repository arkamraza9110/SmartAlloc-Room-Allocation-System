"""MongoDB Atlas connection and shared serialization helpers."""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient

from config import Config


COLLECTIONS = (
    "students",
    "classes",
    "groups",
    "departments",
    "rooms",
    "seats",
    "allocations",
    "allocation_runs",
    "conflicts",
    "constraints",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize(value: Any) -> Any:
    """Convert Mongo/Python values to JSON-safe values recursively."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items() if key != "_id"}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value


class Database:
    def __init__(self) -> None:
        self.client = None
        self.db = None

    def connect(self):
        if self.db is not None:
            return self.db
        if not Config.MONGODB_URI:
            raise RuntimeError("MONGODB_URI is not configured. Add your MongoDB Atlas URI to .env.")
        self.client = MongoClient(
            Config.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
        )
        self.db = self.client[Config.MONGODB_DATABASE]
        self.client.admin.command("ping")
        self.ensure_indexes()
        return self.db

    def ensure_indexes(self) -> None:
        if self.db is None:
            return
        self.db.students.create_index([("student_id", ASCENDING)], unique=True)
        self.db.rooms.create_index([("room_id", ASCENDING)], unique=True)
        self.db.seats.create_index([("seat_id", ASCENDING)], unique=True)
        self.db.classes.create_index([("class_id", ASCENDING)], unique=True)
        self.db.groups.create_index([("group_id", ASCENDING)], unique=True)
        self.db.departments.create_index([("department_id", ASCENDING)], unique=True)
        self.db.students.create_index([("class_name", ASCENDING), ("section", ASCENDING)])
        self.db.students.create_index([("group_id", ASCENDING)])
        self.db.students.create_index([("department", ASCENDING)])
        self.db.students.create_index([("priority", ASCENDING)])
        self.db.rooms.create_index([("available", ASCENDING)])
        self.db.seats.create_index([("room_id", ASCENDING), ("status", ASCENDING)])
        self.db.allocations.create_index([("run_id", ASCENDING)])
        self.db.allocation_runs.create_index([("created_at", ASCENDING)])

    def collection(self, name: str):
        if name not in COLLECTIONS:
            raise ValueError(f"Unknown collection: {name}")
        return self.connect()[name]

    def health(self) -> dict:
        try:
            self.connect()
            return {"connected": True, "database": Config.MONGODB_DATABASE}
        except Exception as exc:  # pragma: no cover - depends on external Atlas state
            return {"connected": False, "database": Config.MONGODB_DATABASE, "error": str(exc)}


db = Database()

