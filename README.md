# SmartAlloc – Automated Room Allocation System Using CSP

SmartAlloc is a full-stack Flask application that assigns students to examination seats or hostel beds while enforcing capacity, accessibility and group-separation rules. The system stores all data in MongoDB Atlas and uses a real Python CSP solver with backtracking, forward checking, minimum remaining values (MRV), degree ordering and least-constraining-value (LCV) ordering.

## Features

- Responsive light admin dashboard built with HTML, CSS and vanilla JavaScript.
- MongoDB Atlas only; no SQL, SQLite, MySQL or PostgreSQL.
- Dynamic CRUD for students, classes, groups and rooms.
- Dynamic room resizing and automatic seat/bed generation.
- Examination Seating and Hostel Room/Bed modes.
- Hard constraints for unique seats, room availability, capacity, accessibility and same-group horizontal adjacency.
- Soft preferences for vertical separation, room balancing, priority ordering and door/lift proximity.
- Detailed conflict explanations when a CSP has no solution.
- Validation report for persisted allocations.
- CSV import/export, JSON export, PDF allocation, seating, validation and conflict reports.
- Demo dataset with 20 students, multiple classes/groups/departments and three rooms.

## Project structure

```text
smartalloc/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── seed.py
├── README.md
├── .gitignore
├── models/
│   ├── database.py
│   ├── student_model.py
│   ├── class_model.py
│   ├── group_model.py
│   ├── room_model.py
│   ├── seat_model.py
│   └── allocation_model.py
├── services/
│   ├── csp_solver.py
│   ├── constraint_manager.py
│   ├── validation_service.py
│   ├── conflict_explainer.py
│   ├── csv_service.py
│   ├── pdf_service.py
│   └── room_service.py
├── routes/
│   ├── student_routes.py
│   ├── class_routes.py
│   ├── group_routes.py
│   ├── room_routes.py
│   ├── seat_routes.py
│   ├── allocation_routes.py
│   ├── report_routes.py
│   ├── dashboard_routes.py
│   └── demo_routes.py
├── templates/index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## 1. Install Python

Install Python 3.10 or newer from <https://www.python.org/downloads/>. During Windows setup, select **Add Python to PATH**. Confirm it:

```powershell
python --version
```

## 2. Create MongoDB Atlas

1. Open <https://www.mongodb.com/atlas/database> and create or sign in to an account.
2. Create a free shared cluster.
3. Create a database user under **Database Access**.
4. Add your current IP address under **Network Access**. For local development, Atlas can temporarily allow `0.0.0.0/0`, but a specific IP is safer.
5. Select **Connect → Drivers → Python** and copy the connection string.
6. The application will create the `smartalloc_db` database and these collections automatically: `students`, `classes`, `groups`, `departments`, `rooms`, `seats`, `allocations`, `allocation_runs`, `conflicts`, and `constraints`.

## 3. Windows setup in VS Code

Open the VS Code terminal inside the folder that contains `app.py`:

```powershell
cd path\to\smartalloc
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and replace `MONGODB_URI` with the Atlas URI. If your password contains characters such as `@`, `/` or `#`, URL-encode it in the connection string.

Seed the demo data and start Flask:

```powershell
python seed.py
python app.py
```

Open <http://127.0.0.1:5000> in a browser.

## 4. Linux/macOS setup

