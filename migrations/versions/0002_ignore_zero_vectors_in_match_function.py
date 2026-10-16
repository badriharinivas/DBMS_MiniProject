"""Ignore placeholder vectors in the SQL matching function.

Revision ID: 0002_nonzero_match
Revises: 0001_initial
"""

from alembic import op

revision = "0002_nonzero_match"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION match_open_projects(p_student_id uuid, p_limit integer DEFAULT 20)
        RETURNS TABLE(project_id uuid, title varchar, description text, required_skills varchar[], similarity double precision)
        LANGUAGE sql STABLE AS $$
            SELECT p.id, p.title, p.description, p.required_skills,
                   (1 - (p.embedding <=> si.embedding))::double precision
            FROM student_interests AS si
            JOIN faculty_projects AS p ON p.status = 'OPEN'
            WHERE si.student_id = p_student_id
              AND vector_norm(si.embedding) > 0
              AND vector_norm(p.embedding) > 0
            ORDER BY p.embedding <=> si.embedding
            LIMIT greatest(1, least(coalesce(p_limit, 20), 100))
        $$
    """)


def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION match_open_projects(p_student_id uuid, p_limit integer DEFAULT 20)
        RETURNS TABLE(project_id uuid, title varchar, description text, required_skills varchar[], similarity double precision)
        LANGUAGE sql STABLE AS $$
            SELECT p.id, p.title, p.description, p.required_skills,
                   (1 - (p.embedding <=> si.embedding))::double precision
            FROM student_interests AS si
            JOIN faculty_projects AS p ON p.status = 'OPEN'
            WHERE si.student_id = p_student_id
            ORDER BY p.embedding <=> si.embedding
            LIMIT greatest(1, least(coalesce(p_limit, 20), 100))
        $$
    """)
