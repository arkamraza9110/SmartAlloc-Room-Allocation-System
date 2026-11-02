"""Constraint Satisfaction Problem solver for examination and hostel allocation.

The implementation uses backtracking, forward checking, MRV, degree ordering and
least-constraining-value ordering. It deliberately keeps the search data in
memory; MongoDB is used by the routes for durable input and output.
"""

from collections import Counter

from services.constraint_manager import PRIORITY_RANK, horizontally_adjacent


class CSPAllocationSolver:
    def __init__(self, students: list[dict], seats: list[dict], rooms: list[dict], max_nodes: int = 100000):
        self.students = {student["student_id"]: student for student in students}
        self.seats = {seat["seat_id"]: seat for seat in seats}
        self.rooms = {room["room_id"]: room for room in rooms}
        self.max_nodes = max_nodes
        self.nodes = 0
        self.dead_ends: list[dict] = []
        self.student_ids = list(self.students)
        self.usable_seats = {
            seat_id: seat
            for seat_id, seat in self.seats.items()
            if self._usable_seat(seat)
        }

    def _usable_seat(self, seat: dict) -> bool:
        room = self.rooms.get(seat.get("room_id"), {})
        return bool(
            room.get("available", False)
            and not seat.get("is_blocked", False)
            and seat.get("status", "Available") not in {"Occupied", "Blocked"}
        )

    def _seat_allowed(self, student: dict, seat: dict) -> bool:
        if not self._usable_seat(seat):
            return False
        if student.get("accessibility_required") and not seat.get("is_accessible"):
            return False
        return True

    def _initial_domains(self) -> tuple[dict[str, list[str]], list[dict]]:
        domains = {}
        conflicts = []
        for student_id, student in self.students.items():
            domains[student_id] = [
                seat_id
                for seat_id, seat in self.usable_seats.items()
                if self._seat_allowed(student, seat)
            ]
            if not domains[student_id]:
                category = "accessibility" if student.get("accessibility_required") else "domain"
                conflicts.append(
                    {
                        "category": category,
                        "severity": "Critical",
                        "description": f"Student {student_id} has no valid seat after domain filtering.",
                        "affected_students": [student_id],
                        "affected_rooms": [],
                        "responsible_constraint": "Accessibility and seat-domain filtering",
                        "suggested_solution": "Add an eligible seat, unblock a seat, or change the student requirement.",
                    }
                )
        return domains, conflicts

    def _precheck(self, domains: dict[str, list[str]]) -> list[dict]:
        conflicts = []
        room_capacity = sum(
            min(
                int(room.get("capacity", 0)),
                sum(1 for seat in self.usable_seats.values() if seat.get("room_id") == room_id),
            )
            for room_id, room in self.rooms.items()
        )
        if len(self.student_ids) > room_capacity:
            conflicts.append(
                {
                    "category": "capacity",
                    "severity": "Critical",
                    "description": f"Required capacity is {len(self.student_ids)} students, but only {room_capacity} usable seats are available within room capacities.",
                    "affected_students": self.student_ids,
                    "affected_rooms": sorted({seat.get("room_id") for seat in self.usable_seats.values()}),
                    "responsible_constraint": "Room capacity and seat availability",
                    "suggested_solution": "Add another room, increase capacity, unblock seats, or select fewer students.",
                }
            )
        required_accessible = sum(1 for student in self.students.values() if student.get("accessibility_required"))
        accessible = sum(1 for seat in self.usable_seats.values() if seat.get("is_accessible"))
        if required_accessible > accessible:
            conflicts.append(
                {
                    "category": "accessibility",
                    "severity": "Critical",
                    "description": f"There are {required_accessible} accessibility-required students but only {accessible} accessible seats.",
                    "affected_students": [
                        student["student_id"]
                        for student in self.students.values()
                        if student.get("accessibility_required")
                    ],
                    "affected_rooms": sorted({seat.get("room_id") for seat in self.usable_seats.values()}),
                    "responsible_constraint": "Accessibility requirement",
                    "suggested_solution": "Add accessible seats near doors or lifts, or enable an accessible room.",
                }
            )
        if len(domains) and any(not domain for domain in domains.values()):
            conflicts.append(
                {
                    "category": "domain",
                    "severity": "Critical",
                    "description": "At least one student has an empty domain of valid seats.",
                    "affected_students": [sid for sid, domain in domains.items() if not domain],
                    "affected_rooms": [],
                    "responsible_constraint": "Domain filtering",
                    "suggested_solution": "Review room availability, blocked seats and accessibility settings.",
                }
            )
        return conflicts

    def _select_student(self, domains: dict[str, list[str]], assigned: dict[str, str]) -> str:
        candidates = [sid for sid in self.student_ids if sid not in assigned]
        return min(
            candidates,
            key=lambda sid: (
                len(domains[sid]),
                -PRIORITY_RANK.get(self.students[sid].get("priority", "Normal"), 2),
                -sum(1 for other in candidates if other != sid and self.students[other].get("group_id") == self.students[sid].get("group_id")),
            ),
        )

    def _is_consistent(self, student_id: str, seat_id: str, assigned: dict[str, str]) -> bool:
        student = self.students[student_id]
        seat = self.seats[seat_id]
        if any(existing_seat == seat_id for existing_seat in assigned.values()):
            return False
        room = self.rooms.get(seat.get("room_id"), {})
        room_load = sum(
            1
            for existing_seat_id in assigned.values()
            if self.seats[existing_seat_id].get("room_id") == seat.get("room_id")
        )
        if room_load >= int(room.get("capacity", 0)):
            return False
        for other_id, other_seat_id in assigned.items():
            other_student = self.students[other_id]
            other_seat = self.seats[other_seat_id]
            if other_student.get("group_id") == student.get("group_id") and horizontally_adjacent(seat, other_seat):
                return False
        return True

    def _propagate(self, student_id: str, seat_id: str, domains: dict[str, list[str]], assigned: dict[str, str]):
        new_domains = {sid: list(values) for sid, values in domains.items()}
        student = self.students[student_id]
        assigned_seat = self.seats[seat_id]
        for other_id in self.student_ids:
            if other_id == student_id or other_id in assigned:
                continue
            filtered = [candidate for candidate in new_domains[other_id] if candidate != seat_id]
            if self.students[other_id].get("group_id") == student.get("group_id"):
                filtered = [
                    candidate
                    for candidate in filtered
                    if not horizontally_adjacent(assigned_seat, self.seats[candidate])
                ]
            new_domains[other_id] = filtered
            if not filtered:
                return None, {
                    "category": "group-separation",
                    "severity": "High",
                    "description": f"Assigning {student_id} to {seat_id} leaves {other_id} with no valid seat after group-separation propagation.",
                    "affected_students": [student_id, other_id],
                    "affected_rooms": [assigned_seat.get("room_id")],
                    "responsible_constraint": "Same-group horizontal adjacency",
                    "suggested_solution": "Add more seats, use another room, or relax the horizontal group rule.",
                }
        return new_domains, None

    def _ordered_values(self, student_id: str, domain: list[str], assigned: dict[str, str]) -> list[str]:
        assignments = [
            {"student": self.students[sid], "seat": self.seats[seat_id]}
            for sid, seat_id in assigned.items()
        ]

        def impact(seat_id: str) -> tuple[int, int, int]:
            seat = self.seats[seat_id]
            impact_score = 0
            for other_id, other in self.students.items():
                if other_id == student_id or other_id in assigned:
                    continue
                if other.get("group_id") == self.students[student_id].get("group_id"):
                    impact_score += sum(
                        1
                        for candidate in self.usable_seats.values()
                        if horizontally_adjacent(seat, candidate)
                    )
            room = self.rooms.get(seat.get("room_id"), {})
            preference = int(seat.get("near_door", False)) + int(seat.get("near_lift", False))
            room_load = sum(1 for sid in assigned if self.seats[assigned[sid]].get("room_id") == seat.get("room_id"))
            return (impact_score, room_load, -(preference + int(seat.get("is_accessible", False))))

        return sorted(domain, key=impact)

    def _backtrack(self, domains: dict[str, list[str]], assigned: dict[str, str]) -> bool:
        self.nodes += 1
        if self.nodes > self.max_nodes:
            self.dead_ends.append(
                {
                    "category": "search-limit",
                    "severity": "Warning",
                    "description": f"Search stopped after {self.max_nodes} nodes.",
                    "affected_students": [sid for sid in self.student_ids if sid not in assigned],
                    "affected_rooms": [],
                    "responsible_constraint": "Backtracking search limit",
                    "suggested_solution": "Reduce the dataset or review constraints before retrying.",
                }
            )
            return False
        if len(assigned) == len(self.student_ids):
            return True
        student_id = self._select_student(domains, assigned)
        for seat_id in self._ordered_values(student_id, domains[student_id], assigned):
            if not self._is_consistent(student_id, seat_id, assigned):
                continue
            assigned[student_id] = seat_id
            propagated, conflict = self._propagate(student_id, seat_id, domains, assigned)
            if propagated is not None and self._backtrack(propagated, assigned):
                return True
            assigned.pop(student_id, None)
            if conflict:
                self.dead_ends.append(conflict)
        return False

    def solve(self) -> dict:
        domains, initial_conflicts = self._initial_domains()
        precheck = self._precheck(domains)
        if precheck:
            return {
                "success": False,
                "assignments": {},
                "conflicts": precheck,
                "nodes": 0,
            }
        assigned = {}
        success = self._backtrack(domains, assigned)
        if not success:
            counter = Counter(conflict.get("category") for conflict in self.dead_ends)
            top_categories = ", ".join(category for category, _ in counter.most_common(3)) or "constraint interaction"
            conflicts = self.dead_ends[-12:] or [
                {
                    "category": "unsatisfiable",
                    "severity": "Critical",
                    "description": f"No complete allocation exists under the active constraints ({top_categories}).",
                    "affected_students": self.student_ids,
                    "affected_rooms": sorted(self.rooms),
                    "responsible_constraint": "CSP backtracking",
                    "suggested_solution": "Add capacity or relax the most restrictive constraint.",
                }
            ]
            return {"success": False, "assignments": {}, "conflicts": conflicts, "nodes": self.nodes}
        return {"success": True, "assignments": assigned, "conflicts": [], "nodes": self.nodes}

