# 🧠 CV_ALIGN – AI-powered CV Evaluation Platform

CV_ALIGN is an intelligent, full-stack platform that revolutionizes the way companies evaluate resumes. It enables recruiters to post jobs and candidates to apply by uploading CVs. These resumes are automatically scored and analyzed using a hybrid AI approach combining semantic similarity, keyword mapping, and LLM-based feedback.

Companies can then view ranked applications with detailed feedback and make informed accept/reject decisions — which are instantly reflected on the candidate's dashboard. This eliminates the hassle of manual screening and makes the recruitment process seamless.

---

## 🚀 Features

- 🔐 **Authentication System** for both recruiters and candidates
- 🧾 **Job Posting & Resume Submission** with Cloudinary-powered upload
- 📊 **Automated Resume Evaluation** using AI models
- 📈 **Score-based Ranking** of candidates per job
- 💬 **LLM-generated Feedback** on resume strengths and weaknesses (via Google Gemini)
- ✅ Recruiters can **accept/reject applications** from their dashboard
- 🔄 Candidates get **real-time status updates** on their submissions

---

## 🛠 Tech Stack

### 🧩 Frontend
- **React + Vite** – lightweight and fast SPA setup
- **Vanilla CSS** – for custom UI styling
- **React Router DOM** – for routing

### 🔧 Backend
- **FastAPI** – modern Python web framework
- **Python 3.x**

### 🗃️ Database & ORM
- **SQLite** (can be swapped with PostgreSQL/MySQL)
- **SQLAlchemy** – ORM for schema and queries

### 🔐 Authentication
- **JWT (JSON Web Tokens)** – for secure login sessions
- **bcrypt** – for password hashing

### ☁️ Cloud/File Storage
- **Cloudinary** – for uploading resumes and job descriptions

### 🤖 AI Model Stack
- **Sentence Transformers** – semantic similarity scoring
- **TF-IDF Matching** – keyword-based relevance scoring
- **LangChain + Google Gemini** – LLM-based feedback generation
- **spaCy, Regex, NER** – for information extraction
- **PyPDF2 / Mammoth / Textract** – for file parsing

---

## 📂 Folder Structure

```
CV_ALIGN/
├── Backend/
│   └── app/                     # FastAPI backend app
│
├── Frontend/
│   └── my-app/                  # Vite + React frontend
│
├── Model/
│   └── new_main.py             # Resume evaluation & scoring logic
│
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🧠 Model Pipeline Overview

```
Resume File
   │
   ├─▶ 1. Document Ingestion & OCR Parsing
   │     (PyPDF2, Mammoth, Textract, Tesseract)
   │
   ├─▶ 2. Information Extraction
   │     (Regex, spaCy, NER)
   │
   ├─▶ 3. Preprocessing & Synonym Mapping
   │     (custom JSON maps + keyword expansion)
   │
   ├─▶ 4. TF-IDF + Embedding Similarity
   │     (Sentence Transformers + cosine similarity)
   │
   ├─▶ 5. Experience Scoring
   │     (custom logic on titles & dates)
   │
   ├─▶ 6. LLM Verdict via LangChain + Gemini
```

---

## 🧪 Setup & Installation

### 🔧 Backend

```bash
cd CV_ALIGN/Backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

---

### 🌐 Frontend

```bash
cd CV_ALIGN/Frontend/my-app
npm install
npm run dev
```

App runs at: `http://localhost:5173`

---

### 🤖 Resume Evaluation Model (Manual Test)

Model is auto-triggered on `/apply`, but for testing:

```bash
cd CV_ALIGN/Model
pip install -r requirements.txt
python new_main.py
```

---

## 👨‍💻 Contributors

- [**Sanidhya Srivastava**](https://github.com/diffused-orbital)
- [**Arnav Tiku**](https://github.com/T-arn21)
- [**Devansh Jangid**](https://github.com/devanshjangid2005)

---

## 📄 License

This project is currently **not licensed**.
