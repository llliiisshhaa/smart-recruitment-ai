# Smart Recruitment System Using AI

> **Final-Year Academic Project**: An AI-powered virtual interview platform featuring automated resume parsing, adaptive real-time questioning, multilingual candidate interviews, resume-vs-interview skill matching, and automated recruiter performance reports.

---

## Tech Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0, PostgreSQL, Pydantic-Settings, Uvicorn
- **Resume Parser (Stage 8)**: Offline deterministic NLP parser (pdfplumber, python-docx, spaCy `en_core_web_sm`)
- **Frontend**: React 19, Vite, Tailwind CSS v4
- **Testing**: Pytest, HTTPX, ReportLab, FastAPI TestClient

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
│   ├── scripts/             # Data seeding and admin provisioning
│   ├── tests/               # Automated test suites
│   └── app/
│       ├── __init__.py
│       ├── config.py        # Settings loaded via pydantic-settings
│       ├── database.py      # SQLAlchemy engine, SessionLocal, Base, get_db
│       ├── main.py          # FastAPI app, CORS middleware, /health endpoint
│       ├── api/
│       │   ├── auth.py      # Authentication & RBAC routes
│       │   └── routes/      # Modular route handlers (resumes, jobs, applications)
│       ├── models/          # SQLAlchemy ORM models (User, Resume, Skill, Job, etc.)
│       ├── schemas/         # Pydantic schemas
│       ├── services/        # Resilient business services (audit logging)
│       └── ai/              # Non-LLM deterministic AI engine
│           ├── data/
│           │   └── skill_aliases.json # 60+ alias taxonomy mappings
│           └── services/
│               └── resume_parser/     # Modular extraction, cleaning, sections, entities, skills
│
├── frontend/                # React 19 (Vite) + Tailwind CSS application
│   ├── .env.example         # Template for frontend environment variables
│   ├── index.html           # HTML entrypoint
│   ├── package.json         # Node.js dependencies and scripts
│   ├── vite.config.js       # Vite configuration with Tailwind CSS plugin
│   └── src/
│       ├── App.jsx          # Router & application shell
│       ├── api/             # Axios client & route API modules
│       ├── pages/           # Candidate & Recruiter views
│       └── components/      # UI components (dossier modal, status badges, navbar)
│
├── database/                # Database migrations (Alembic) and SQL schemas (.gitkeep)
├── docs/                    # Project reports, diagrams, API specifications (.gitkeep)
└── sample_data/             # Test resumes (PDF/DOCX) and mock job descriptions (.gitkeep)
```

---

## Running Locally

Follow these step-by-step instructions to set up and run the project locally.

### 1. Prerequisites

- **Python**: Version 3.11 or higher (`python --version`)
- **Node.js**: Version 18 or higher with `npm` (`node --version`, `npm --version`)
- **PostgreSQL**: (Optional for initial health check, required for full DB persistence)

---

### 2. Backend Setup (Windows PowerShell)

Open a PowerShell terminal at the project root (`smart-recruitment-ai`):

#### Step 2.1: Create & Activate Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

*Note for Windows users:* If you encounter an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 2.2: Install Backend Dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

#### Step 2.3: Download or Install the spaCy Model

```powershell
.\.venv\Scripts\python.exe -m spacy download en_core_web_sm
```

#### Step 2.4: Verify Installed Packages

```powershell
.\.venv\Scripts\python.exe -m pip list
```

Verify that `pdfplumber`, `python-docx`, `spacy`, `en_core_web_sm`, `reportlab`, and `fastapi` are present.

#### Step 2.5: Configure Environment Variables

Copy `.env.example` to `.env` in the project root:

```powershell
Copy-Item .env.example .env
```

*(Edit `.env` to update your database credentials when ready)*.

#### Step 2.6: Seed Canonical Skills Taxonomy (Optional / Offline)

```powershell
cd backend
..\.venv\Scripts\python.exe scripts/seed_data.py
cd ..
```

#### Step 2.7: Start the FastAPI Server

Navigate to the `backend` folder and start Uvicorn on port `8001`:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

The backend will be available at:
- **API Root**: [http://localhost:8001/](http://localhost:8001/)
- **Health Check**: [http://localhost:8001/health](http://localhost:8001/health)
- **Interactive Swagger Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Alternative ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

### 3. Frontend Setup

Open a second terminal window at the project root (`smart-recruitment-ai`):

#### Step 3.1: Navigate to Frontend Directory & Install Dependencies

```powershell
cd frontend
npm install
```

#### Step 3.2: Configure Frontend Environment (Optional)

```powershell
Copy-Item .env.example .env
```

*(By default, it connects to `http://localhost:8001`)*.

