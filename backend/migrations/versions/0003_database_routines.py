"""Add a guarded application-status procedure and stable match ordering."""

from alembic import op

revision = "0003_database_routines"
down_revision = "0002_nonzero_match"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep recommendation ordering equivalent to the API's previous ordering,
    # with a UUID tie-breaker so equal distances return deterministically.
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
            ORDER BY p.embedding <=> si.embedding, p.created_at DESC, p.id ASC
            LIMIT greatest(1, least(coalesce(p_limit, 20), 100))
        $$
    """)

    op.execute("""
        CREATE PROCEDURE mentormatch_set_application_status(
            p_application_id uuid,
            p_faculty_id uuid,
            p_new_status text
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF p_new_status IS NULL OR p_new_status NOT IN ('ACCEPTED', 'REJECTED') THEN
                RAISE EXCEPTION 'Application status must be ACCEPTED or REJECTED'
                    USING ERRCODE = '22023';
            END IF;

            UPDATE applications AS a
            SET status = p_new_status
            FROM faculty_projects AS p
            WHERE a.id = p_application_id
              AND p.id = a.project_id
              AND p.faculty_id = p_faculty_id
              AND a.status = 'PENDING';

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Application is missing, not owned by this faculty member, or is no longer pending'
                    USING ERRCODE = 'P0001';
            END IF;
        END;
        $$
    """)


def downgrade() -> None:
    op.execute("DROP PROCEDURE IF EXISTS mentormatch_set_application_status(uuid, uuid, text)")
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
