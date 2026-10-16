import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_faculty
from app.db.models import FacultyProject, ProjectStatus, User
from app.db.session import get_db
from app.schemas import PaginatedProjects, ProjectCreate, ProjectOut, ProjectSearchPage, ProjectUpdate
from app.services.embeddings import EmbeddingUnavailableError, generate_embedding, project_text

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/search", response_model=ProjectSearchPage)
def search_projects(q: str = Query(min_length=1, max_length=200), offset: int = Query(default=0, ge=0),
                    limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    normalized_query = " ".join(q.split())
    if not normalized_query:
        raise HTTPException(status_code=422, detail="Search query cannot be empty")
    tsquery = func.plainto_tsquery("english", normalized_query)
    predicate = FacultyProject.status == ProjectStatus.OPEN
    match = FacultyProject.search_vector.op("@@")(tsquery)
    statement = select(FacultyProject).where(predicate, match)
    count_statement = select(func.count(FacultyProject.id)).where(predicate, match)
    rank = func.ts_rank_cd(FacultyProject.search_vector, tsquery)
    items = db.scalars(statement.order_by(rank.desc(), FacultyProject.created_at.desc(), FacultyProject.id.asc()).offset(offset).limit(limit)).all()
    return ProjectSearchPage(items=items, total=db.scalar(count_statement) or 0, limit=limit, offset=offset, query=normalized_query)


@router.get("", response_model=PaginatedProjects)
def list_projects(status_filter: ProjectStatus | None = Query(default=None, alias="status"), department_id: uuid.UUID | None = None,
                  offset: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    statement = select(FacultyProject)
    count_statement = select(func.count(FacultyProject.id))
    if status_filter is not None:
        statement = statement.where(FacultyProject.status == status_filter)
        count_statement = count_statement.where(FacultyProject.status == status_filter)
    if department_id is not None:
        statement = statement.join(FacultyProject.faculty).where(User.department_id == department_id)
        count_statement = count_statement.join(User, FacultyProject.faculty_id == User.id).where(User.department_id == department_id)
    items = db.scalars(statement.order_by(FacultyProject.created_at.desc()).offset(offset).limit(limit)).all()
    return PaginatedProjects(items=items, total=db.scalar(count_statement) or 0, limit=limit, offset=offset)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), faculty: User = Depends(require_faculty)):
    try:
        embedding = generate_embedding(project_text(payload.title, payload.description, payload.required_skills))
    except EmbeddingUnavailableError:
        raise HTTPException(status_code=503, detail="Semantic embedding is temporarily unavailable") from None
    project = FacultyProject(
        faculty_id=faculty.id, title=payload.title, description=payload.description,
        required_skills=payload.required_skills, status=ProjectStatus.OPEN,
        embedding=embedding,
        search_vector="",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = db.get(FacultyProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: uuid.UUID, payload: ProjectUpdate, db: Session = Depends(get_db), faculty: User = Depends(require_faculty)):
    project = db.scalar(select(FacultyProject).where(FacultyProject.id == project_id).with_for_update())
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="You can only manage your own projects")
    changes = payload.model_dump(exclude_unset=True)
    if {"title", "description", "required_skills"} & changes.keys():
        title = changes.get("title", project.title)
        description = changes.get("description", project.description)
        skills = changes.get("required_skills", project.required_skills)
        try:
            changes["embedding"] = generate_embedding(project_text(title, description, skills))
        except EmbeddingUnavailableError:
            raise HTTPException(status_code=503, detail="Semantic embedding is temporarily unavailable") from None
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project
