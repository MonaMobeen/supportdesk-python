# SupportDesk — Service Request & Support Ticket Management System

A backend-only Python capstone project that gives a support team one reliable place to register, manage, track, search, and report on support requests from creation to closure.

---

## 1. Project Overview & Business Problem

A small company currently receives support requests through chat messages, email, and verbal follow-ups. Requests are easily lost, there is no consistent ownership, and managers cannot see which issues are open, overdue, or already resolved.

**SupportDesk** solves this by providing a single backend service where:
- Requesters can log issues and track them
- Support Agents can take ownership, update status, and resolve requests
- Administrators/Team Leads can oversee the whole operation, assign work, and view reports

The system supports these roles **conceptually** through the data model and endpoint behavior (a requester creates/views tickets, an agent updates/resolves them, an admin views everything and assigns work). A full authentication/authorization system was intentionally not built — see the Engineering Decision Log for the reasoning.

---

## 2. Feature List

| Area | Features |
|---|---|
| **Ticket Lifecycle** | Create, view, update tickets; assign/reassign to agents; status lifecycle (Open → In Progress → Resolved → Closed) with enforced valid transitions; reopen support; priority levels (Low/Medium/High/Critical) |
| **Comments** | Add chronological comments to a ticket without overwriting previous ones |
| **Activity History** | Automatic audit trail of status, priority, and assignment changes (old value, new value, timestamp) |
| **Search / Filter / Sort / Pagination** | Filter by status, priority, category, requester, assignee, created-date range; text search on title/description; sorting; paginated results with total count |
| **Attachments** | Upload files to a ticket with type and size validation; list and download attachments |
| **Import / Export** | Bulk-import tickets from CSV with per-row validation and a success/failure summary; export a filtered set of tickets to CSV |
| **Reporting** | Dashboard summary (total tickets, counts by status/priority, open tickets per agent, average resolution time); overdue/aging ticket detection |
| **Reliability** | Centralized configuration via `.env`, structured logging to console and file, a global exception handler that returns clean JSON errors instead of raw tracebacks |
| **Testing** | Automated test suite (pytest) covering business rules, CRUD, filters, import, and a mocked dependency-failure scenario |

### Known Limitations

- No real authentication/authorization — role behavior is demonstrated through endpoint design, not enforced via login sessions or tokens.
- SQLite is used as the database, which is suitable for this capstone's scale but not for high-concurrency production use.
- Attachments are stored on local disk, not on a dedicated object-storage service.
- No database migration tool (e.g., Alembic) is used yet — schema changes during development required recreating the database.

---

## 3. Project Structure

```
supportdesk/
├── app/
│   ├── main.py                # App entry point, router registration, global exception handler
│   ├── config.py               # Centralized configuration (reads from .env)
│   ├── logger.py                # Logging setup
│   ├── database.py             # SQLAlchemy engine/session setup
│   ├── models/                  # SQLAlchemy ORM models (database tables)
│   │   ├── ticket.py
│   │   ├── agent.py
│   │   ├── comment.py
│   │   ├── history.py
│   │   └── attachment.py
│   ├── schemas/                 # Pydantic schemas (request/response validation)
│   │   ├── ticket.py
│   │   ├── agent.py
│   │   ├── comment.py
│   │   ├── history.py
│   │   └── attachment.py
│   ├── services/                 # Business logic layer
│   │   ├── ticket_service.py
│   │   ├── agent_service.py
│   │   ├── comment_service.py
│   │   ├── history_service.py
│   │   └── attachment_service.py
│   ├── routers/                   # API route definitions
│   │   ├── tickets.py
│   │   └── agents.py
│   └── uploads/                    # Uploaded attachment files (git-ignored)
├── tests/
│   ├── conftest.py               # Test database and client fixtures
│   ├── test_tickets.py           # Core business rule tests
│   ├── test_import.py             # Import validation tests
│   └── test_failures.py           # Mocked dependency-failure test
├── .env                            # Environment configuration (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

**Separation of concerns**: `routers` handle HTTP request/response only, `services` contain business logic, `models` define database structure, `schemas` define validation rules for data entering/leaving the API. This keeps logic testable and avoids one oversized file.

---

## 4. Local Setup Instructions (From a Clean Machine)

### Prerequisites
- Python 3.10+ installed
- Git installed

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/MonaMobeen/supportdesk-python
cd supportdesk

# 2. Create and activate a virtual environment
python -m venv venv

# Windows (CMD):
venv\Scripts\activate
# Windows (Git Bash):
source venv/Scripts/activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file (see Configuration section below)

# 5. Run the application
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`
Interactive API docs (Swagger UI): `http://127.0.0.1:8000/docs`

