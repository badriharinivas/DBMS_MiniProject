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

    distance = FacultyProject.embedding.cosine_distance(interest.embedding)
    statement = (
        select(FacultyProject, User, Department, distance.label("cosine_distance"))
        .join(User, FacultyProject.faculty_id == User.id)
        .join(Department, User.department_id == Department.id)
        .where(
            FacultyProject.status == ProjectStatus.OPEN,
            FacultyProject.faculty_id != student.id,
            func.vector_norm(FacultyProject.embedding) > 0,
        )
        .order_by(distance.asc(), FacultyProject.created_at.desc())
        .limit(limit)
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
            similarity=max(-1.0, min(1.0, 1.0 - float(cosine_distance))),
        )
        for project, faculty, department, cosine_distance in results
    ]
    return RecommendationPage(items=items, limit=limit)
