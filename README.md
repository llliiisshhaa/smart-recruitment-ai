# Smart Recruitment System Using AI

> **Final-Year Academic Project**: An AI-powered virtual interview platform featuring automated resume parsing, adaptive real-time questioning, multilingual candidate interviews, resume-vs-interview skill matching, and automated recruiter performance reports.

---

## Tech Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0, PostgreSQL, Pydantic-Settings, Uvicorn
- **AI Engine (Upcoming)**: Google Gemini API
- **Frontend**: React 19, Vite, Tailwind CSS v4
- **Testing**: Pytest, HTTPX, FastAPI TestClient

---

## Project Structure

```text
smart-recruitment-ai/
├── .env.example             # Template for backend environment variables
├── .gitignore               # Excludes secrets, virtual environments, build artifacts
├── LICENSE                  # MIT License
├── README.md                # Project documentation and setup guide
│
├── backend/                 # FastAPI REST API backend
│   ├── requirements.txt     # Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── config.py        # Settings loaded via pydantic-settings
│       ├── database.py      # SQLAlchemy engine, SessionLocal, Base, get_db
│       ├── main.py          # FastAPI app, CORS middleware, /health endpoint
│       └── routers/
│           └── __init__.py  # Modular route handlers (auth, interviews, resumes)
│
├── ai/                      # AI orchestration and business logic
│   ├── prompts/
│   │   └── __init__.py      # Prompt templates for Gemini AI
│   ├── services/
│   │   └── __init__.py      # Core AI interview, resume parsing, scoring logic
│   └── validators/
│       └── __init__.py      # AI output schemas and hallucination guards
│
├── frontend/                # React (Vite) + Tailwind CSS application
│   ├── .env.example         # Template for frontend environment variables
│   ├── index.html           # HTML entrypoint
│   ├── package.json         # Node.js dependencies and scripts
│   ├── vite.config.js       # Vite configuration with Tailwind CSS plugin
│   └── src/
│       ├── App.jsx          # Dashboard with live /health status monitor
│       ├── index.css        # Tailwind CSS imports & global styles
│       └── main.jsx         # React DOM mounting
│
├── database/                # Database migrations (Alembic) and SQL schemas (.gitkeep)
├── docs/                    # Project reports, diagrams, API specifications (.gitkeep)
├── sample_data/             # Test resumes (PDF/DOCX) and mock job descriptions (.gitkeep)
└── tests/
    └── test_health.py       # Automated tests verifying /health endpoint
```

---

## Running Locally

Follow these step-by-step instructions to set up and run the project locally.

### 1. Prerequisites

- **Python**: Version 3.11 or higher (`python --version`)
- **Node.js**: Version 18 or higher with `npm` (`node --version`, `npm --version`)
- **PostgreSQL**: (Optional for initial health check, required for full DB persistence)

---

### 2. Backend Setup

Open a terminal at the project root (`smart-recruitment-ai`):

#### Step 2.1: Create & Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

*Note for Windows users:* If you encounter an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 2.2: Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

#### Step 2.3: Configure Environment Variables

Copy `.env.example` to `.env` in the project root:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On macOS / Linux:**
```bash
cp .env.example .env
```

*(Edit `.env` to update your database credentials or Gemini API key when ready).*

#### Step 2.4: Start the FastAPI Server

Navigate to the `backend` folder and start Uvicorn:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The backend will be available at:
- **API Root**: [http://localhost:8000/](http://localhost:8000/)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 3. Frontend Setup

Open a second terminal window at the project root (`smart-recruitment-ai`):

#### Step 3.1: Navigate to Frontend Directory & Install Dependencies

```bash
cd frontend
npm install
```

#### Step 3.2: Configure Frontend Environment (Optional)

Copy `frontend/.env.example` to `frontend/.env`:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On macOS / Linux:**
```bash
cp .env.example .env
```

*(By default, it connects to `http://localhost:8000`)*.

#### Step 3.3: Start Vite Development Server

```bash
npm run dev
```

Open your browser at:
- **Frontend Application**: [http://localhost:5173/](http://localhost:5173/)

The dashboard displays the live health state of the FastAPI backend and database connectivity.

---

### 4. Running Automated Tests

With your Python virtual environment activated, run `pytest` from the project root:

```bash
pytest tests/test_health.py -v
```

Expected output:
```text
tests/test_health.py::test_health_endpoint_returns_200 PASSED
tests/test_health.py::test_root_endpoint PASSED
```

---

## Health Check Behavior

The `GET /health` endpoint checks both the FastAPI server and the database:
- When the database is running and reachable:
  ```json
  {
    "status": "ok",
    "database": "connected"
  }
  ```
- When the database is offline or not yet configured:
  ```json
  {
    "status": "ok",
    "database": "unavailable"
  }
  ```
The endpoint returns HTTP 200 in both cases and **will never crash** if PostgreSQL is down.

---

## Roadmap

- [x] **Phase 1**: Project skeleton, health check endpoint, React + Tailwind dashboard
- [ ] **Phase 2**: User authentication (JWT) & PostgreSQL SQLAlchemy data models
- [ ] **Phase 3**: Resume parsing service (PDF/DOCX) & Gemini AI skill extraction
- [ ] **Phase 4**: Virtual interview engine (adaptive questions & speech-to-text)
- [ ] **Phase 5**: Candidate evaluation scoring & PDF recruiter report generation