# 🧠 CV_ALIGN – AI-powered CV Evaluation Platform

CV_ALIGN is a full-stack platform that helps companies evaluate resumes against a
job description. Recruiters post jobs; candidates fill in a profile once and apply
to open roles with a single click. When a recruiter closes a job, they can run a
hybrid AI model (semantic similarity + keyword matching + LLM feedback) to rank the
applicants and generate per-candidate strengths and weaknesses, then accept or
reject them — with the outcome reflected instantly on the candidate's dashboard.

---

## 🚀 Features

- 🔐 **Authentication & role-based access** for recruiters and candidates (JWT + bcrypt)
- 🧾 **Job posting** with the job description uploaded to Cloudinary
- 👤 **Candidate profile** — enter details and upload a resume **once**, then apply with one click
- 📋 **Open-role browsing** — candidates see all open roles and their own application status
- 🚦 **Job open/closed lifecycle** — recruiters close a job to stop new applications
- 🤖 **On-demand scoring** — after closing, a recruiter clicks **Generate** to rank the top candidates with strengths/weaknesses
- ✅ Recruiters **accept/reject** applications (only for their own jobs)
- 🔄 Candidates get **real-time status updates** and see “No longer accepting” for closed roles
- 💬 **Inline, specific error messages** across the UI (no popups)

---

## 🛠 Tech Stack

- **Frontend:** React + Vite, React Router DOM, Axios, vanilla CSS
- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Auth:** JWT (python-jose), bcrypt (passlib)
- **Storage:** Cloudinary (resumes & job descriptions)
- **AI model:** Sentence-Transformers + TF-IDF + experience scoring, LangChain + Google Gemini for feedback, spaCy/NLTK/PyMuPDF/PyPDF2 for extraction

---

## 📂 Folder Structure

```
CV_ALIGN/
├── Backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & router wiring
│   │   ├── config.py            # Loads secrets from .env
│   │   ├── database.py          # SQLAlchemy engine/session + table setup
│   │   ├── models/              # user, job, application, profile
│   │   ├── routers/             # auth, job, application, candidate, recruiter
│   │   ├── schemas/             # Pydantic schemas
│   │   └── utils/               # deps, token
│   ├── tests/                   # Backend test suite (pytest)
│   ├── .env.example             # Backend environment variables
│   └── requirements-dev.txt     # Test-only dependencies
│
├── Frontend/
│   └── my-app/                  # Vite + React frontend
│       ├── src/config.js        # API base URL (VITE_API_URL)
│       └── .env.example         # Frontend environment variables
│
├── New_Model/
│   ├── new_main.py              # score_cvs_v2(): fetch from Cloudinary + rank
│   └── functions/               # extraction, tokenizing, scoring
│
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🔑 Environment Variables (Cloudinary, Gemini, JWT)

Secrets are **not** committed. Copy the example files and fill them in locally
(the real `.env` files are gitignored).

**Backend** — copy `Backend/.env.example` to `Backend/.env`:

| Variable | Description |
|---|---|
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `GOOGLE_API_KEY` | Google Gemini API key (used by LangChain) |
| `JWT_SECRET_KEY` | Secret used to sign JWTs |
| `JWT_ALGORITHM` | JWT algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default `60`) |

**Frontend** — optionally copy `Frontend/my-app/.env.example` to `Frontend/my-app/.env`:

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL (defaults to `http://localhost:8000`) |

---

## 🧪 Setup & Installation

### 🔧 Backend

```bash
cd CV_ALIGN
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# create Backend/.env from the example and fill in your keys
cd Backend
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### 🌐 Frontend

```bash
cd CV_ALIGN/Frontend/my-app
npm install
npm run dev
```

App runs at `http://localhost:5173`.

### ✅ Running the backend tests

The suite uses an isolated in-memory database and mocks Cloudinary/Gemini, so no
real credentials or the heavy ML stack are required.

```bash
pip install -r Backend/requirements-dev.txt
cd Backend
pytest tests/
```

---

## 🔄 How it works

**Candidate**
1. Register (role = candidate) and log in.
2. Fill in your **profile** once (name, contact, CGPA, degree, institute) and upload a resume — stored on Cloudinary.
3. On the dashboard, browse **open roles** and click **Apply** — the saved profile and resume are reused automatically.
4. Track each application's status; closed roles show **“No longer accepting applications.”**

**Recruiter**
1. Register (role = recruiter), log in, and **post a job** (uploads the JD to Cloudinary).
2. Open a job to see its applicants. Click **Close applications** to stop new applications.
3. Click **Generate** to run the scoring model over all applicants and rank the top candidates with strengths/weaknesses.
4. **Accept / Reject** candidates — the status updates on their dashboard.

---

## 📡 API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Log in, returns a JWT |
| POST | `/auth/forgot-password` | Request a password-reset token for an email |
| POST | `/auth/reset-password` | Set a new password using a reset token |
| GET | `/auth/me`, `/me` | Current user |
| GET | `/jobs` | List jobs (with the caller's applied state/status) |
| POST | `/job/upload` | Recruiter posts a job (JD → Cloudinary) |
| GET | `/candidate/profile` | Get the candidate's profile |
| POST | `/candidate/profile` | Create/update profile + upload resume |
| POST | `/apply` | One-click apply (`{ "job_id": N }`) using the saved profile |
| GET | `/candidate/dashboard` | Candidate's applications |
| GET | `/recruiter/dashboard` | Recruiter's jobs summary |
| GET | `/recruiter/job/{id}` | Job detail with ranked candidates + `is_open` |
| POST | `/recruiter/job/{id}/close` | Close a job (owner only) |
| POST | `/recruiter/job/{id}/generate` | Score applicants, return top ranked (owner only) |
| POST | `/application/{id}/accept` | Accept an application (owner only) |
| POST | `/application/{id}/reject` | Reject an application (owner only) |

> The legacy `/score/`, `/cloud_score/` and `/upload_cv/` endpoints have been removed.

---

## 👨‍💻 Contributors

- [**Sanidhya Srivastava**](https://github.com/diffused-orbital)
- [**Arnav Tiku**](https://github.com/T-arn21)
- [**Devansh Jangid**](https://github.com/devanshjangid2005)

---

## 📄 License

This project is currently **not licensed**.
