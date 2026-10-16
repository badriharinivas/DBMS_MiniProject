"""Validated API input and output models."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator

from app.db.models import ApplicationStatus, ProjectStatus, UserRole

NameText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
ProjectTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=240)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=10000)]
SkillText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None


class UserRegister(BaseModel):
    name: NameText
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole
    department_id: uuid.UUID

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def reject_weak_passwords(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    department_id: uuid.UUID
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ProjectCreate(BaseModel):
    title: ProjectTitle
    description: LongText
    required_skills: list[SkillText] = Field(default_factory=list, max_length=30)

    @field_validator("required_skills")
    @classmethod
    def unique_skills(cls, value: list[str]) -> list[str]:
        unique = list(dict.fromkeys(skill.casefold() for skill in value))
        lookup = {skill.casefold(): skill for skill in value}
        return [lookup[skill] for skill in unique]


class ProjectUpdate(BaseModel):
    title: ProjectTitle | None = None
    description: LongText | None = None
    required_skills: list[SkillText] | None = Field(default=None, max_length=30)
    status: ProjectStatus | None = None

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one project field must be supplied")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Project fields cannot be null")
        return self


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    faculty_id: uuid.UUID
    title: str
    description: str
    required_skills: list[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class InterestWrite(BaseModel):
    description: LongText
    skills: list[SkillText] = Field(default_factory=list, max_length=50)

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        result = []
        for skill in value:
            if skill.casefold() not in seen:
                seen.add(skill.casefold())
                result.append(skill)
        return result


class InterestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    description: str
    skills: list[str]
    updated_at: datetime


class ApplicationCreate(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=20, max_length=4000)]


class ApplicationStatusUpdate(BaseModel):
    status: Literal[ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED]


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    project_id: uuid.UUID
    message: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class PaginatedProjects(BaseModel):
    items: list[ProjectOut]
    total: int
    limit: int
    offset: int


class ProjectSearchPage(PaginatedProjects):
    query: str


class RecommendationOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    required_skills: list[str]
    status: ProjectStatus
    faculty_id: uuid.UUID
    faculty_name: str
    department_id: uuid.UUID
    department_name: str
    similarity: float = Field(ge=-1.0, le=1.0)


class RecommendationPage(BaseModel):
    items: list[RecommendationOut]
    limit: int
