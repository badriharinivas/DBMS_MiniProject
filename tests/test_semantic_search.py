import uuid

import app.services.embeddings as embeddings_module
from app.db.models import FacultyProject, StudentInterest
from app.services.embeddings import EMBEDDING_DIMENSION, EmbeddingUnavailableError


PASSWORD = "StrongPass12345"


def create_account(client, role):
    email = f"{uuid.uuid4().hex}@example.edu"
    response = client.post("/api/v1/auth/register", json={
        "name": "Matching Test User", "email": email, "password": PASSWORD,
        "role": role, "department_id": client.department_id,
    })
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return login.json()["access_token"], response.json()


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_project(client, faculty_token, title, description, skills=None):
    response = client.post("/api/v1/projects", headers=headers(faculty_token), json={
        "title": title, "description": description, "required_skills": skills or ["research"],
    })
    assert response.status_code == 201, response.text
    return response.json()


def create_interest(client, student_token, description, skills=None):
    return client.post("/api/v1/students/me/interests", headers=headers(student_token), json={
        "description": description, "skills": skills or ["research"],
    })


def test_project_and_interest_writes_generate_embeddings_and_updates_refresh_them(api_client):
    student_token, student = create_account(api_client, "STUDENT")
    faculty_token, _ = create_account(api_client, "FACULTY")
    project = create_project(api_client, faculty_token, "Wetland ecology", "Research on wetland restoration", ["Ecology"])
    interest = create_interest(api_client, student_token, "Wetland biodiversity research", ["ecology"])
    assert interest.status_code == 201
    assert "embedding" not in interest.json()

    with api_client.test_sessions() as db:
        stored_project = db.get(FacultyProject, uuid.UUID(project["id"]))
        stored_interest = db.query(StudentInterest).filter_by(student_id=uuid.UUID(student["id"])).one()
        assert len(stored_project.embedding) == EMBEDDING_DIMENSION
        assert len(stored_interest.embedding) == EMBEDDING_DIMENSION
        assert stored_project.embedding[1] == 1.0
        assert stored_interest.embedding[1] == 1.0

    project_update = api_client.patch(f"/api/v1/projects/{project['id']}", headers=headers(faculty_token), json={
        "title": "Language technology", "description": "Research on language systems and evaluation.",
    })
    assert project_update.status_code == 200
    interest_update = api_client.put("/api/v1/students/me/interests", headers=headers(student_token), json={
        "description": "Language technology research", "skills": ["NLP"],
    })
    assert interest_update.status_code == 200
    with api_client.test_sessions() as db:
        assert db.get(FacultyProject, uuid.UUID(project["id"])).embedding[0] == 1.0
        assert db.query(StudentInterest).filter_by(student_id=uuid.UUID(student["id"])).one().embedding[0] == 1.0


def test_recommendations_are_student_only_open_ordered_and_do_not_expose_vectors(api_client):
    student_token, _ = create_account(api_client, "STUDENT")
    faculty_token, _ = create_account(api_client, "FACULTY")
    interest = create_interest(api_client, student_token, "Neural language modeling research")
    assert interest.status_code == 201
    best = create_project(api_client, faculty_token, "Neural language modeling", "Research on neural language models", ["NLP"])
    lower = create_project(api_client, faculty_token, "Wetland ecology", "Research on wetland restoration", ["Ecology"])
    closed = create_project(api_client, faculty_token, "Neural language archive", "Research on neural language corpora", ["NLP"])
    placeholder = create_project(api_client, faculty_token, "Neural placeholder project", "Project awaiting its model embedding", ["NLP"])
    api_client.patch(f"/api/v1/projects/{closed['id']}", headers=headers(faculty_token), json={"status": "CLOSED"})
    with api_client.test_sessions() as db:
        db.get(FacultyProject, uuid.UUID(placeholder["id"])).embedding = [0.0] * EMBEDDING_DIMENSION
        db.commit()

    response = api_client.get("/api/v1/recommendations", headers=headers(student_token), params={"limit": 1})
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["id"] == best["id"]
    assert response.json()["items"][0]["similarity"] == 1.0
    assert "embedding" not in response.json()["items"][0]

    all_results = api_client.get("/api/v1/recommendations", headers=headers(student_token), params={"limit": 10}).json()["items"]
    assert [item["id"] for item in all_results[:2]] == [best["id"], lower["id"]]
    assert closed["id"] not in {item["id"] for item in all_results}
    assert placeholder["id"] not in {item["id"] for item in all_results}
    assert "faculty_name" in all_results[0] and "department_name" in all_results[0]
    assert api_client.get("/api/v1/recommendations").status_code == 401
    assert api_client.get("/api/v1/recommendations", headers=headers(faculty_token)).status_code == 403
    assert api_client.get("/api/v1/recommendations", headers=headers(student_token), params={"limit": 0}).status_code == 422


