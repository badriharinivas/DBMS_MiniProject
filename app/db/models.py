"""Relational models for MentorMatch's database layer."""

import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"


class ProjectStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    users: Mapped[list["User"]] = relationship(back_populates="department")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('STUDENT', 'FACULTY')", name="ck_users_role"),
        Index("ix_users_department_id", "department_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", native_enum=False, create_constraint=False), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    department: Mapped[Department] = relationship(back_populates="users")
    projects: Mapped[list["FacultyProject"]] = relationship(back_populates="faculty")
    interest: Mapped["StudentInterest | None"] = relationship(back_populates="student", uselist=False, cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")


class FacultyProject(Base):
    __tablename__ = "faculty_projects"
    __table_args__ = (
        CheckConstraint("status IN ('OPEN', 'CLOSED')", name="ck_faculty_projects_status"),
        Index("ix_faculty_projects_faculty_id", "faculty_id"),
        Index("ix_faculty_projects_status", "status"),
        Index("ix_faculty_projects_embedding_cosine", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}, postgresql_with={"lists": 100}),
        Index("ix_faculty_projects_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    faculty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'::varchar[]"))
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus, name="project_status", native_enum=False, create_constraint=False), nullable=False, server_default="OPEN")
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    search_vector: Mapped[str] = mapped_column(TSVECTOR, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    faculty: Mapped[User] = relationship(back_populates="projects")
    applications: Mapped[list["Application"]] = relationship(back_populates="project")


class StudentInterest(Base):
    __tablename__ = "student_interests"
    __table_args__ = (
        UniqueConstraint("student_id", name="uq_student_interests_student_id"),
        Index("ix_student_interests_embedding_cosine", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}, postgresql_with={"lists": 100}),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'::varchar[]"))
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    student: Mapped[User] = relationship(back_populates="interest")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("student_id", "project_id", name="uq_applications_student_project"),
        CheckConstraint("status IN ('PENDING', 'ACCEPTED', 'REJECTED')", name="ck_applications_status"),
        Index("ix_applications_student_id", "student_id"),
        Index("ix_applications_project_status", "project_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty_projects.id", ondelete="RESTRICT"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus, name="application_status", native_enum=False, create_constraint=False), nullable=False, server_default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    student: Mapped[User] = relationship(back_populates="applications")
    project: Mapped[FacultyProject] = relationship(back_populates="applications")
