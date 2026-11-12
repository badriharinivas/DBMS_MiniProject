from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_student
from app.db.models import Department, FacultyProject, ProjectStatus, StudentInterest, User
from app.db.session import get_db
from app.schemas import RecommendationOut, RecommendationPage

router = APIRouter(tags=["semantic recommendations"])


@router.get("/recommendations", response_model=RecommendationPage)
def recommend_projects(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), student: User = Depends(require_student)):
    interest = db.scalar(select(StudentInterest).where(StudentInterest.student_id == student.id))
    if interest is None:
        raise HTTPException(status_code=404, detail="Create an interest profile to receive recommendations")
    if not any(float(value) != 0.0 for value in interest.embedding):
        raise HTTPException(status_code=409, detail="Interest embedding is not initialized; update your interest profile")

    # Use the migrated PostgreSQL function for vector filtering, ranking, and
    # bounded results. Joining its output restores the faculty/department data
    # required by the existing API response.
    matches = func.match_open_projects(student.id, limit).table_valued(
        "project_id", "title", "description", "required_skills", "similarity",
        name="matches",
    )
    statement = (
        select(FacultyProject, User, Department, matches.c.similarity)
        .join(matches, matches.c.project_id == FacultyProject.id)
        .join(User, FacultyProject.faculty_id == User.id)
        .join(Department, User.department_id == Department.id)
        .where(FacultyProject.faculty_id != student.id)
        .order_by(matches.c.similarity.desc(), FacultyProject.created_at.desc(), FacultyProject.id.asc())
    )
    results = db.execute(statement).all()
    items = [
        RecommendationOut(
            id=project.id,
            title=project.title,
            description=project.description,
            required_skills=project.required_skills,
            status=project.status,
            faculty_id=faculty.id,
            faculty_name=faculty.name,
            department_id=department.id,
            department_name=department.name,
            similarity=max(-1.0, min(1.0, float(similarity))),
        )
        for project, faculty, department, similarity in results
    ]
    return RecommendationPage(items=items, limit=limit)
