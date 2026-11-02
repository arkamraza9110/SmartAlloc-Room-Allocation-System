"""Demo data lifecycle endpoints."""

from flask import Blueprint

from models.database import COLLECTIONS, db
from routes.common import response
from seed import seed_demo_data


demo_bp = Blueprint("demo", __name__)


def ensure_demo_data():
    """Seed only a brand-new database; a deliberate clear-all stays empty."""
    try:
        database = db.connect()
        if database.constraints.find_one({"key": "demo_seeded"}):
            return
        if database.students.count_documents({}) == 0 and database.rooms.count_documents({}) == 0:
            seed_demo_data(reset=False)
    except Exception:
        # The health endpoint remains useful when Atlas credentials are not configured yet.
        return


@demo_bp.post("/api/demo/load")
def load_demo():
    try:
        return response(message="Default data loaded", data=seed_demo_data(reset=False))
    except Exception as exc:
        return response(False, "Could not load default data", errors=[str(exc)], status=500)


@demo_bp.delete("/api/demo/reset")
def reset_demo():
    try:
        return response(message="Demo data reset successfully", data=seed_demo_data(reset=True))
    except Exception as exc:
        return response(False, "Could not reset demo data", errors=[str(exc)], status=500)


@demo_bp.delete("/api/demo/clear")
def clear_all_data():
    try:
        database = db.connect()
        for collection in COLLECTIONS:
            database[collection].delete_many({})
        return response(message="All SmartAlloc data cleared")
    except Exception as exc:
        return response(False, "Could not clear data", errors=[str(exc)], status=500)