```bash
cd /path/to/smartalloc
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then run:

```bash
python seed.py
python app.py
```

Open <http://127.0.0.1:5000>.

## 5. Demo data controls

The first API request seeds a completely empty Atlas database with demo data if no previous seed marker exists. You can also use **Settings**:

- **Load default data** preserves existing student data when records already exist.
- **Reset demo data** clears the SmartAlloc collections and inserts the full demo dataset again.
- **Clear all data** removes all documents and leaves the database empty.

Run `python seed.py` when you explicitly want a clean demo database from the terminal.

## 6. Using the application

1. Add or import students in **Students**. Student IDs are unique.
2. Create classes and groups in **Classes & groups**.
3. Create rooms in **Rooms**. Rows, columns, capacity and accessible-seat count automatically generate the seat grid.
4. Use **Seats & beds** to block or unblock individual resources.
5. Open **Generate allocation**, select a mode and optionally select rooms.
6. SmartAlloc builds domains, filters blocked/unavailable resources, processes priority and accessibility, and performs CSP search.
7. Open **Allocation results** for the room-wise table and CSV, JSON or PDF exports.
8. Open **Validation report** after manual changes or room resizing.

## CSP algorithm

The solver creates one CSP variable per active student. Each variable's domain contains eligible seats. Domains remove blocked seats, occupied seats, unavailable rooms and inaccessible seats for accessibility-required students.

At each search step:

1. MRV chooses the unassigned student with the smallest remaining domain.
2. Priority and degree ordering break ties so Critical/High students and highly connected groups are considered early.
3. LCV orders candidate seats by estimated impact on other domains.
4. A candidate is checked against unique-seat and same-group horizontal adjacency rules.
5. Forward checking removes the chosen seat from every other domain and removes horizontal neighbours for students from the same group.
6. An empty domain causes immediate backtracking.
7. When all variables are assigned, the solution is persisted as one allocation run.

## Conflict explanations

Failure reports are generated from domain filtering and search dead ends. Examples include:

- Required capacity is larger than usable capacity.
- Accessibility-required students exceed accessible seats.
- A student has no domain after accessibility filtering.
- A group-separation assignment leaves another student with no valid seat.
- Search reached its safe node limit.

Each conflict includes category, severity, affected students, affected rooms, responsible constraint and a suggested correction.

## REST API examples

All JSON endpoints use:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {},
  "errors": []
}
```

Health:

```bash
curl http://127.0.0.1:5000/api/health
```

Create a student:

```bash
curl -X POST http://127.0.0.1:5000/api/students \
  -H "Content-Type: application/json" \
  -d '{"student_id":"ST999","name":"Test Student","class_name":"B.Tech CSE","group_id":"G1","department":"CSE","priority":"High","accessibility_required":false}'
```

Generate an allocation:

```bash
curl -X POST http://127.0.0.1:5000/api/allocation/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"Examination Seating","room_ids":[]}'
```

Validate:

```bash
curl -X POST http://127.0.0.1:5000/api/allocation/validate \
  -H "Content-Type: application/json" -d '{}'
```

## Export endpoints

- `GET /api/students/export-csv`
- `GET /api/rooms/export-csv`
- `GET /api/seats/export-csv`
- `GET /api/allocation/export/csv`
- `GET /api/allocation/export/json`
- `GET /api/allocation/export/pdf`
- `GET /api/reports/seating-chart/pdf`
- `GET /api/reports/validation/pdf`
- `GET /api/reports/conflicts/pdf`

The PDF files include the SmartAlloc title, generation time, run context, room/seat information, accessibility indicators, tables and page numbers.

## Troubleshooting

### `MONGODB_URI is not configured`

Create `.env` next to `app.py`, copy the value from `.env.example`, paste the Atlas connection string and restart Flask.

### `Server selection timeout`

Check that the Atlas cluster is running, the database user password is correct, your IP is in Network Access, and your password is URL-encoded.

### `ModuleNotFoundError`

Activate the virtual environment and reinstall:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Browser shows stale data

Click the refresh icon, or stop and restart Flask. The dashboard reads current MongoDB documents on each API request.

### Allocation fails

Open **Generate allocation** and read each conflict explanation. Typical fixes are adding seats, enabling a room, unblocking resources, adding accessible seats or changing the group separation input.

## Security notes

- Never commit `.env`.
- The MongoDB URI is only read by the Flask process and is never embedded in HTML or JavaScript.
- Use a least-privilege Atlas database user.
- Restrict Atlas Network Access to trusted IP addresses when possible.

