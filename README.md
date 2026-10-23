# Student Doubt-Solving Platform — Backend

## Overview

Flask REST API for a student doubt-solving platform. The backend supports account registration, login, college ID verification, questions, and faculty answers.

## Current Features

- User registration and login with password hashing.
- JWT-based authentication.
- College ID-card upload and OCR-based roster verification.
- Verification-attempt limits.
- Question creation and retrieval for verified students.
- Faculty answers for questions.
- Role-based access control.
- Database migrations with Flask-Migrate.
- Automated tests using pytest.

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-Limiter
- SQLite for local development
- Pillow and pytesseract for image processing and OCR
- pytest

## Prerequisites

- Python 3.12 or a compatible version.
- Git.
- Tesseract OCR installed and accessible to the backend for ID-card verification.

## Setup on Windows

Run these commands from the repository root.

### 1. Create and activate the virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Copy the template:

```powershell
Copy-Item backend/.env.example backend/.env
```

Generate a strong random secret:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Use generated values for `SECRET_KEY` and `JWT_SECRET_KEY` in `backend/.env`. Generate separate values for the two keys.

**Never commit `backend/.env` or share its secrets.**

### 4. Configure Tesseract OCR

Install the Tesseract OCR application for your operating system. Ensure the executable is available on PATH, or configure the OCR service with the correct executable path.

Installing the Python package alone may not install the Tesseract application.

### 5. Apply database migrations

```powershell
Set-Location backend
python -m flask --app run.py db upgrade
```

### 6. Start the development server

```powershell
python run.py
```

The development server is for local development only. Use a production WSGI server for deployment.

## Health Check

With the backend running, open:

`http://127.0.0.1:5000/api/health`

A healthy response indicates that the backend can connect to its database.

## Run Tests

From the repository root:

```powershell
python -m pytest backend/tests -v
```

Tests use a temporary SQLite database.

## Import the Authorized College Roster

View the supported command:

```powershell
python backend/import_roster.py --help
```

Import a roster CSV:

```powershell
python backend/import_roster.py path\to\authorized_roster.csv
```

Use only a college-authorized roster. Confirm the required CSV column names from the roster importer implementation. Do not commit real student or faculty records to GitHub.

## API Endpoints

All versioned endpoints use the `/api/v1` prefix.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Register an account |
| POST | `/api/v1/auth/login` | Log in and obtain a JWT |
| GET | `/api/v1/auth/me` | Retrieve the current user |
| GET | `/api/v1/auth/status` | Retrieve verification status |
| POST | `/api/v1/verification/upload` | Upload an ID card for verification |
| POST | `/api/v1/verification/verify-details` | Disabled legacy verification route |
| POST | `/api/v1/questions/` | Create a question |
| GET | `/api/v1/questions/` | List accessible questions |
| GET | `/api/v1/questions/<question_id>` | Retrieve a question |
| POST | `/api/v1/questions/<question_id>/answers` | Submit a faculty answer |
| GET | `/api/v1/questions/<question_id>/answers` | List accessible answers |

Protected endpoints require the following header:

`Authorization: Bearer <access_token>`

The backend enforces verification status, roles, and ownership. Students can access their own questions and answers; verified faculty can access questions across students.

For exact request fields, response formats, and error codes, consult the route implementations and automated tests.

## Frontend Integration

1. Register using `/api/v1/auth/register`.
2. Log in using `/api/v1/auth/login`.
3. Send the returned JWT in the Authorization header for protected requests.
4. Check verification status through `/api/v1/auth/status`.
5. Upload an ID card to `/api/v1/verification/upload` using multipart form data with the field name `id_card`.
6. After verification, use the question endpoints.
7. Use the answer endpoints for faculty responses.

The frontend must not treat a client-supplied role or verification status as authoritative.

## AI Integration Status

AI answer generation is not yet documented as an implemented API capability. Although the question model contains an `ai_answer` field, the AI service contract and generation workflow must be agreed upon and implemented before the frontend depends on them.

The planned integration should use server-side credentials, approved knowledge sources, timeouts, safe failure behavior, and grounded answers. Never expose AI provider API keys in frontend code.

## Security and Deployment Notes

- Never commit `.env` files, real secrets, local databases, ID-card uploads, or real roster data.
- Use HTTPS in deployed environments.
- Use strong, separately managed application and JWT secrets.
- Configure a shared rate-limit store for multi-worker deployments; the in-memory default is intended for local development.
- Restrict roster imports to authorized operators.
- Treat OCR output as untrusted input and provide a manual-review path for verification failures.
- Do not use Flask's development server in production.
- Review logging, data retention, backups, monitoring, and access controls before handling real student data.

## Project Status

The backend API and automated tests are under development. Frontend and AI integration remain separate workstreams and must be integrated and tested before the complete platform is considered ready for deployment.