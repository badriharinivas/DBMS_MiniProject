import uuid

from sqlalchemy import text

from app.db.session import engine


def test_postgresql_migration_objects_and_matching_behavior():
    connection = engine.connect()
    transaction = connection.begin()
    try:
        table_names = set(
            connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            ).scalars()
        )
        assert {"departments", "users", "faculty_projects", "student_interests", "applications", "alembic_version"} <= table_names

        object_names = set(
            connection.execute(
                text("SELECT routine_name FROM information_schema.routines WHERE routine_schema='public'")
            ).scalars()
        )
        assert {"match_open_projects", "mentormatch_touch_updated_at"} <= object_names
        assert connection.execute(
            text("SELECT to_regclass('public.open_projects_with_application_stats')")
        ).scalar_one() is not None
        assert connection.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one() == "0.8.6"

        dimension = connection.execute(
            text("SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a WHERE a.attrelid='faculty_projects'::regclass AND a.attname='embedding'")
        ).scalar_one()
        assert dimension == "vector(384)"
        index_names = set(
            connection.execute(
                text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
            ).scalars()
        )
        assert {
            "ix_faculty_projects_embedding_cosine",
            "ix_student_interests_embedding_cosine",
            "ix_faculty_projects_search_vector",
            "uq_applications_student_project",
        } <= index_names

        department_id, faculty_id, student_id, project_id, zero_project_id = [uuid.uuid4() for _ in range(5)]
        connection.execute(text("INSERT INTO departments (id, name) VALUES (:id, :name)"), {"id": department_id, "name": f"Test {department_id}"})
        connection.execute(
            text("INSERT INTO users (id,name,email,password_hash,role,department_id) VALUES (:id,'Faculty','f-' || :id || '@example.test','hash','FACULTY',:department)"),
            {"id": faculty_id, "department": department_id},
        )
        connection.execute(
            text("INSERT INTO users (id,name,email,password_hash,role,department_id) VALUES (:id,'Student','s-' || :id || '@example.test','hash','STUDENT',:department)"),
            {"id": student_id, "department": department_id},
        )
        vector = "[1," + ",".join(["0"] * 383) + "]"
        connection.execute(
            text("INSERT INTO faculty_projects (id,faculty_id,title,description,embedding) VALUES (:id,:faculty,'Quantum materials','Research on quantum materials',CAST(:embedding AS vector))"),
            {"id": project_id, "faculty": faculty_id, "embedding": vector},
        )
        connection.execute(
            text("INSERT INTO faculty_projects (id,faculty_id,title,description,embedding) VALUES (:id,:faculty,'Placeholder project','Awaiting embedding backfill',CAST(:embedding AS vector))"),
            {"id": zero_project_id, "faculty": faculty_id, "embedding": '[' + ','.join(['0'] * 384) + ']'},
        )
        connection.execute(
            text("INSERT INTO student_interests (student_id,description,embedding) VALUES (:id,'Quantum materials',CAST(:embedding AS vector))"),
            {"id": student_id, "embedding": vector},
        )
        result = connection.execute(
            text("SELECT project_id, similarity FROM match_open_projects(:student, 10) WHERE project_id=:project"),
            {"student": student_id, "project": project_id},
        ).one()
        assert result.project_id == project_id
        assert result.similarity == 1.0
        assert connection.execute(text("SELECT count(*) FROM match_open_projects(:student, 10) WHERE project_id=:zero_project"), {"student": student_id, "zero_project": zero_project_id}).scalar_one() == 0
        assert connection.execute(
            text("SELECT application_count FROM open_projects_with_application_stats WHERE project_id=:project"),
            {"project": project_id},
        ).scalar_one() == 0
        search_match = connection.execute(
            text("SELECT search_vector @@ plainto_tsquery('english', 'quantum materials') FROM faculty_projects WHERE id=:project"),
            {"project": project_id},
        ).scalar_one()
        assert search_match is True

        connection.execute(text("UPDATE faculty_projects SET title='Quantum systems' WHERE id=:project"), {"project": project_id})
        updated_search_match = connection.execute(
            text("SELECT search_vector @@ plainto_tsquery('english', 'systems') FROM faculty_projects WHERE id=:project"),
            {"project": project_id},
        ).scalar_one()
        assert updated_search_match is True
        assert connection.execute(
            text("SELECT updated_at > created_at FROM faculty_projects WHERE id=:project"),
            {"project": project_id},
        ).scalar_one() is True
    finally:
        transaction.rollback()
        connection.close()
