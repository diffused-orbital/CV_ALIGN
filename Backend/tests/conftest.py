"""Shared fixtures: isolated in-memory DB + mocked external services.

These tests exercise the frontend<->backend connection contracts (routing,
auth, RBAC, DB persistence, response shapes). External services that the
wiring depends on -- Cloudinary storage and the Gemini-based scoring model --
are mocked so we test *our* code, not third-party APIs or the network.
"""
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Make the Backend package importable regardless of pytest's rootdir
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "synthetic-test-signing-secret-at-least-32-characters"
os.environ["CLOUDINARY_CLOUD_NAME"] = "test-cloud"
os.environ["CLOUDINARY_API_KEY"] = "synthetic-key"
os.environ["CLOUDINARY_API_SECRET"] = "synthetic-secret"

from app.database import Base
import app.database as database_mod
import app.routers.auth as auth_mod
import app.utils.deps as deps_mod
from app.main import app

# One shared in-memory SQLite connection for the whole test session
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Every router pulls a db session from one of these three get_db definitions
app.dependency_overrides[database_mod.get_db] = _override_get_db
app.dependency_overrides[auth_mod.get_db] = _override_get_db
app.dependency_overrides[deps_mod.get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _reset_db():
    """Give every test a clean database so tests don't pollute each other."""
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield


# Records every mocked Cloudinary upload call for assertions in tests.
UPLOAD_CALLS = []


def _fake_upload(*args, **kwargs):
    # Echo the requested public_id so each upload yields a unique URL,
    # mirroring how real Cloudinary keys uploads by public_id. For raw
    # uploads Cloudinary keeps an existing extension and appends the source
    # format only when the public_id has none.
    public_id = kwargs.get("public_id", "resource")
    url = f"https://res.cloudinary.com/test-cloud/raw/authenticated/s--testsignature--/v1/{public_id}"
    if not public_id.lower().endswith(".pdf"):
        url += ".pdf"
    UPLOAD_CALLS.append({"source": args[0] if args else None, "kwargs": kwargs})
    return {"secure_url": url, "public_id": public_id}


@pytest.fixture(autouse=True)
def _mock_external_services(monkeypatch):
    """Stub Cloudinary uploads (recording calls) for every test."""
    import cloudinary.uploader

    UPLOAD_CALLS.clear()
    monkeypatch.setattr(cloudinary.uploader, "upload", _fake_upload)
    monkeypatch.setattr(cloudinary.uploader, "destroy", lambda *a, **k: {"result": "ok"})
    import app.routers.application as application_mod
    monkeypatch.setattr(application_mod, "download_pdf", lambda url: pdf_bytes())
    yield


@pytest.fixture
def upload_calls():
    """Cloudinary upload calls recorded during the current test."""
    return UPLOAD_CALLS


@pytest.fixture
def client():
    return TestClient(app)


# ---- Auth helpers -----------------------------------------------------------

def _register(client, username, email, password, role):
    return client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password, "role": role},
    )


def _login(client, email, password):
    resp = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return resp


def _auth_header(client, username, email, password, role):
    _register(client, username, email, password, role)
    resp = _login(client, email, password)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recruiter_headers(client):
    return _auth_header(client, "rec_one", "rec1@test.com", "Passw0rd!", "recruiter")


@pytest.fixture
def recruiter2_headers(client):
    return _auth_header(client, "rec_two", "rec2@test.com", "Passw0rd!", "recruiter")


@pytest.fixture
def candidate_headers(client):
    return _auth_header(client, "cand_one", "cand1@test.com", "Passw0rd!", "candidate")


def _create_profile(client, headers, full_name="Cand One", contact="9990001111",
                    cgpa=8.5, institute="IIT", degree="BTech", with_resume=True):
    import io
    files = {}
    if with_resume:
        files["resume"] = ("resume.pdf", io.BytesIO(pdf_bytes()), "application/pdf")
    return client.post(
        "/candidate/profile",
        headers=headers,
        data={
            "full_name": full_name,
            "contact": contact,
            "cgpa": cgpa,
            "institute": institute,
            "degree": degree,
        },
        files=files or None,
    )


@pytest.fixture
def candidate_with_profile(client, candidate_headers):
    _create_profile(client, candidate_headers)
    return candidate_headers


def pdf_bytes():
    from io import BytesIO
    from PyPDF2 import PdfWriter
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(stream)
    return stream.getvalue()


@pytest.fixture
def sent_emails(monkeypatch):
    import app.routers.auth as auth_mod
    from app import config
    monkeypatch.setattr(config, "SMTP_HOST", "127.0.0.1")
    monkeypatch.setattr(config, "SMTP_FROM", "no-reply@cv-align.test")
    messages = []
    monkeypatch.setattr(auth_mod, "send_reset_email", lambda email, token, digest: messages.append({"email": email, "token": token}))
    return messages
