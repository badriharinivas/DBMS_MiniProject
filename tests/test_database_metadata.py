from sqlalchemy import CheckConstraint, UniqueConstraint

from app.db.models import Application, Department, FacultyProject, StudentInterest, User
from app.db.session import Base


def test_all_database_models_are_registered():
    assert set(Base.metadata.tables) == {
        "departments",
        "users",
        "faculty_projects",
        "student_interests",
        "applications",
    }


def test_vector_dimensions_and_search_column():
    assert FacultyProject.__table__.c.embedding.type.dim == 384
    assert StudentInterest.__table__.c.embedding.type.dim == 384
    assert FacultyProject.__table__.c.search_vector.type.__class__.__name__ == "TSVECTOR"


def test_required_relational_constraints_exist():
    assert any(isinstance(c, UniqueConstraint) and c.name == "uq_student_interests_student_id" for c in StudentInterest.__table__.constraints)
    assert any(isinstance(c, UniqueConstraint) and c.name == "uq_applications_student_project" for c in Application.__table__.constraints)
    assert any(isinstance(c, CheckConstraint) and c.name == "ck_users_role" for c in User.__table__.constraints)
    assert any(isinstance(c, UniqueConstraint) and "name" in {col.name for col in c.columns} for c in Department.__table__.constraints)
