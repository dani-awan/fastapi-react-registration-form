# React + FastAPI + PostgreSQL Registration Form

A local learning project: one registration form, browser and server validation, persistent PostgreSQL records, and hashed passwords. This creates a registration record; login and authentication are not included.

## Requirements

Python 3.11 or newer, Node.js 20.19+ or 22.12+, and PostgreSQL (or Docker Desktop for the supplied database container). Start with an extracted project folder opened in VS Code.

## 1. Start PostgreSQL

In a terminal at the project root, with Docker Desktop running:

```powershell
docker compose up -d db
```

Alternatively, use an installed PostgreSQL server and pgAdmin. Create a login role `form_user` with a password, then a database `form_db` owned by that role. Set its connection URL in `backend/.env`. The supplied container password is for local demonstration only.

## 2. Start the Python API

Open a PowerShell terminal at the project root:

```powershell
cd backend
python -m venv .venv
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

No virtual environment activation is needed. PostgreSQL must be running first. The application creates the `users` table on startup. If you use a different database user or password, update `DATABASE_URL` before starting the API. URL-encode special characters in database passwords.

API documentation: http://localhost:8000/docs

## 3. Start React

Open a second PowerShell terminal at the project root:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev -- --port 5173 --strictPort
```

Open http://localhost:5173 and submit the form. Keep both terminals running. If PowerShell blocks `npm.ps1`, use `npm.cmd` instead of `npm`.

For macOS/Linux, replace `Copy-Item` with `cp` and use `.venv/bin/python` for the backend interpreter.

## Validation rules

| Field | Rule |
| --- | --- |
| Name | 2–80 characters after trimming; contains a letter |
| Email | Valid email, maximum 254 characters, trimmed and lowercased; unique in DB |
| Phone | Pakistan format: 11 digits beginning with 03 |
| Password | 8–128 characters; contains an ASCII letter and digit |
| Confirm password | Must match; checked in React and not sent to the API |

React gives immediate feedback on submit. FastAPI/Pydantic validates the request independently, so bypassing the frontend cannot bypass server validation. Invalid input returns 422; duplicate email returns 409; a successful insert returns 201 with the saved ID and public fields. Passwords are Argon2 hashed and never included in the response. Database failure during insertion returns 503.

## How the code works

1. `frontend/src/main.jsx` collects the input, validates it, and sends JSON with `fetch`.
2. `backend/app/main.py` uses the `Registration` Pydantic schema to validate JSON.
3. SQLAlchemy maps the `User` class to the PostgreSQL `users` table and commits the record.
4. React displays the ID returned after storage.

Example API body for `POST /api/register`:

```json
{"name":"Muhammad Danial","email":"danial@example.com","phone":"03001234567","password":"Example123"}
```

To inspect saved records in pgAdmin Query Tool:

```sql
SELECT id, name, email, phone, created_at FROM users ORDER BY id DESC;
```

There is no public endpoint listing registered people. The database volume preserves records when the container stops. `docker compose down` preserves it; `docker compose down -v` deletes it.

## Checks

### Real PostgreSQL verification (Windows)

With Docker Desktop running, open PowerShell at the extracted project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\Verify_PostgreSQL.ps1
```

This starts the supplied PostgreSQL database, installs backend dependencies and runs real integration checks. It creates a uniquely named test record, checks the saved row and password hash directly in PostgreSQL, checks duplicate and invalid requests, then deletes only that test record. Existing records are preserved. It uses the FastAPI test client to run the real API handlers; React is not part of this check. No permanent PowerShell execution-policy change is made.

If you already have PostgreSQL set up without Docker, configure `backend/.env`, install `requirements-dev.txt` and run this from `backend` instead:

```powershell
.\.venv\Scripts\python.exe verify_postgres.py
```

Success ends with `SUCCESS: all PostgreSQL integration checks passed.` This script was added for local verification; its PostgreSQL checks have not been executed in the build environment because PostgreSQL cannot run there with the available system-user permissions.

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use an isolated in-memory SQLite database to check request validation, insertion, normalization, password hashing, response privacy, and duplicate rejection. They do not replace a PostgreSQL integration check. For that check, start PostgreSQL, submit a valid form, confirm the record in pgAdmin, then retry the same email and confirm the duplicate error.

From `frontend`, run `npm run build` to check the production bundle.

## Troubleshooting

- `File does not exist` / `requirements.txt not found`: open the extracted folder and run commands from the correct subfolder.
- Database connection refused: start PostgreSQL and check the host, port, database, username and password in `.env`.
- Browser cannot connect: start the backend on port 8000. Check `VITE_API_URL` and restart Vite after editing frontend environment values.
- CORS error: frontend must use the origin specified by `FRONTEND_ORIGINS`, including its port. For the provided setup use `http://localhost:5173`.
- Port 5432 already used: use your existing PostgreSQL instance or change the container's host port and the URL together.

Before internet deployment, add authentication if needed, rate limiting, HTTPS, environment-managed secrets and schema migrations. This package is intended to run locally.
