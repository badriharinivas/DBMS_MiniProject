import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_faculty, require_student
from app.db.models import Application, ApplicationStatus, FacultyProject, ProjectStatus, User
from app.db.session import get_db
from app.schemas import ApplicationCreate, ApplicationOut, ApplicationStatusUpdate

router = APIRouter(tags=["applications"])


@router.post("/projects/{project_id}/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def submit_application(project_id: uuid.UUID, payload: ApplicationCreate, db: Session = Depends(get_db), student: User = Depends(require_student)):
    project = db.scalar(select(FacultyProject).where(FacultyProject.id == project_id).with_for_update())
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=409, detail="Applications are closed for this project")
    if db.scalar(select(Application.id).where(Application.student_id == student.id, Application.project_id == project_id)) is not None:
        raise HTTPException(status_code=409, detail="You have already applied to this project")
    application = Application(student_id=student.id, project_id=project_id, message=payload.message)
    db.add(application)
    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An application for this project already exists") from None
    return application


@router.get("/applications/me", response_model=list[ApplicationOut])
def list_my_applications(offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100),
                         db: Session = Depends(get_db), student: User = Depends(require_student)):
    return db.scalars(select(Application).where(Application.student_id == student.id)
                      .order_by(Application.created_at.desc()).offset(offset).limit(limit)).all()


@router.get("/projects/{project_id}/applications", response_model=list[ApplicationOut])
def list_project_applications(project_id: uuid.UUID, offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100),
                              db: Session = Depends(get_db), faculty: User = Depends(require_faculty)):
    project = db.get(FacultyProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="You can only review applications to your own projects")
    return db.scalars(select(Application).where(Application.project_id == project_id)
                      .order_by(Application.created_at.desc()).offset(offset).limit(limit)).all()


@router.patch("/applications/{application_id}/status", response_model=ApplicationOut)
def update_application_status(application_id: uuid.UUID, payload: ApplicationStatusUpdate,
                              db: Session = Depends(get_db), faculty: User = Depends(require_faculty)):
    application = db.scalar(select(Application).where(Application.id == application_id).with_for_update())
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.project.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="You can only review applications to your own projects")
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Only pending applications can change status")
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return application
