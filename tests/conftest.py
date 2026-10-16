import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import app.services.embeddings as embeddings_module
from app.db.models import Department
from app.db.session import engine, get_db
from app.main import app


@pytest.fixture
def api_client(monkeypatch):
    """Run every API request inside a transaction that is rolled back."""
    connection = engine.connect()
    transaction = connection.begin()
    test_sessions = sessionmaker(bind=connection, autoflush=False, autocommit=False)

    def override_get_db():
        session = test_sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    class TestEmbeddingProvider:
        def embed(self, text: str) -> list[float]:
            vector = [0.0] * 384
            vector[1 if "wetland" in text.casefold() else 0] = 1.0
            return vector

    monkeypatch.setattr(embeddings_module, "embedding_provider", TestEmbeddingProvider())
    with test_sessions() as session:
        department = Department(name="API test department", description="Transaction-scoped test fixture")
        session.add(department)
        session.flush()
        department_id = department.id
    try:
        with TestClient(app) as client:
            client.department_id = str(department_id)
            client.test_sessions = test_sessions
            yield client
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()
