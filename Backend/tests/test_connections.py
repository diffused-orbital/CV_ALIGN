"""End-to-end connection tests for every frontend->backend endpoint.

Each test maps to a real call made by the React frontend (see src/api.js and
src/pages/*.jsx) and verifies routing, authentication, role-based access,
DB persistence and the response contract the frontend relies on.
"""
import io
import pytest

from conftest import _register, _login, _create_profile


def _post_job(client, headers, title="Backend Engineer", company="Acme"):
    return client.post(
        "/job/upload",
        headers=headers,
        data={"title": title, "company": company},
        files={"jd_file": ("jd.pdf", io.BytesIO(b"%PDF-1.4 jd"), "application/pdf")},
    )


def _apply(client, headers, job_id):
    # One-click apply: JSON body, uses the candidate's saved profile.
    return client.post("/apply", headers=headers, json={"job_id": job_id})


# ---- Auth (login.jsx / register.jsx via api.js) -----------------------------

class TestAuth:
    def test_register_returns_user(self, client):
        r = _register(client, "newuser", "new@test.com", "Passw0rd!", "candidate")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["email"] == "new@test.com"
        assert body["role"] == "candidate"

    def test_duplicate_email_rejected(self, client):
        _register(client, "dup1", "dup@test.com", "Passw0rd!", "candidate")
        r = _register(client, "dup2", "dup@test.com", "Passw0rd!", "candidate")
        assert r.status_code == 400

    def test_login_returns_token(self, client):
        _register(client, "loginu", "login@test.com", "Passw0rd!", "recruiter")
        r = _login(client, "login@test.com", "Passw0rd!")
        assert r.status_code == 200, r.text
        assert r.json()["token_type"] == "bearer"
        assert r.json()["access_token"]

    def test_login_wrong_password(self, client):
        _register(client, "wp", "wp@test.com", "Passw0rd!", "recruiter")
        r = _login(client, "wp@test.com", "nope")
        assert r.status_code == 401

    def test_me_endpoints(self, client, candidate_headers):
        r1 = client.get("/me", headers=candidate_headers)
        r2 = client.get("/auth/me", headers=candidate_headers)
        assert r1.status_code == 200 and r1.json()["role"] == "candidate"
        assert r2.status_code == 200 and r2.json()["email"] == "cand1@test.com"

    def test_protected_requires_token(self, client):
        assert client.get("/me").status_code == 401


# ---- Candidate profile (profile.jsx) ----------------------------------------

