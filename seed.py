"""Seed SmartAlloc with realistic demo data.

Run from the project directory with: python seed.py
"""

from datetime import datetime, timezone

from models.database import COLLECTIONS, db
from models.student_model import normalize_student
from models.room_model import normalize_room
from services.room_service import generate_seat_documents


def demo_documents():
    departments = [
        {"department_id": "CSE", "name": "Computer Science & Engineering"},
        {"department_id": "ECE", "name": "Electronics & Communication"},
        {"department_id": "BBA", "name": "Business Administration"},
    ]
    classes = [
        {"class_id": "CSE-BTECH", "name": "B.Tech CSE", "sections": ["A", "B"], "semesters": ["4", "6"], "department": "CSE"},
        {"class_id": "ECE-BTECH", "name": "B.Tech ECE", "sections": ["A"], "semesters": ["4"], "department": "ECE"},
        {"class_id": "BBA-MGMT", "name": "BBA Management", "sections": ["A"], "semesters": ["2"], "department": "BBA"},
    ]
    groups = [
        {"group_id": "G1", "name": "CSE Alpha", "class_name": "B.Tech CSE"},
        {"group_id": "G2", "name": "CSE Beta", "class_name": "B.Tech CSE"},
        {"group_id": "G3", "name": "ECE Alpha", "class_name": "B.Tech ECE"},
        {"group_id": "G4", "name": "BBA Alpha", "class_name": "BBA Management"},
    ]
    rooms = [
        normalize_room({"room_id": "R101", "room_name": "Innovation Hall", "room_type": "Examination", "allocation_mode": "Examination Seating", "floor": "Ground", "capacity": 20, "rows": 4, "columns": 5, "accessible_count": 4, "is_accessible": True, "near_lift": True, "door_position": "first-column", "lift_position": "last-column", "available": True}),
        normalize_room({"room_id": "R102", "room_name": "Seminar Room", "room_type": "Examination", "allocation_mode": "Examination Seating", "floor": "Ground", "capacity": 15, "rows": 3, "columns": 5, "accessible_count": 3, "is_accessible": True, "near_lift": False, "door_position": "last-column", "lift_position": "first-column", "available": True}),
        normalize_room({"room_id": "R201", "room_name": "Hostel Block A", "room_type": "Hostel", "allocation_mode": "Hostel Room/Bed", "floor": "2", "capacity": 12, "rows": 3, "columns": 4, "accessible_count": 2, "is_accessible": True, "near_lift": True, "door_position": "first-column", "lift_position": "first-column", "available": True}),
    ]
    students = []
    specs = [
        ("CSE", "B.Tech CSE", "A", "6", "G1", "Critical", False),
        ("CSE", "B.Tech CSE", "A", "6", "G2", "High", False),
        ("ECE", "B.Tech ECE", "A", "4", "G3", "Normal", False),
        ("BBA", "BBA Management", "A", "2", "G4", "Low", False),
    ]
    for index in range(20):
        department, class_name, section, semester, group_id, priority, access = specs[index % len(specs)]
        if index in {3, 11, 16}:
            access = True
            priority = "High" if index != 16 else "Critical"
        students.append(
            normalize_student(
                {
                    "student_id": f"ST{index + 1:03d}",
                    "name": ["Aarav Sharma", "Diya Kapoor", "Kabir Singh", "Meera Joshi", "Riya Verma", "Arjun Mehta"][index % 6] + f" {index + 1}",
                    "email": f"student{index + 1}@smartalloc.demo",
                    "phone": f"987650{index:04d}",
                    "class_name": class_name,
                    "section": section,
                    "semester": semester,
                    "group_id": group_id,
                    "department": department,
                    "gender": "Unspecified",
                    "accessibility_required": access,
                    "accessibility_type": "Wheelchair access" if access else "",
                    "priority": priority,
                    "status": "Active",
                    "notes": "Demo record",
                }
            )
        )
    return departments, classes, groups, rooms, students


def seed_demo_data(reset=False):
    database = db.connect()
    if reset:
        for collection in COLLECTIONS:
            database[collection].delete_many({})
    if not reset and database.students.count_documents({}) > 0:
        return {"seeded": False, "message": "Existing student data was preserved."}
    timestamp = datetime.now(timezone.utc)
    departments, classes, groups, rooms, students = demo_documents()
    database.departments.insert_many([{**item, "created_at": timestamp, "updated_at": timestamp} for item in departments])
    database.classes.insert_many([{**item, "created_at": timestamp, "updated_at": timestamp} for item in classes])
    database.groups.insert_many([{**item, "created_at": timestamp, "updated_at": timestamp} for item in groups])
    database.students.insert_many([{**item, "created_at": timestamp, "updated_at": timestamp} for item in students])
    for room in rooms:
        room["created_at"] = timestamp
        room["updated_at"] = timestamp
        database.rooms.insert_one(room)
        database.seats.insert_many(generate_seat_documents(room))
    database.constraints.insert_one({"key": "demo_seeded", "value": True, "created_at": timestamp, "updated_at": timestamp})
    return {"seeded": True, "students": len(students), "rooms": len(rooms), "seats": database.seats.count_documents({})}


if __name__ == "__main__":
    print(seed_demo_data(reset=True))