### `requirements.txt` (dependency list)

```
fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
python-multipart
pytest
httpx
```

Generate/update this file anytime with:
```bash
pip freeze > requirements.txt
```

---

## 5. Configuration / Environment Variables

Create a `.env` file in the project root:

```
DATABASE_URL=sqlite:///./app.db
UPLOAD_DIR=app/uploads
MAX_UPLOAD_SIZE_MB=5
OVERDUE_THRESHOLD_HOURS=48
```

| Variable | Purpose | Example |
|---|---|---|
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `UPLOAD_DIR` | Folder where attachment files are stored | `app/uploads` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed attachment size | `5` |
| `OVERDUE_THRESHOLD_HOURS` | Hours after which an unresolved ticket is considered overdue | `48` |

`.env` is excluded from version control via `.gitignore` — configuration and secrets are never hard-coded into source code (NFR-06).

---

## 6. How to Run the Application

```bash
uvicorn app.main:app --reload
```

Test check (used to verify the service is running):
```
GET /test
```
Expected response:
```json
{"status": "ok", "message": "SupportDesk is running"}
```

---

## 7. How to Run Tests

```bash
python -m pytest -v
```

This runs the full automated test suite covering:
- Valid and invalid ticket creation
- Valid and forbidden status transitions
- Resolution note requirement before closing
- Agent assignment and reassignment (valid and invalid agent)
- Search and status filtering
- CSV import with mixed valid/invalid rows
- A mocked database failure to confirm the global error handler responds safely instead of crashing

Tests use a separate SQLite database (`test.db`), created fresh and destroyed after each test — the real `app.db` is never touched by the test suite.

---

## 8. API Usage — Example Requests & Workflows

Full interactive documentation is available at `/docs`. Key examples:

### Create a ticket
```bash
curl -X POST http://127.0.0.1:8000/tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Login page not loading",
    "description": "Getting blank screen on login",
    "requester": "Mona Mobeen",
    "category": "Bug",
    "priority": "High"
  }'
```

### Update ticket status (with resolution note)
```bash
curl -X PUT http://127.0.0.1:8000/tickets/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Closed", "resolution_note": "Fixed by clearing cache"}'
```

### Search and filter tickets
```bash
GET /tickets/?status=Open&priority=High&search=login&sort_by=created_at&order=desc&skip=0&limit=20
```

### Add a comment
```bash
curl -X POST http://127.0.0.1:8000/tickets/1/comments \
  -H "Content-Type: application/json" \
  -d '{"author": "Hooria khan", "text": "Investigating the issue"}'
```

### View ticket history
```
GET /tickets/1/history
```

### Upload an attachment
```
POST /tickets/1/attachments   (multipart/form-data, field name: file)
```

### Bulk import tickets from CSV
```
POST /tickets/import   (multipart/form-data, field name: file, .csv only)
```

### Export tickets to CSV
```
GET /tickets/export?status=Open
```

### Dashboard summary
```
GET /tickets/reports/summary
```

### Overdue tickets
```
GET /tickets/reports/overdue
```

### Register an agent (reference data — Admin capability)
```bash
curl -X POST http://127.0.0.1:8000/agents/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Minal Noor", "email": "minal@facebook.com"}'
```

---

## 9. Engineering Decision Log