class TestProfile:
    def test_profile_empty_initially(self, client, candidate_headers):
        r = client.get("/candidate/profile", headers=candidate_headers)
        assert r.status_code == 200
        assert r.json()["complete"] is False

    def test_create_profile(self, client, candidate_headers):
        r = _create_profile(client, candidate_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["complete"] is True
        assert body["full_name"] == "Cand One"
        # And it is now readable
        got = client.get("/candidate/profile", headers=candidate_headers).json()
        assert got["complete"] is True

    def test_profile_requires_resume_first_time(self, client, candidate_headers):
        r = _create_profile(client, candidate_headers, with_resume=False)
        assert r.status_code == 400

    def test_profile_non_pdf_rejected(self, client, candidate_headers):
        r = client.post(
            "/candidate/profile",
            headers=candidate_headers,
            data={"full_name": "X", "contact": "1", "cgpa": 8.0,
                  "institute": "I", "degree": "D"},
            files={"resume": ("cv.txt", io.BytesIO(b"nope"), "text/plain")},
        )
        assert r.status_code == 400

    def test_recruiter_has_no_profile(self, client, recruiter_headers):
        assert client.get("/candidate/profile", headers=recruiter_headers).status_code == 403

    def test_update_profile_keeps_existing_resume(self, client, candidate_headers):
        _create_profile(client, candidate_headers)
        # Update text fields only, no new resume file
        r = client.post(
            "/candidate/profile",
            headers=candidate_headers,
            data={"full_name": "Renamed", "contact": "2", "cgpa": 9.0,
                  "institute": "NIT", "degree": "MTech"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["complete"] is True
        assert r.json()["full_name"] == "Renamed"


# ---- Jobs (jobupload.jsx + candidate dashboard) -----------------------------

class TestJobs:
    def test_recruiter_can_post_job(self, client, recruiter_headers):
        r = _post_job(client, recruiter_headers)
        assert r.status_code == 200, r.text
        assert "job_id" in r.json()

    def test_candidate_cannot_post_job(self, client, candidate_headers):
        assert _post_job(client, candidate_headers).status_code == 403

    def test_list_jobs_endpoint(self, client, recruiter_headers, candidate_headers):
        _post_job(client, recruiter_headers, title="Frontend Dev", company="Globex")
        r = client.get("/jobs", headers=candidate_headers)
        assert r.status_code == 200, r.text
        jobs = r.json()["jobs"]
        assert len(jobs) >= 1
        job = jobs[0]
        assert {"id", "title", "company", "applied", "status"} <= set(job.keys())
        assert job["applied"] is False

    def test_list_jobs_requires_auth(self, client):
        assert client.get("/jobs").status_code == 401


# ---- Apply (candidate dashboard one-click) ----------------------------------

class TestApply:
    def test_candidate_can_apply(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        r = _apply(client, candidate_headers, job_id)
        assert r.status_code == 200, r.text
        assert "application_id" in r.json()
        # /jobs now reports it as applied
        jobs = client.get("/jobs", headers=candidate_headers).json()["jobs"]
        assert any(j["id"] == job_id and j["applied"] for j in jobs)

    def test_apply_requires_profile(self, client, recruiter_headers, candidate_headers):
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        r = _apply(client, candidate_headers, job_id)  # no profile created
        assert r.status_code == 400

    def test_recruiter_cannot_apply(self, client, recruiter_headers):
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        assert _apply(client, recruiter_headers, job_id).status_code == 403

    def test_duplicate_application_rejected(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        assert _apply(client, candidate_headers, job_id).status_code == 200
        assert _apply(client, candidate_headers, job_id).status_code == 400

    def test_apply_to_missing_job(self, client, candidate_headers):
        _create_profile(client, candidate_headers)
        assert _apply(client, candidate_headers, 99999).status_code == 404


# ---- Candidate dashboard (candidatedashboard.jsx) ---------------------------

class TestCandidateDashboard:
    def test_candidate_dashboard(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        _apply(client, candidate_headers, job_id)
        r = client.get("/candidate/dashboard", headers=candidate_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["candidate"] == "cand_one"
        assert body["applications"][0]["status"] == "Pending"

    def test_recruiter_blocked_from_candidate_dashboard(self, client, recruiter_headers):
        assert client.get("/candidate/dashboard", headers=recruiter_headers).status_code == 403


# ---- Recruiter dashboard + job details --------------------------------------

class TestRecruiterDashboard:
    def test_dashboard_summary(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        _apply(client, candidate_headers, job_id)
        r = client.get("/recruiter/dashboard", headers=recruiter_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["total_jobs_posted"] == 1
        assert body["jobs"][0]["resumes_applied"] == 1

    def test_candidate_blocked_from_recruiter_dashboard(self, client, candidate_headers):
        assert client.get("/recruiter/dashboard", headers=candidate_headers).status_code == 403

    def test_job_details_returns_candidates(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        _apply(client, candidate_headers, job_id)
        r = client.get(f"/recruiter/job/{job_id}", headers=recruiter_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["job_title"] == "Backend Engineer"
        cand = body["candidates"][0]
        assert "application_id" in cand
        assert cand["candidate_name"] == "cand_one"
        assert cand["status"] == 0

    def test_job_details_owner_only(self, client, recruiter_headers, recruiter2_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        _apply(client, candidate_headers, job_id)
        assert client.get(f"/recruiter/job/{job_id}", headers=recruiter2_headers).status_code == 404


# ---- Accept / Reject + RBAC -------------------------------------------------

class TestAcceptReject:
    def _setup_application(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        return _apply(client, candidate_headers, job_id).json()["application_id"], job_id

    def test_owner_can_accept(self, client, recruiter_headers, candidate_headers):
        app_id, _ = self._setup_application(client, recruiter_headers, candidate_headers)
        r = client.post(f"/application/{app_id}/accept", headers=recruiter_headers)
        assert r.status_code == 200, r.text
        dash = client.get("/candidate/dashboard", headers=candidate_headers).json()
        assert dash["applications"][0]["status"] == "Accepted"

    def test_owner_can_reject(self, client, recruiter_headers, candidate_headers):
        app_id, _ = self._setup_application(client, recruiter_headers, candidate_headers)
        r = client.post(f"/application/{app_id}/reject", headers=recruiter_headers)
        assert r.status_code == 200, r.text
        dash = client.get("/candidate/dashboard", headers=candidate_headers).json()
        assert dash["applications"][0]["status"] == "Rejected"

    def test_candidate_cannot_accept(self, client, recruiter_headers, candidate_headers):
        app_id, _ = self._setup_application(client, recruiter_headers, candidate_headers)
        assert client.post(f"/application/{app_id}/accept", headers=candidate_headers).status_code == 403

    def test_non_owner_recruiter_cannot_accept(self, client, recruiter_headers, recruiter2_headers, candidate_headers):
        app_id, _ = self._setup_application(client, recruiter_headers, candidate_headers)
        assert client.post(f"/application/{app_id}/accept", headers=recruiter2_headers).status_code == 403

    def test_accept_missing_application(self, client, recruiter_headers):
        assert client.post("/application/99999/accept", headers=recruiter_headers).status_code == 404


# ---- Job lifecycle: close + generate (Task 3) -------------------------------

class TestJobLifecycle:
    def test_job_details_includes_is_open(self, client, recruiter_headers):
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        r = client.get(f"/recruiter/job/{job_id}", headers=recruiter_headers)
        assert r.json()["is_open"] is True

    def test_close_job_blocks_new_applications(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        r = client.post(f"/recruiter/job/{job_id}/close", headers=recruiter_headers)
        assert r.status_code == 200 and r.json()["is_open"] is False
        # Candidate sees it as closed and can no longer apply
        jobs = client.get("/jobs", headers=candidate_headers).json()["jobs"]
        assert any(j["id"] == job_id and j["is_open"] is False for j in jobs)
        assert _apply(client, candidate_headers, job_id).status_code == 400

    def test_close_requires_owner(self, client, recruiter_headers, recruiter2_headers, candidate_headers):
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        assert client.post(f"/recruiter/job/{job_id}/close", headers=recruiter2_headers).status_code == 404
        assert client.post(f"/recruiter/job/{job_id}/close", headers=candidate_headers).status_code == 403

    def test_generate_requires_closed_job(self, client, recruiter_headers):
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        assert client.post(f"/recruiter/job/{job_id}/generate", headers=recruiter_headers).status_code == 400

    def test_generate_scores_persists_top_candidates(self, client, recruiter_headers, candidate_headers, monkeypatch):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        _apply(client, candidate_headers, job_id)
        client.post(f"/recruiter/job/{job_id}/close", headers=recruiter_headers)

        # Key the mocked model output by the applied resume's UUID stem
        from conftest import TestingSessionLocal
        from app.models.application import Application
        from pathlib import Path
        db = TestingSessionLocal()
        try:
            appn = db.query(Application).filter(Application.job_id == job_id).first()
            stem = Path(appn.resume_path.split("?")[0]).stem
        finally:
            db.close()

        import app.routers.recruiter as recruiter_mod
        monkeypatch.setattr(recruiter_mod, "score_cvs_v2", lambda *a, **k: [
            {"Name": stem, "Score": 91.0, "Feedback": "Strengths: Great.\nWeaknesses: None."}
        ])

        r = client.post(f"/recruiter/job/{job_id}/generate", headers=recruiter_headers)
        assert r.status_code == 200, r.text
        assert r.json()["candidates"][0]["score"] == 91.0
        got = client.get(f"/recruiter/job/{job_id}", headers=recruiter_headers).json()
        assert got["candidates"][0]["score"] == 91.0
        assert "Great" in got["candidates"][0]["strengths"]

    def test_generate_requires_owner(self, client, recruiter_headers, recruiter2_headers):
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        client.post(f"/recruiter/job/{job_id}/close", headers=recruiter_headers)
        assert client.post(f"/recruiter/job/{job_id}/generate", headers=recruiter2_headers).status_code == 404


# ---- Score persistence helpers ----------------------------------------------

class TestScorePersistence:
    def test_split_feedback(self):
        from app.routers.application import _split_feedback
        s, w = _split_feedback("Strengths: Strong Python.\nWeaknesses: No cloud experience.")
        assert "Strong Python" in s
        assert "No cloud experience" in w

    def test_split_feedback_empty(self):
        from app.routers.application import _split_feedback
        assert _split_feedback(None) == (None, None)

    def test_persist_scores_maps_to_application(self, client, recruiter_headers, candidate_headers):
        _create_profile(client, candidate_headers)
        job_id = _post_job(client, recruiter_headers).json()["job_id"]
        _apply(client, candidate_headers, job_id)

        from conftest import TestingSessionLocal
        from app.models.application import Application
        from app.routers.application import _persist_scores
        from pathlib import Path

        db = TestingSessionLocal()
        try:
            appn = db.query(Application).filter(Application.job_id == job_id).first()
            stem = Path(appn.resume_path.split("?")[0]).stem
            _persist_scores(db, job_id, [{
                "Name": stem,
                "Score": 87.5,
                "Feedback": "Strengths: Great fit.\nWeaknesses: Junior.",
            }])
            db.refresh(appn)
            assert appn.score == 87.5
            assert "Great fit" in appn.strengths
            assert "Junior" in appn.weaknesses
        finally:
            db.close()

        r = client.get(f"/recruiter/job/{job_id}", headers=recruiter_headers)
        assert r.json()["candidates"][0]["score"] == 87.5
