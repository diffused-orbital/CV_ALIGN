import io
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from conftest import TestingSessionLocal, _create_profile, _login, _register, pdf_bytes
from test_connections import _post_job, _apply
from app.database import Base
from app.models.application import Application
from app.models.job import Job
from app.models.password_reset import PasswordReset
from app.models.profile import Profile
from app.models.user import User
from app.routers.application import _persist_scores, apply_to_job
from app.schemas.application import ApplicationCreate


def test_reset_is_private_single_use_and_revokes_sessions(client, sent_emails):
    _register(client, "reset-security", "secure@test.com", "OldPass1!", "candidate")
    access = _login(client, "secure@test.com", "OldPass1!").json()["access_token"]
    known = client.post("/auth/forgot-password", json={"email": "secure@test.com"})
    unknown = client.post("/auth/forgot-password", json={"email": "unknown@test.com"})
    assert known.json() == unknown.json()
    assert "reset_token" not in known.json()
    token = sent_emails[-1]["token"]
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    from jose import jwt
    from app.utils.token import SECRET_KEY, ALGORITHM
    legacy_reset = jwt.encode(
        {"sub": "secure@test.com", "purpose": "reset", "auth_version": 0, "exp": int(time.time()) + 60},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    # A correctly signed reset token is still forbidden on protected routes.
    assert client.get("/me", headers={"Authorization": f"Bearer {legacy_reset}"}).status_code == 401
    body = {"token": token, "new_password": "NewPass1!"}
    assert client.post("/auth/reset-password", json=body).status_code == 200
    assert client.post("/auth/reset-password", json=body).status_code == 400
    assert client.get("/me", headers={"Authorization": f"Bearer {access}"}).status_code == 401
    assert _login(client, "secure@test.com", "NewPass1!").status_code == 200


def test_expired_and_replaced_reset_links_are_rejected(client, sent_emails):
    _register(client, "reset-expiry", "expiry@test.com", "OldPass1!", "candidate")
    for _ in range(2):
        client.post("/auth/forgot-password", json={"email": "expiry@test.com"})
    assert client.post("/auth/reset-password", json={"token": sent_emails[0]["token"], "new_password": "NewPass1!"}).status_code == 400
    with TestingSessionLocal() as db:
        db.execute(update(PasswordReset).values(expires_at=int(time.time()) - 1))
        db.commit()
    assert client.post("/auth/reset-password", json={"token": sent_emails[1]["token"], "new_password": "NewPass1!"}).status_code == 400


def test_reset_requests_are_rate_limited_for_unknown_accounts(client, sent_emails):
    for _ in range(5):
        assert client.post("/auth/forgot-password", json={"email": "unknown@test.com"}).status_code == 200
    assert client.post("/auth/forgot-password", json={"email": "unknown@test.com"}).status_code == 429


def test_passwords_are_never_logged(client, capsys):
    _register(client, "log-test", "logs@test.com", "NeverLogThis!", "candidate")
    captured = capsys.readouterr()
    assert "NeverLogThis!" not in captured.out + captured.err


def test_filename_is_ignored_and_uploads_are_private(client, recruiter_headers, candidate_headers, upload_calls, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.post("/job/upload", headers=recruiter_headers,
                           data={"title": "Same title", "company": "Same company"},
                           files={"jd_file": ("../../escape.pdf", io.BytesIO(pdf_bytes()), "application/pdf")})
    assert response.status_code == 200
    assert list(tmp_path.rglob("*.pdf")) == []
    assert upload_calls[-1]["kwargs"]["type"] == "authenticated"
    assert client.get("/uploads/profiles/1/test.pdf").status_code == 404
    _create_profile(client, candidate_headers)
    assert client.get("/candidate/profile/resume", headers=candidate_headers).status_code == 200
    assert client.get("/candidate/profile/resume").status_code == 401


@pytest.mark.parametrize("content", [b"not a PDF", b"%PDF-1.4 broken", b"x" * (10 * 1024 * 1024 + 1)])
def test_invalid_or_oversized_pdfs_never_reach_storage(client, recruiter_headers, upload_calls, content):
    response = client.post("/job/upload", headers=recruiter_headers,
                           data={"title": "Role", "company": "Company"},
                           files={"jd_file": ("jd.pdf", io.BytesIO(content), "application/pdf")})
    assert response.status_code in {400, 413}
    assert upload_calls == []
    with TestingSessionLocal() as db:
        assert db.query(Job).count() == 0


def test_identical_job_labels_do_not_share_assets(client, recruiter_headers, upload_calls):
    ids = [_post_job(client, recruiter_headers).json()["job_id"] for _ in range(2)]
    paths = [call["kwargs"]["public_id"] for call in upload_calls]
    assert len(set(paths)) == 2
    assert all(f"/jobs/{job_id}/jd/" in path for job_id, path in zip(ids, paths))


def test_score_results_use_application_ids_and_validate_every_result(client, recruiter_headers, candidate_headers):
    _create_profile(client, candidate_headers)
    job_id = _post_job(client, recruiter_headers).json()["job_id"]
    app_id = _apply(client, candidate_headers, job_id).json()["application_id"]
    with TestingSessionLocal() as db:
        assert _persist_scores(db, job_id, [{"ApplicationId": app_id, "Score": 89, "Feedback": "Strengths: Python.\nWeaknesses: Experience."}]) == 1
        for invalid in ([], [{"ApplicationId": 999, "Score": 0}], [{"ApplicationId": app_id, "Score": float("nan")}], [{"ApplicationId": app_id, "Score": 101}]):
            with pytest.raises(ValueError):
                _persist_scores(db, job_id, invalid)
            db.rollback()
        assert db.get(Application, app_id).score == 89


def test_failed_scoring_does_not_claim_success(client, recruiter_headers, candidate_headers, monkeypatch):
    _create_profile(client, candidate_headers)
    job_id = _post_job(client, recruiter_headers).json()["job_id"]
    _apply(client, candidate_headers, job_id)
    client.post(f"/recruiter/job/{job_id}/close", headers=recruiter_headers)
    monkeypatch.setattr("app.routers.recruiter.score_cvs_v2", lambda *args: [])
    assert client.post(f"/recruiter/job/{job_id}/generate", headers=recruiter_headers).status_code == 502


def test_signed_download_urls_keep_application_ids(monkeypatch):
    import sys
    from urllib.parse import parse_qs, urlparse
    from New_Model.new_main import score_cvs_v2

    recorded = []

    def process(resumes, jd):
        resumes = list(resumes)
        recorded.extend(resumes)
        return [{"ApplicationId": resume["ApplicationId"], "Score": 75} for resume in resumes]

    monkeypatch.setitem(sys.modules, "New_Model.functions.scoring", SimpleNamespace(process_resumes=process))
    base = "https://res.cloudinary.com/test-cloud/raw/authenticated/v1/cv_align/jobs/1"
    result = score_cvs_v2(base + "/jd/jd.pdf", [
        {"ApplicationId": 11, "ResumeUrl": base + "/resumes/a.pdf"},
        {"ApplicationId": 12, "ResumeUrl": base + "/resumes/b.pdf"},
    ])
    assert [r["ApplicationId"] for r in result] == [11, 12]
    assert [urlparse(r["ResumeUrl"]).path.split("/")[-1] for r in recorded] == ["download", "download"]
    assert [parse_qs(urlparse(r["ResumeUrl"]).query)["public_id"][0] for r in recorded] == ["cv_align/jobs/1/resumes/a.pdf", "cv_align/jobs/1/resumes/b.pdf"]


def test_simultaneous_applications_create_one_record(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.db'}", connect_args={"check_same_thread": False, "timeout": 20})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        candidate = User(username="concurrent", email="concurrent@test.com", role="candidate")
        db.add(candidate)
        db.flush()
        candidate_id = candidate.id
        job = Job(title="Role", company="Company", description_path="https://example.invalid/jd.pdf", is_open=True)
        db.add(job)
        db.flush()
        job_id = job.id
        db.add(Profile(user_id=candidate_id, resume_path="https://example.invalid/resume.pdf"))
        db.commit()
    monkeypatch.setattr("app.routers.application.upload_pdf_bytes", lambda *args: "https://example.invalid/snapshot.pdf")

    def apply():
        with Session(engine) as db:
            try:
                return apply_to_job(ApplicationCreate(job_id=job_id), db, SimpleNamespace(id=candidate_id, role="candidate"))
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: apply(), range(2)))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert 400 in results
    with Session(engine) as db:
        assert db.query(Application).count() == 1
    engine.dispose()


def test_authenticated_url_signature_is_not_part_of_public_id():
    from app.utils.storage import cloudinary_asset_reference
    public_id, _, delivery = cloudinary_asset_reference(
        "https://res.cloudinary.com/test-cloud/raw/authenticated/s--Example1--/v123/cv_align/jobs/1/resumes/a.pdf"
    )
    assert public_id == "cv_align/jobs/1/resumes/a.pdf"
    assert delivery == "authenticated"


def test_markdown_feedback_is_split_into_both_fields():
    from app.routers.application import _split_feedback
    strengths, weaknesses = _split_feedback("**Strengths:** Python.\n**Weaknesses:** Limited experience.")
    assert strengths == "Python."
    assert weaknesses == "Limited experience."


def test_closing_waits_for_an_in_flight_application(tmp_path, monkeypatch):
    from threading import Event
    from app.routers.recruiter import close_job

    engine = create_engine(f"sqlite:///{tmp_path / 'closing.db'}", connect_args={"check_same_thread": False, "timeout": 20})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        recruiter = User(username="owner", email="owner@test.com", role="recruiter")
        candidate = User(username="applicant", email="applicant@test.com", role="candidate")
        db.add_all([recruiter, candidate])
        db.flush()
        owner_id, candidate_id = recruiter.id, candidate.id
        job = Job(title="Role", company="Company", posted_by=owner_id, description_path="jd.pdf", is_open=True)
        db.add(job)
        db.flush()
        job_id = job.id
        db.add(Profile(user_id=candidate_id, resume_path="resume.pdf"))
        db.commit()
    uploading, release = Event(), Event()

    def upload(*args):
        uploading.set()
        assert release.wait(5)
        return "https://example.invalid/snapshot.pdf"

    monkeypatch.setattr("app.routers.application.upload_pdf_bytes", upload)

    def apply():
        with Session(engine) as db:
            return apply_to_job(ApplicationCreate(job_id=job_id), db, SimpleNamespace(id=candidate_id, role="candidate"))

    def close():
        with Session(engine) as db:
            return close_job(job_id, db, SimpleNamespace(id=owner_id, role="recruiter"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        applying = pool.submit(apply)
        assert uploading.wait(5)
        closing = pool.submit(close)
        release.set()
        assert applying.result(timeout=10)["application_id"]
        assert closing.result(timeout=10)["is_open"] is False
    with Session(engine) as db:
        with pytest.raises(HTTPException, match="no longer accepting"):
            apply_to_job(ApplicationCreate(job_id=job_id), db, SimpleNamespace(id=candidate_id, role="candidate"))
    engine.dispose()


def test_legacy_database_migration_preserves_rows_and_blocks_new_duplicates(tmp_path, monkeypatch):
    import app.database as database
    from sqlalchemy import inspect
    from sqlalchemy.exc import IntegrityError

    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER TABLE users DROP COLUMN auth_version")
        conn.exec_driver_sql("ALTER TABLE jobs DROP COLUMN is_open")
        conn.exec_driver_sql("CREATE TABLE old_applications AS SELECT * FROM applications")
        conn.exec_driver_sql("DROP TABLE applications")
        conn.exec_driver_sql("ALTER TABLE old_applications RENAME TO applications")
        conn.exec_driver_sql("INSERT INTO applications(id, user_id, job_id) VALUES (1, 1, 1), (2, 1, 1)")
    monkeypatch.setattr(database, "engine", engine)
    database.create_tables()
    database.create_tables()
    assert "auth_version" in {c["name"] for c in inspect(engine).get_columns("users")}
    assert "is_open" in {c["name"] for c in inspect(engine).get_columns("jobs")}
    with engine.begin() as conn:
        assert conn.exec_driver_sql("SELECT COUNT(*) FROM applications").scalar_one() == 2
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO applications(id, user_id, job_id) VALUES (3, 1, 1)")
    engine.dispose()


def test_scoring_pipeline_retains_ids_with_identical_signed_url_paths(monkeypatch):
    from New_Model.functions import scoring

    monkeypatch.setattr(scoring.exte, "read_job_description", lambda url: "Responsibilities Python")
    monkeypatch.setattr(scoring.exte, "read_resume", lambda url: "Skills Python")
    monkeypatch.setattr(scoring.exjd, "extract_job_details", lambda text: {"responsibilities": "Python"})
    monkeypatch.setattr(scoring.exres, "extract_sections", lambda text: {"skills": "Python"})
    monkeypatch.setattr(scoring.tk, "tokenize_sections", lambda sections: {k: v.split() for k, v in sections.items()})
    monkeypatch.setattr(scoring.ps, "embedding_score", lambda *args: 90)
    monkeypatch.setattr(scoring.ps, "tfidf_score", lambda *args: 80)
    monkeypatch.setattr(scoring.ps, "experience_score", lambda *args: 70)
    monkeypatch.setattr(scoring.ot, "create_synonym_mapping", lambda text: {})
    monkeypatch.setattr(scoring, "score_and_feedback", lambda *args: "Strengths: Python.\nWeaknesses: Experience.")
    results = scoring.process_resumes([
        {"ApplicationId": 11, "ResumeUrl": "https://example.invalid/raw/download?public_id=a.pdf"},
        {"ApplicationId": 12, "ResumeUrl": "https://example.invalid/raw/download?public_id=b.pdf"},
    ], "https://example.invalid/raw/download?public_id=jd.pdf")
    assert [result["ApplicationId"] for result in results] == [11, 12]
    assert [result["Score"] for result in results] == [83, 83]


def test_feedback_receives_readable_document_text_and_separate_instructions(monkeypatch):
    from langchain_core.runnables import RunnableLambda
    from New_Model.functions import scoring

    prompts = []

    def feedback(prompt, **kwargs):
        prompts.extend(prompt.to_messages())
        return "Strengths: Python.\nWeaknesses: Experience not demonstrated."

    monkeypatch.setattr(scoring, "ChatGoogleGenerativeAI", lambda **kwargs: RunnableLambda(feedback))
    result = scoring.score_and_feedback({"skills": "Python experience."}, {"responsibilities": "Build APIs."}, 83)
    assert prompts[0].type == "system"
    assert "untrusted document data" in prompts[0].content
    assert "Python experience." in prompts[1].content
    assert "Build APIs." in prompts[1].content
    assert result.startswith("Strengths:")