#### Step 3.3: Verify Frontend Code Quality

```powershell
npm run lint
npm run build
```

#### Step 3.4: Start Vite Development Server

```powershell
npm run dev
```

Open your browser at:
- **Frontend Application**: [http://localhost:5173/](http://localhost:5173/)

---

### 4. Running Automated Tests

Run tests using the project's root virtual environment:

#### Run Parser Unit and API Tests Specifically:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_resume_parser_unit.py backend\tests\test_resume_parser_api.py -v
```

#### Run the Complete Backend Regression Suite:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Expected output:
```text
80 passed, 5 warnings in 9.64s
```

---

## Resume Parsing Engine (Stage 8)

The system features a **100% offline, deterministic, non-LLM resume parsing engine** that extracts structured candidate information, matches skills to a canonical database taxonomy, extracts verbatim evidence sentences, and determines contextual skill support without calling external AI APIs.

### Architecture
- **`extract.py`**: Reads PDF (via `pdfplumber`) and DOCX (via `python-docx` including tables). Enforces a strict 10-page ceiling and rejects empty or image-only scanned files with `"no extractable text"`.
- **`clean.py`**: Normalizes Unicode, bullets, and line wrapping while strictly preserving technical terms (`C++`, `C#`, `.NET`, `Node.js`, `Next.js`, `CI/CD`).
- **`sections.py`**: Heading-based section detector mapping variations into canonical categories (`summary`, `education`, `skills`, `projects`, `experience`, `certifications`, `languages`, `achievements`) while preserving header content.
- **`entities.py`**: Regex and spaCy NER extraction of contacts (email, phone, LinkedIn, GitHub, name), education history (degrees, institutions, CGPA, graduation years), work experience, projects, and certifications.
- **`skills.py`**: Canonical skill matcher using `skill_aliases.json` (60+ aliases) and the database `Skill` taxonomy. Assigns `supported_by_context = true` if skills appear in project or experience sections.
- **`parser.py`**: Orchestrator returning structured data and cleaned text.

### Privacy Decision
> **Anti-Bias Privacy Guarantee**: Sensitive demographic attributes—including gender, date of birth, age, marital status, religion, caste, nationality, and photographs—are **strictly excluded from extraction and storage** to prevent discrimination in candidate ranking.

### Recruiter Privacy Boundaries
- Recruiters only access parsed resume data through the authorized job applicant endpoint: `GET /applications/{application_id}`.
- If `reveal_contact=False`, candidate contact details (including those inside `parsed_json`) are automatically redacted before transmission.
- `Resume.raw_text` and physical storage paths are **never exposed to recruiters**.

---

## Authentication & Authorization

The system provides a hardened, role-based authentication and authorization mechanism built on FastAPI, Pydantic, Argon2 password hashing, and PyJWT.

### User Roles
- **candidate**: Job applicant; profile includes contact details, headline, resume management, and GDPR/AI consent timestamp.
- **recruiter**: Hiring manager; profile includes company information, job posting access, and applicant evaluation dossiers.
- **admin**: System administrator; provisioned securely via CLI/environment variables.

### Endpoints
| Method | Path | Access | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Register new candidate or recruiter. |
| `POST` | `/auth/login` | Public | Authenticates user; returns JWT. |
| `GET` | `/auth/me` | Authenticated | Returns current authenticated user profile. |
| `POST` | `/resumes` | Candidate | Upload PDF or DOCX resume (max 5 MB). |
| `GET` | `/resumes` | Candidate | List candidate's uploaded resumes. |
| `POST` | `/resumes/{id}/parse` | Candidate (Owner) | Synchronously parse resume into structured JSON and save skills. |
| `GET` | `/resumes/{id}/parsed` | Candidate (Owner) | Retrieve parsed structured resume dossier and skills. |
| `GET` | `/applications/{id}` | Recruiter (Job Owner) | View applicant dossier with privacy-controlled contact reveal and skill evidence. |

---

## Roadmap

- [x] **Phase 1**: Project skeleton, health check endpoint, React + Tailwind dashboard
- [x] **Phase 2**: User authentication (JWT), RBAC, audit logging & PostgreSQL SQLAlchemy data models
- [x] **Phase 3 (Stage 8)**: Non-LLM offline deterministic resume parser (PDF/DOCX), skill evidence & recruiter privacy controls
- [ ] **Phase 4**: Virtual interview engine (adaptive questions & speech-to-text)
- [ ] **Phase 5**: Candidate evaluation scoring & PDF recruiter report generation
