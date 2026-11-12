"""Backfill all-zero placeholder vectors without touching valid embeddings.

Run with: python -m app.scripts.backfill_embeddings --batch-size 100
"""

import argparse
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import FacultyProject, StudentInterest
from app.db.session import SessionLocal
from app.services.embeddings import generate_embedding, interest_text, project_text


def backfill_embeddings(
    db: Session,
    batch_size: int = 100,
    project_ids: set[uuid.UUID] | None = None,
    interest_ids: set[uuid.UUID] | None = None,
) -> dict[str, int]:
    if not 1 <= batch_size <= 1000:
        raise ValueError("batch_size must be between 1 and 1000")

    totals = {"faculty_projects": 0, "student_interests": 0}
    for model, table_name, text_builder, target_ids in (
        (FacultyProject, "faculty_projects", lambda row: project_text(row.title, row.description, row.required_skills), project_ids),
        (StudentInterest, "student_interests", lambda row: interest_text(row.description, row.skills), interest_ids),
    ):
        filters = [func.vector_norm(model.embedding) == 0]
        if target_ids is not None:
            filters.append(model.id.in_(target_ids))
        pending = db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
        if pending:
            # Load/check the model before taking row locks, so a first-run download
            # failure cannot hold project or interest rows locked.
            generate_embedding("MentorMatch embedding backfill initialization")
        while True:
            rows = db.scalars(
                select(model)
                .where(*filters)
                .order_by(model.id)
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            ).all()
            if not rows:
                break
            try:
                for row in rows:
                    row.embedding = generate_embedding(text_builder(row))
                db.commit()
            except Exception:
                db.rollback()
                raise
            totals[table_name] += len(rows)
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace zero-vector placeholders with MiniLM embeddings")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    with SessionLocal() as db:
        totals = backfill_embeddings(db, batch_size=args.batch_size)
    print(f"Backfilled {totals['faculty_projects']} projects and {totals['student_interests']} interest profiles.")


if __name__ == "__main__":
    main()
