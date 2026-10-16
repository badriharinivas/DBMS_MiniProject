from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_student
from app.db.models import StudentInterest, User
from app.db.session import get_db
from app.schemas import InterestOut, InterestWrite
from app.services.embeddings import EmbeddingUnavailableError, generate_embedding, interest_text

router = APIRouter(prefix="/students/me/interests", tags=["student interests"])


@router.get("", response_model=InterestOut)
def get_interest(db: Session = Depends(get_db), student: User = Depends(require_student)):
    interest = db.scalar(select(StudentInterest).where(StudentInterest.student_id == student.id))
    if interest is None:
        raise HTTPException(status_code=404, detail="Interest profile not found")
    return interest


@router.post("", response_model=InterestOut, status_code=status.HTTP_201_CREATED)
def create_interest(payload: InterestWrite, db: Session = Depends(get_db), student: User = Depends(require_student)):
    if db.scalar(select(StudentInterest.id).where(StudentInterest.student_id == student.id)) is not None:
        raise HTTPException(status_code=409, detail="Interest profile already exists; use PUT to update it")
    try:
        embedding = generate_embedding(interest_text(payload.description, payload.skills))
    except EmbeddingUnavailableError:
        raise HTTPException(status_code=503, detail="Semantic embedding is temporarily unavailable") from None
    profile = StudentInterest(student_id=student.id, description=payload.description, skills=payload.skills, embedding=embedding)
    db.add(profile)
    try:
        db.commit()
        db.refresh(profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Interest profile already exists") from None
    return profile


@router.put("", response_model=InterestOut)
def update_interest(payload: InterestWrite, db: Session = Depends(get_db), student: User = Depends(require_student)):
    try:
        embedding = generate_embedding(interest_text(payload.description, payload.skills))
    except EmbeddingUnavailableError:
        raise HTTPException(status_code=503, detail="Semantic embedding is temporarily unavailable") from None
    profile = db.scalar(select(StudentInterest).where(StudentInterest.student_id == student.id))
    if profile is None:
        profile = StudentInterest(student_id=student.id, description=payload.description, skills=payload.skills, embedding=embedding)
        db.add(profile)
    else:
        profile.description = payload.description
        profile.skills = payload.skills
        profile.embedding = embedding
    try:
        db.commit()
        db.refresh(profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Interest profile could not be saved because a profile already exists") from None
    return profile
