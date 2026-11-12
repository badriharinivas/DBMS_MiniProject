"""Safely populate the configured development database with repeatable demo data."""

from __future__ import annotations

import argparse
import getpass
import math
import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import (
    Application,
    ApplicationStatus,
    Department,
    FacultyProject,
    ProjectStatus,
    StudentInterest,
    User,
    UserRole,
)
from app.db.session import SessionLocal, engine, settings
from app.services.embeddings import (
    EMBEDDING_DIMENSION,
    generate_embedding,
    interest_text,
    project_text,
)


FACULTY = [
    {"name": "Dr. Mira Sen", "email": "demo.mira.sen@example.edu", "department": "Computer Science"},
    {"name": "Dr. Kiran Patel", "email": "demo.kiran.patel@example.edu", "department": "Electrical Engineering"},
]
STUDENTS = [
    {"name": "Aarav Mehta", "email": "demo.aarav.mehta@example.edu", "department": "Computer Science"},
    {"name": "Nisha Iyer", "email": "demo.nisha.iyer@example.edu", "department": "Environmental Science"},
    {"name": "Devika Rao", "email": "demo.devika.rao@example.edu", "department": "Electrical Engineering"},
]
PROJECTS = [
    {
        "key": "solar-forecasting", "title": "Solar Energy Forecasting with Weather Data",
        "faculty": FACULTY[0]["email"], "department": "Electrical Engineering",
        "description": "Build machine learning models that combine satellite cloud imagery, historical weather, and inverter telemetry to forecast campus solar generation at hourly and day-ahead horizons. Evaluate calibration and performance during rapidly changing cloud conditions.",
        "skills": ["Python", "time series", "machine learning", "solar energy", "data visualization"],
    },
    {
        "key": "smart-traffic", "title": "Smart Traffic Signal Coordination",
        "faculty": FACULTY[1]["email"], "department": "Computer Science",
        "description": "Study adaptive traffic signal timing using road sensors and simulated vehicle flows. The team will compare reinforcement learning and conventional control strategies for reducing congestion, travel time, and emissions while protecting pedestrian crossing time.",
        "skills": ["Python", "optimization", "simulation", "reinforcement learning", "交通 systems"],
    },
    {
        "key": "medical-imaging", "title": "Explainable Medical Image Classification",
        "faculty": FACULTY[0]["email"], "department": "Computer Science",
        "description": "Develop and assess interpretable image classification methods for de-identified medical scans. Work includes careful dataset splitting, model calibration, error analysis, and visual explanations that help researchers understand failure modes.",
        "skills": ["Python", "deep learning", "computer vision", "image classification", "model evaluation"],
    },
    {
        "key": "water-quality", "title": "Water Quality Prediction from River Sensors",
        "faculty": FACULTY[1]["email"], "department": "Environmental Science",
        "description": "Use longitudinal river sensor measurements and rainfall records to predict water quality indicators and identify unusual pollution events. The project emphasizes robust time-series analysis, environmental interpretation, and clear uncertainty reporting.",
        "skills": ["water quality", "environmental data", "Python", "statistics", "time series"],
    },
    {
        "key": "crop-disease", "title": "Crop Disease Detection in Field Images",
        "faculty": FACULTY[0]["email"], "department": "Electrical Engineering",
        "description": "Investigate computer vision methods for identifying crop diseases from field photographs captured under varied lighting and backgrounds. Compare transfer learning approaches and assess how image quality and class imbalance affect reliable detection.",
        "skills": ["computer vision", "agriculture", "Python", "deep learning", "image analysis"],
    },
]
INTERESTS = [
    {
        "key": "aarav-ml-imaging", "student": STUDENTS[0]["email"],
        "description": "I want to apply machine learning and computer vision to images, especially explainable medical image classification and robust visual recognition. I also enjoy analyzing model errors and building clear evaluation tools.",
        "skills": ["Python", "machine learning", "computer vision", "image analysis", "data visualization"],
    },
    {
        "key": "nisha-rivers", "student": STUDENTS[1]["email"],
        "description": "My main interest is environmental science, river ecology, and protecting water resources. I would like to analyze water quality measurements, rainfall, and pollution patterns using statistics and time-series prediction.",
        "skills": ["environmental science", "water quality", "statistics", "Python", "field research"],
    },
    {
        "key": "devika-energy", "student": STUDENTS[2]["email"],
        "description": "I am interested in renewable energy systems, solar power forecasting, and smart infrastructure. I would like to combine weather data with engineering measurements and explore optimization for sustainable cities.",
        "skills": ["solar energy", "electrical engineering", "time series", "optimization", "Python"],
    },
]
APPLICATIONS = [
    {"student": STUDENTS[0]["email"], "project": "medical-imaging", "decision": ApplicationStatus.ACCEPTED, "message": "My coursework in computer vision and experience building image classifiers would help me contribute to model evaluation and explainability."},
    {"student": STUDENTS[0]["email"], "project": "smart-traffic", "decision": None, "message": "I have experience with Python and optimization, and I would like to learn how adaptive control can make urban transportation safer and more efficient."},
    {"student": STUDENTS[1]["email"], "project": "water-quality", "decision": ApplicationStatus.ACCEPTED, "message": "My environmental science background and statistics experience align with analyzing river measurements and communicating uncertainty in pollution predictions."},
    {"student": STUDENTS[1]["email"], "project": "crop-disease", "decision": ApplicationStatus.REJECTED, "message": "I am interested in applying data analysis to field observations and would value the chance to contribute to this agricultural imaging study."},
    {"student": STUDENTS[2]["email"], "project": "solar-forecasting", "decision": None, "message": "My electrical engineering studies and interest in renewable systems would prepare me to help analyze weather and solar generation data."},
    {"student": STUDENTS[2]["email"], "project": "water-quality", "decision": None, "message": "I can contribute Python and time-series skills, and I am interested in understanding how sensor data supports reliable environmental monitoring."},
    {"student": STUDENTS[0]["email"], "project": "crop-disease", "decision": ApplicationStatus.PENDING, "message": "I have worked with image analysis in class projects and would like to study how computer vision can support practical crop health monitoring."},
]