| Decision Area | Chosen Option | Alternative Considered | Why Chosen | Trade-off / Limitation |
|---|---|---|---|---|
| **API Framework** | FastAPI | Flask, Django REST Framework | Built-in async support, automatic request validation via Pydantic, auto-generated interactive docs (`/docs`) which double as a demo interface — no separate frontend needed | Smaller ecosystem than Django for things like admin panels |
| **Database** | SQLite (via SQLAlchemy) | PostgreSQL | Zero setup, file-based, sufficient for this capstone's data volume and single-instance deployment | Not suitable for high-concurrency production use or multiple app instances writing simultaneously |
| **Data Access** | SQLAlchemy ORM | Raw SQL queries | Prevents SQL injection by design, makes schema changes and relationships (foreign keys) easier to manage and read | Slight performance overhead vs. hand-tuned raw SQL; abstracts away some SQL-specific optimizations |
| **Project Structure** | Layered (routers → services → models/schemas) | Single-file script | Keeps business logic separate from HTTP handling and database structure, making each layer independently testable | More files to navigate for a project of this size, but scales better if features grow |
| **Role/Identity Handling** | Simple identity fields passed in request data (e.g., `requester`, `assigned_agent`, comment `author`) rather than full authentication | JWT-based login/auth system, OAuth | The PDF explicitly leaves identity/authorization implementation as a free decision and lists complex auth/SSO as out of scope; the project's focus is backend business logic, not access control | No real security boundary between roles — anyone calling the API can act as any role. Documented here as a known limitation and would be the first addition for production use |
| **Validation** | Pydantic schemas + Python `Enum` for fixed value sets (priority) | Manual `if` checks | Declarative, automatic, and produces clear `422` errors without extra code | Enum error messages are framework-generated and less customizable than hand-written validation |
| **Attachment Storage** | Local disk (`app/uploads`) with unique filenames (UUID-prefixed) | Cloud object storage (S3, etc.) | Simple, no external account/service required for a capstone project; sufficient for demonstrating the feature | Not durable across redeployments on some hosting platforms; would need persistent disk or object storage in production |
| **Import/Export Format** | CSV, using Python's built-in `csv` module | JSON, Excel (`openpyxl`) | CSV is the most common structured format for bulk ticket data and needs no extra dependency | Less rich than Excel (no formatting/multiple sheets); acceptable per the "at least one common format" requirement |
| **Testing Library** | pytest + FastAPI's `TestClient` (httpx) | unittest | Simpler syntax, widely used with FastAPI, supports fixtures for clean test database setup/teardown | N/A |
| **Mocking Strategy** | `unittest.mock.patch` on the ORM model to simulate a database failure | A real broken database connection | Lets us test the failure path safely and repeatably without an actual outage | Only tests the code's *reaction* to failure, not real database failure modes (timeouts, deadlocks) |
| **Dependency Management** | `pip` + `requirements.txt` | Poetry, pipenv | Simplest, most universally supported approach; no extra tooling needed | Less strict dependency locking than Poetry's lockfile |
| **Configuration** | `.env` file + `python-dotenv`, centralized in `app/config.py` | Hard-coded values, OS environment variables set manually | Keeps secrets/config out of source code (NFR-06) while remaining simple for local development | `.env` file itself must still be kept out of version control and handled carefully in deployment |
| **Logging** | Python's built-in `logging` module, writing to console and `app.log` | Third-party logging libraries (structlog, loguru) | No extra dependency, sufficient for this project's scale, easy to inspect during review | Less structured (not JSON) than production-grade logging setups |
| **Error Handling** | Centralized FastAPI exception handler for unexpected errors + explicit `HTTPException` for expected business errors | Try/except in every route | Guarantees no raw traceback ever reaches the client (NFR-10 security basic), while still distinguishing expected (400/404) from unexpected (500) failures | A single unexpected-error handler gives a generic message; more granular custom exception types could give richer error categorization in a larger system |

---

## 10. Business Rules Enforced

- Ticket IDs are auto-generated and never change after creation.
- A ticket cannot be marked Resolved or Closed without a resolution note.
- Status can only move through defined valid transitions (invalid transitions return `400`).
- A Closed ticket can only be edited by first reopening it.
- A ticket cannot be assigned to an agent that does not exist in the Agent reference table.
- Invalid data (bad enum values, missing required fields) is rejected — never silently ignored.
- Timestamps (`created_at`, `updated_at`, `resolution_at`) are system-generated, not user-supplied.

## 11. Edge Cases Handled

