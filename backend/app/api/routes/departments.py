import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Department
from app.db.session import get_db
from app.schemas import DepartmentOut

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(offset: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200), db: Session = Depends(get_db)):
    return db.scalars(select(Department).order_by(Department.name).offset(offset).limit(limit)).all()


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return department