def _password(reset: bool) -> str | None:
    value = os.environ.get("MENTORMATCH_DEMO_PASSWORD")
    if value:
        if len(value) < 12:
            raise SystemExit("MENTORMATCH_DEMO_PASSWORD must contain at least 12 characters.")
        return value
    if not reset:
        return None
    first = getpass.getpass("Choose a password for all demo accounts (12+ characters): ")
    second = getpass.getpass("Confirm demo-account password: ")
    if len(first) < 12 or first != second:
        raise SystemExit("Passwords must match and contain at least 12 characters.")
    return first


def _vector_is_valid(vector) -> bool:
    return (
        vector is not None
        and len(vector) == EMBEDDING_DIMENSION
        and all(math.isfinite(float(value)) for value in vector)
        and math.sqrt(sum(float(value) ** 2 for value in vector)) > 1e-12
    )


def seed(*, reset_passwords: bool = False) -> dict[str, int]:
    url = engine.url
    if settings.app_env.casefold() not in {"development", "dev", "local"}:
        raise SystemExit("Refusing to seed because APP_ENV is not a development environment.")
    if url.host not in {"localhost", "127.0.0.1", "::1"} or url.port != 5433:
        raise SystemExit("Refusing to seed: configured database is not localhost on port 5433.")
    password = _password(reset_passwords)
    counts = {"users_created": 0, "projects_created": 0, "interests_created": 0, "applications_created": 0}

    with SessionLocal.begin() as db:
        departments = {d.name: d for d in db.scalars(select(Department))}
        needed = {item["department"] for item in FACULTY + STUDENTS} | {p["department"] for p in PROJECTS}
        missing = needed - departments.keys()
        if missing:
            raise SystemExit(f"Required existing departments are missing: {', '.join(sorted(missing))}")

        accounts: dict[str, User] = {}
        for spec, role in [(x, UserRole.FACULTY) for x in FACULTY] + [(x, UserRole.STUDENT) for x in STUDENTS]:
            user = db.scalar(select(User).where(User.email == spec["email"]))
            if user:
                if user.role != role or user.name != spec["name"]:
                    raise SystemExit(f"Demo account identity conflict for {spec['email']}.")
                if reset_passwords:
                    user.password_hash = hash_password(password)
            else:
                if password is None:
                    raise SystemExit("A demo account is missing. Set MENTORMATCH_DEMO_PASSWORD or use --reset-demo-passwords to choose one securely.")
                user = User(name=spec["name"], email=spec["email"], password_hash=hash_password(password), role=role, department_id=departments[spec["department"]].id)
                db.add(user)
                db.flush()
                counts["users_created"] += 1
            accounts[spec["email"]] = user

        project_rows: dict[str, FacultyProject] = {}
        for spec in PROJECTS:
            marker = f"[MentorMatch demo seed v1:{spec['key']}]"
            matches = list(db.scalars(select(FacultyProject).where(FacultyProject.description.contains(marker))))
            if len(matches) > 1:
                raise SystemExit(f"Multiple projects found for seed key {spec['key']}.")
            project = matches[0] if matches else None
            if project:
                if project.faculty_id != accounts[spec["faculty"]].id or project.title != spec["title"]:
                    raise SystemExit(f"Seed project identity conflict for {spec['key']}.")
            else:
                collision = db.scalar(select(FacultyProject.id).where(FacultyProject.title == spec["title"]))
                if collision:
                    raise SystemExit(f"Project title already exists outside the seed: {spec['title']}.")
                description = f"{spec['description']} {marker}"
                embedding = generate_embedding(project_text(spec["title"], description, spec["skills"]))
                project = FacultyProject(faculty_id=accounts[spec["faculty"]].id, title=spec["title"], description=description,
                                         required_skills=spec["skills"], status=ProjectStatus.OPEN, embedding=embedding, search_vector="")
                db.add(project)
                db.flush()
                counts["projects_created"] += 1
            project_rows[spec["key"]] = project

        for spec in INTERESTS:
            marker = f"[MentorMatch demo seed v1:{spec['key']}]"
            student = accounts[spec["student"]]
            interest = db.scalar(select(StudentInterest).where(StudentInterest.student_id == student.id))
            if interest:
                if marker not in interest.description:
                    raise SystemExit(f"Student {spec['student']} already has a non-seed interest profile; refusing to overwrite it.")
            else:
                description = f"{spec['description']} {marker}"
                embedding = generate_embedding(interest_text(description, spec["skills"]))
                interest = StudentInterest(student_id=student.id, description=description, skills=spec["skills"], embedding=embedding)
                db.add(interest)
                counts["interests_created"] += 1

        for spec in APPLICATIONS:
            student = accounts[spec["student"]]
            project = project_rows[spec["project"]]
            marker = f"[MentorMatch demo application:{spec['student']}:{spec['project']}]"
            application = db.scalar(select(Application).where(Application.student_id == student.id, Application.project_id == project.id))
            if application:
                if marker not in application.message:
                    raise SystemExit("An application pair already exists outside the seed; refusing to alter it.")
                continue
            if project.status != ProjectStatus.OPEN or student.role != UserRole.STUDENT or project.faculty.role != UserRole.FACULTY:
                raise SystemExit("Application failed the API's role or open-project checks.")
            application = Application(student_id=student.id, project_id=project.id,
                                      message=f"{spec['message']} {marker}", status=ApplicationStatus.PENDING)
            db.add(application)
            db.flush()
            counts["applications_created"] += 1
            if spec["decision"] is not None:
                if application.status != ApplicationStatus.PENDING or project.faculty_id != accounts[project.faculty.email].id:
                    raise SystemExit("Application decision failed the API's pending-status or faculty-ownership checks.")
                application.status = spec["decision"]

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-demo-passwords", action="store_true", help="Interactively set a new shared password for the five seeded demo accounts.")
    args = parser.parse_args()
    result = seed(reset_passwords=args.reset_demo_passwords)
    print("Seed completed:", result)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not emit database URLs or model/provider exception details that can contain local configuration.
        from app.services.embeddings import EmbeddingUnavailableError

        if isinstance(exc, EmbeddingUnavailableError):
            print(f"Seeding stopped: {exc}", file=sys.stderr)
            raise SystemExit(1) from None
        raise