| Edge Case | Handling |
|---|---|
| Ticket ID does not exist | `404 Not Found` |
| Missing mandatory fields | `422 Validation Error` (Pydantic) |
| Unsupported status/priority | `422` (priority enum) / `400` (status transition rule) |
| Invalid status transition | `400` with a clear message |
| Assignment to invalid agent | `400` with a clear message |
| Corrupted/invalid import file | Non-CSV files rejected at upload; malformed rows reported individually |
| Import file with valid + invalid rows | Valid rows are saved; invalid rows are reported with reasons — one bad row does not block the rest |
| Unsupported attachment type / oversized file | `400` with a clear message before saving |
| No records match a filter/search | `200` with an empty `results` array and `total: 0`, not an error |
| Unexpected internal exception | Caught by the global exception handler, logged, and returned as a generic `500` — no stack trace exposed to the client |

---

## 12. Demo Scenarios

1. **Create a valid High/Critical ticket** — `POST /tickets/` with `priority: "Critical"`, confirm it's returned by `GET /tickets/{id}`.
2. **Attempt an invalid ticket creation** — omit `title` or use `priority: "Urgent"`, observe the `422` validation response.
3. **Full lifecycle** — assign a ticket to a registered agent, move it Open → In Progress → Resolved, add a comment along the way, then close it with a resolution note; view its history afterward.
4. **Invalid status transition** — attempt Closed → In Progress directly, observe the `400` rejection.
5. **Search and filter at scale** — import several tickets via CSV, then filter/search/paginate the results.
6. **Import with mixed rows** — upload a CSV with valid and invalid rows, review the returned success/failure summary.
7. **Reporting metric change** — check `GET /tickets/reports/summary`, resolve a ticket, check again — `average_resolution_time_hours` updates.
8. **Restart persistence check** — stop and restart the server, confirm previously created tickets are still present (SQLite file persists on disk).
9. **Run the automated test suite** — `python -m pytest -v`, showing all business-rule and failure-mocking tests passing.
10. **Logs for normal and error flow** — show `app.log` containing an `INFO` line for a successful ticket creation and an `ERROR` line for a caught exception, with no secrets exposed.

---

## 13. Deployment
 
**Live URL**: `https://supportdesk-python.onrender.com/` 
**Interactive API docs (live)**: `https://supportdesk-python.onrender.com/docs`
**Test check (live)**: `https://supportdesk-python.onrender.com/test`
 
### Platform Choice
 
The application is deployed as two separate pieces, each on the free tier of a different provider:
 