def test_recommendations_report_missing_and_zero_interest_vectors(api_client):
    student_token, student = create_account(api_client, "STUDENT")
    missing = api_client.get("/api/v1/recommendations", headers=headers(student_token))
    assert missing.status_code == 404

    with api_client.test_sessions() as db:
        db.add(StudentInterest(student_id=uuid.UUID(student["id"]), description="placeholder", skills=[], embedding=[0.0] * EMBEDDING_DIMENSION))
        db.commit()
    zero = api_client.get("/api/v1/recommendations", headers=headers(student_token))
    assert zero.status_code == 409


def test_keyword_search_uses_full_text_open_filter_pagination_and_rejects_blank(api_client):
    faculty_token, _ = create_account(api_client, "FACULTY")
    first = create_project(api_client, faculty_token, "Climate adaptation research", "Study climate adaptation planning in coastal communities", ["Climate science"])
    second = create_project(api_client, faculty_token, "Urban climate resilience", "Research climate resilience strategies in cities", ["Urban planning"])
    closed = create_project(api_client, faculty_token, "Climate archive", "Searchable climate history and adaptation records", ["Archives"])
    api_client.patch(f"/api/v1/projects/{closed['id']}", headers=headers(faculty_token), json={"status": "CLOSED"})

    page_one = api_client.get("/api/v1/projects/search", params={"q": "climate", "limit": 1, "offset": 0})
    page_two = api_client.get("/api/v1/projects/search", params={"q": "climate", "limit": 1, "offset": 1})
    assert page_one.status_code == page_two.status_code == 200
    assert page_one.json()["total"] == 2
    assert len(page_one.json()["items"]) == len(page_two.json()["items"]) == 1
    assert page_one.json()["items"][0]["id"] != page_two.json()["items"][0]["id"]
    assert closed["id"] not in {page_one.json()["items"][0]["id"], page_two.json()["items"][0]["id"]}
    assert api_client.get("/api/v1/projects/search", params={"q": "   "}).status_code == 422
    no_terms = api_client.get("/api/v1/projects/search", params={"q": "the"})
    assert no_terms.status_code == 200 and no_terms.json()["total"] == 0


def test_backfill_updates_only_zero_vectors_and_is_rerunnable(api_client):
    from app.scripts.backfill_embeddings import backfill_embeddings

    student_token, student = create_account(api_client, "STUDENT")
    faculty_token, _ = create_account(api_client, "FACULTY")
    project = create_project(api_client, faculty_token, "Wetland ecology", "Research on wetland communities")
    interest = create_interest(api_client, student_token, "Wetland ecology interests")
    assert interest.status_code == 201
    with api_client.test_sessions() as db:
        stored_project = db.get(FacultyProject, uuid.UUID(project["id"]))
        stored_interest = db.query(StudentInterest).filter_by(student_id=uuid.UUID(student["id"])).one()
        stored_project.embedding = [0.0] * EMBEDDING_DIMENSION
        stored_interest.embedding = [0.0] * EMBEDDING_DIMENSION
        db.commit()
        assert backfill_embeddings(db, batch_size=1, project_ids={uuid.UUID(project["id"])},
                                   interest_ids={stored_interest.id}) == {"faculty_projects": 1, "student_interests": 1}
        assert backfill_embeddings(db, batch_size=1, project_ids={uuid.UUID(project["id"])},
                                   interest_ids={stored_interest.id}) == {"faculty_projects": 0, "student_interests": 0}
        assert db.get(FacultyProject, uuid.UUID(project["id"])).embedding[1] == 1.0


def test_model_unavailable_returns_service_unavailable_on_profile_write(api_client, monkeypatch):
    student_token, _ = create_account(api_client, "STUDENT")

    class UnavailableProvider:
        def embed(self, text: str) -> list[float]:
            raise EmbeddingUnavailableError("private model/network error")

    monkeypatch.setattr(embeddings_module, "embedding_provider", UnavailableProvider())
    response = create_interest(api_client, student_token, "Research into sustainable energy systems")
    assert response.status_code == 503
    assert response.json()["detail"] == "Semantic embedding is temporarily unavailable"
    assert "private model/network error" not in response.text
