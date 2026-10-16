import uuid

from sqlalchemy import select

from app.db.models import User


def register(client, role="STUDENT", email=None, department_id=None):
    email = email or f"{uuid.uuid4().hex}@example.edu"
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "StrongPass12345",
        "role": role,
        "department_id": department_id or client.department_id,
    })
    return email, response


def token_for(client, role="STUDENT", email=None):
    email, registration = register(client, role=role, email=email)
    assert registration.status_code == 201, registration.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass12345"})
    assert login.status_code == 200, login.text
    return email, login.json()["access_token"], registration.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_cors_allows_configured_nextjs_origin_only(api_client):
    allowed = api_client.options(
        "/api/v1/departments",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "authorization" in allowed.headers["access-control-allow-headers"].lower()

    rejected = api_client.get("/api/v1/departments", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in rejected.headers


def create_project(client, faculty_token):
    response = client.post("/api/v1/projects", headers=auth(faculty_token), json={
        "title": "NLP for scientific literature",
        "description": "Explore robust tools for analyzing scientific literature and scholarly evidence.",
        "required_skills": ["Python", "NLP"],
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_hashes_password_and_login_and_me_are_safe(api_client):
    email, response = register(api_client)
    assert response.status_code == 201
    assert "password" not in response.json()
    assert "password_hash" not in response.json()
    with api_client.test_sessions() as db:
        stored = db.scalar(select(User).where(User.email == email))
        assert stored.password_hash.startswith("$argon2id$")
        assert stored.password_hash != "StrongPass12345"
    login = api_client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass12345"})
    assert login.status_code == 200
    assert login.json()["user"]["email"] == email
    assert "password_hash" not in login.json()["user"]
    me = api_client.get("/api/v1/auth/me", headers=auth(login.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["id"] == response.json()["id"]
    assert "password_hash" not in me.json()


def test_duplicate_registration_invalid_login_and_validation(api_client):
    email, first = register(api_client, email="Duplicate@example.edu")
    assert first.status_code == 201
    _, duplicate = register(api_client, email=email.upper())
    assert duplicate.status_code == 409
    bad_login = api_client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword123"})
    assert bad_login.status_code == 401
    _, faculty_token, _ = token_for(api_client, role="FACULTY")
    bad_transition = api_client.patch(f"/api/v1/applications/{uuid.uuid4()}/status", headers=auth(faculty_token), json={"status": "PENDING"})
    assert bad_transition.status_code == 422
    invalid = api_client.post("/api/v1/auth/register", json={
        "name": "x", "email": "not-an-email", "password": "short", "role": "ADMIN", "department_id": api_client.department_id,
    })
    assert invalid.status_code == 422


def test_authentication_role_and_project_ownership_and_crud(api_client):
    _, student_token, _ = token_for(api_client)
    _, faculty_token, faculty = token_for(api_client, role="FACULTY")
    _, other_faculty_token, _ = token_for(api_client, role="FACULTY")
    assert api_client.get("/api/v1/auth/me").status_code == 401
    denied = api_client.post("/api/v1/projects", headers=auth(student_token), json={
        "title": "Unauthorized project", "description": "This request should be rejected for student role.",
    })
    assert denied.status_code == 403
    project = create_project(api_client, faculty_token)
    assert project["faculty_id"] == faculty["id"]
    assert api_client.get(f"/api/v1/projects/{project['id']}").status_code == 200
    listed = api_client.get("/api/v1/projects", params={"status": "OPEN", "department_id": api_client.department_id})
    assert listed.status_code == 200 and listed.json()["total"] >= 1
    forbidden = api_client.patch(f"/api/v1/projects/{project['id']}", headers=auth(other_faculty_token), json={"title": "Not mine"})
    assert forbidden.status_code == 403
    updated = api_client.patch(f"/api/v1/projects/{project['id']}", headers=auth(faculty_token), json={"title": "Updated research title"})
    assert updated.status_code == 200 and updated.json()["title"] == "Updated research title"
    closed = api_client.patch(f"/api/v1/projects/{project['id']}", headers=auth(faculty_token), json={"status": "CLOSED"})
    assert closed.status_code == 200 and closed.json()["status"] == "CLOSED"


def test_departments_list_detail_and_unknown_id(api_client):
    response = api_client.get("/api/v1/departments")
    assert response.status_code == 200
    assert any(item["id"] == api_client.department_id for item in response.json())
    detail = api_client.get(f"/api/v1/departments/{api_client.department_id}")
    assert detail.status_code == 200
    assert api_client.get(f"/api/v1/departments/{uuid.uuid4()}").status_code == 404


def test_student_interests_self_service_and_role_enforcement(api_client):
    _, student_token, student = token_for(api_client)
    _, other_student_token, _ = token_for(api_client)
    _, faculty_token, _ = token_for(api_client, role="FACULTY")
    payload = {"description": "Interested in robust natural language processing research.", "skills": ["Python", "NLP", "python"]}
    created = api_client.post("/api/v1/students/me/interests", headers=auth(student_token), json=payload)
    assert created.status_code == 201
    assert created.json()["student_id"] == student["id"]
    assert created.json()["skills"] == ["Python", "NLP"]
    assert "embedding" not in created.json()
    assert api_client.post("/api/v1/students/me/interests", headers=auth(student_token), json=payload).status_code == 409
    assert api_client.get("/api/v1/students/me/interests", headers=auth(other_student_token)).status_code == 404
    assert api_client.put("/api/v1/students/me/interests", headers=auth(other_student_token), json=payload).status_code == 200
    assert api_client.get("/api/v1/students/me/interests", headers=auth(faculty_token)).status_code == 403


def test_applications_submission_ownership_and_status_transitions(api_client):
    _, student_token, _ = token_for(api_client)
    _, other_student_token, _ = token_for(api_client)
    _, faculty_token, _ = token_for(api_client, role="FACULTY")
    _, other_faculty_token, _ = token_for(api_client, role="FACULTY")
    project = create_project(api_client, faculty_token)
    project_path = f"/api/v1/projects/{project['id']}/applications"
    application_payload = {"message": "My background in research and Python can support this project."}
    created = api_client.post(project_path, headers=auth(student_token), json=application_payload)
    assert created.status_code == 201
    application_id = created.json()["id"]
    assert api_client.post(project_path, headers=auth(student_token), json=application_payload).status_code == 409
    assert api_client.post(project_path, headers=auth(faculty_token), json=application_payload).status_code == 403
    assert len(api_client.get("/api/v1/applications/me", headers=auth(student_token)).json()) == 1
    assert api_client.get("/api/v1/projects/{}/applications".format(project["id"]), headers=auth(other_faculty_token)).status_code == 403
    assert len(api_client.get(project_path, headers=auth(faculty_token)).json()) == 1
    decision_path = f"/api/v1/applications/{application_id}/status"
    accepted = api_client.patch(decision_path, headers=auth(faculty_token), json={"status": "ACCEPTED"})
    assert accepted.status_code == 200 and accepted.json()["status"] == "ACCEPTED"
    assert api_client.patch(decision_path, headers=auth(faculty_token), json={"status": "REJECTED"}).status_code == 409
    assert api_client.patch(decision_path, headers=auth(other_faculty_token), json={"status": "REJECTED"}).status_code == 403
    assert api_client.patch(decision_path, headers=auth(student_token), json={"status": "REJECTED"}).status_code == 403


def test_closed_project_rejects_applications(api_client):
    _, student_token, _ = token_for(api_client)
    _, faculty_token, _ = token_for(api_client, role="FACULTY")
    project = create_project(api_client, faculty_token)
    api_client.patch(f"/api/v1/projects/{project['id']}", headers=auth(faculty_token), json={"status": "CLOSED"})
    response = api_client.post(f"/api/v1/projects/{project['id']}/applications", headers=auth(student_token), json={
        "message": "I would like to participate in the project research work."
    })
    assert response.status_code == 409