| Piece | Provider | Why |
|---|---|---|
| **Web Service** (the FastAPI app) | [Render](https://render.com) | Deploys directly from a GitHub repository, detects Python automatically, provides a free HTTPS URL, and needs no credit card for a standard free web service |
| **Database** (PostgreSQL) | [Neon](https://neon.tech) | Genuinely free, permanent Postgres tier with no credit card requirement and no forced expiry — unlike some providers' free databases, which expire after a fixed number of days |
 
Locally, the project uses **SQLite** (simple, zero setup, ideal for development). In the deployed environment, **PostgreSQL (via Neon)** is used instead, because the requirement is that persisted data must survive process restarts — a hosting provider's local disk is not guaranteed to persist between deploys/restarts, but a managed Postgres database is. No application code changes were needed to switch databases — only the `DATABASE_URL` value, because the app reads its database connection through SQLAlchemy via `app/config.py`.
 
### Configuration in the Deployed Environment
 
Secrets and environment-specific values are set directly in Render's **Environment Variables** dashboard for the service — never committed to the repository:
 
| Key | Purpose |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `UPLOAD_DIR` | `app/uploads` |
| `MAX_UPLOAD_SIZE_MB` | `5` |
| `OVERDUE_THRESHOLD_HOURS` | `48` |
 
### Build & Start Configuration (Render)
 
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
### Persistence Across Restarts
 
Because ticket data lives in the Neon PostgreSQL database (not on Render's local filesystem), restarting or redeploying the web service does **not** delete or reset application data — only the running process restarts; the database is a separate, independently hosted service.
 
### Test Check
 
`GET /test` is used to verify the deployed service is running:
```json
{"status": "ok", "message": "SupportDesk is running"}
```
 
### What Would Change for a Higher-Traffic Production System
 
- Move off the free tiers to paid instances with guaranteed uptime (Render's free web service spins down after inactivity, causing a slow "cold start" on the next request).
- Move attachment storage from local disk to a dedicated object storage service (e.g., S3-compatible storage), since local disk on most free/managed hosts is not guaranteed to persist or scale.
- Introduce a proper database migration tool (e.g., Alembic) instead of manual schema/table recreation.
- Add real authentication/authorization instead of the simplified identity fields used in this capstone.
- Add connection pooling tuning and monitoring/alerting for the database and application.
---
 
  
## 14. Final Reflection
 
### The Hardest Issue: Missing Dependencies Crashing the App on Startup
 
**What happened**
 
While adding the file-attachment feature, a new endpoint was written to accept file uploads (`POST /tickets/{id}/attachments`). The moment the server was restarted to test it, the app failed to start at all:
 
```
RuntimeError: Form data requires "python-multipart" to be installed.
```
 
This was more disruptive than a normal `400`/`500` error during a request — the **entire application refused to boot**, so every endpoint (not just the new one) was unreachable.
 
**Why it happened**
 
FastAPI supports file uploads through `UploadFile`, but the actual parsing of multipart form data (the format browsers/Postman use to send files) is handled by a separate library, `python-multipart`. It isn't installed automatically with FastAPI itself, so a route that *declares* a file-upload parameter fails at import time if that library is missing — even before any request is ever made.
 
**How it was debugged**
 
- The error message was read carefully rather than treated as unrelated noise — it directly named the missing package and even suggested the fix (`pip install python-multipart`).
- After installing it, the *same* error still appeared once, which was confusing at first — this turned out to be a version-mismatch between `fastapi` and `python-multipart` rather than a missing install, and was resolved by reinstalling a specific compatible version and upgrading `fastapi`.
- The fix was verified by restarting the server and confirming the app booted cleanly, then re-testing the upload endpoint itself.
**The trade-off this exposed**
 
A single missing optional dependency was able to take down the *entire* application, not just the one feature that needed it — there was no isolation between features at the dependency level. It also revealed that `requirements.txt` needs to be kept genuinely in sync with what the code uses, rather than assumed to be complete.
 
**What would be improved with more time**
 
- Regenerate and review `requirements.txt` (via `pip freeze`) after every new feature that introduces a new import, rather than only near the end of the project.
- Add a basic startup smoke test (even just importing `app.main` in CI) that would catch a boot-time failure like this automatically, before it's discovered manually.
- Pin exact dependency versions (not just names) in `requirements.txt` to avoid the kind of version-mismatch surprise encountered here, especially before deployment to a different machine/environment.
### Other Notable Issues Along the Way
 
| Issue | Root Cause | Resolution |
|---|---|---|
| A new `resolution_note` column caused `no such column` errors after being added to the model | SQLite doesn't alter existing tables automatically when a SQLAlchemy model changes — `create_all()` only creates tables that don't exist yet | Deleted and recreated the local development database; documented the need for a real migration tool as a limitation |
| `/tickets/reports/summary` returned a `404 "Ticket not found"` instead of the report | FastAPI matches routes in the order they're defined — a `/{ticket_id}` route defined above `/reports/summary` treats `"reports"` as if it were a ticket ID | Reordered the routes so fixed-path endpoints (`/import`, `/export`, `/reports/...`) are declared before the dynamic `/{ticket_id}` route |
| A mocked "database failure" test failed even though the app was behaving correctly | FastAPI's `TestClient` re-raises unhandled exceptions by default during tests — different from how a real client experiences a `500` response | Set `raise_server_exceptions=False` on the test client so the global exception handler could be verified the way a real caller would see it |
 
### General Takeaway
 
The most disruptive problems in this project weren't wrong business logic — they were **things outside the application code itself**: an uninstalled dependency, a mismatched package version, and the order routes were declared in. Each produced an error that looked unrelated to its real cause at first glance. The habit that consistently cut through the confusion was the same each time: **read the exact error message and traceback line before changing anything**, rather than guessing. With more time, the next priorities would be a proper migration tool, pinned dependency versions, and a basic startup check in the test suite to catch boot-time failures automatically.
 