"""Initial MentorMatch schema and PostgreSQL matching objects."""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "departments",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_departments_name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=7), nullable=False),
        sa.Column("department_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('STUDENT', 'FACULTY')", name="ck_users_role"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_table(
        "faculty_projects",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("faculty_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.ARRAY(sa.String()), server_default=sa.text("'{}'::varchar[]"), nullable=False),
        sa.Column("status", sa.String(length=6), server_default=sa.text("'OPEN'"), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED')", name="ck_faculty_projects_status"),
        sa.ForeignKeyConstraint(["faculty_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_faculty_projects_faculty_id", "faculty_projects", ["faculty_id"])
    op.create_index("ix_faculty_projects_status", "faculty_projects", ["status"])
    op.create_index("ix_faculty_projects_search_vector", "faculty_projects", ["search_vector"], postgresql_using="gin")
    op.create_index("ix_faculty_projects_embedding_cosine", "faculty_projects", ["embedding"], postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}, postgresql_with={"lists": 100})
    op.create_table(
        "student_interests",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("skills", sa.ARRAY(sa.String()), server_default=sa.text("'{}'::varchar[]"), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", name="uq_student_interests_student_id"),
    )
    op.create_index("ix_student_interests_embedding_cosine", "student_interests", ["embedding"], postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}, postgresql_with={"lists": 100})
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=8), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'ACCEPTED', 'REJECTED')", name="ck_applications_status"),
        sa.ForeignKeyConstraint(["project_id"], ["faculty_projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "project_id", name="uq_applications_student_project"),
    )
    op.create_index("ix_applications_student_id", "applications", ["student_id"])
    op.create_index("ix_applications_project_status", "applications", ["project_id", "status"])

    op.execute("""
        CREATE FUNCTION mentormatch_touch_updated_at() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at := clock_timestamp();
            IF TG_TABLE_NAME = 'faculty_projects' THEN
                NEW.search_vector := to_tsvector(
                    'english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.description, '') || ' ' || coalesce(array_to_string(NEW.required_skills, ' '), '')
                );
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("CREATE TRIGGER trg_faculty_projects_maintain BEFORE INSERT OR UPDATE ON faculty_projects FOR EACH ROW EXECUTE FUNCTION mentormatch_touch_updated_at()")
    for table in ("student_interests", "applications"):
        op.execute(f"CREATE TRIGGER trg_{table}_touch_updated_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION mentormatch_touch_updated_at()")

    op.execute("""
        CREATE FUNCTION match_open_projects(p_student_id uuid, p_limit integer DEFAULT 20)
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
    op.execute("""
        CREATE VIEW open_projects_with_application_stats AS
        SELECT p.id AS project_id, p.faculty_id, p.title, p.description, p.required_skills,
               p.created_at, p.updated_at, count(a.id)::bigint AS application_count,
               count(a.id) FILTER (WHERE a.status = 'PENDING')::bigint AS pending_application_count
        FROM faculty_projects AS p
        LEFT JOIN applications AS a ON a.project_id = p.id
        WHERE p.status = 'OPEN'
        GROUP BY p.id
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS open_projects_with_application_stats")
    op.execute("DROP FUNCTION IF EXISTS match_open_projects(uuid, integer)")
    for table, trigger in (("applications", "trg_applications_touch_updated_at"), ("student_interests", "trg_student_interests_touch_updated_at"), ("faculty_projects", "trg_faculty_projects_maintain")):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON {table}")
    op.execute("DROP FUNCTION IF EXISTS mentormatch_touch_updated_at()")
    op.drop_index("ix_applications_project_status", table_name="applications")
    op.drop_index("ix_applications_student_id", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_student_interests_embedding_cosine", table_name="student_interests")
    op.drop_table("student_interests")
    op.drop_index("ix_faculty_projects_embedding_cosine", table_name="faculty_projects")
    op.drop_index("ix_faculty_projects_search_vector", table_name="faculty_projects")
    op.drop_index("ix_faculty_projects_status", table_name="faculty_projects")
    op.drop_index("ix_faculty_projects_faculty_id", table_name="faculty_projects")
    op.drop_table("faculty_projects")
    op.drop_index("ix_users_department_id", table_name="users")
    op.drop_table("users")
    op.drop_table("departments")
