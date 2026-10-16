# MentorMatch DBMS demonstration

Run these demonstrations against the migrated development database from `backend` using `psql` (or an equivalent SQL client). The examples inspect existing rows and use rollback for writes. Do not run the constraint-failure examples on a shared transaction without a savepoint.

## 1. Tables, keys, and constraints

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

SELECT tc.table_name, tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints AS tc
WHERE tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

SELECT conrelid::regclass AS table_name, conname, pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY table_name::text, conname;
```

The foreign keys connect users to departments, projects to faculty users, interests to students, and applications to students/projects. `uq_applications_student_project` rejects duplicate applications; role and status check constraints restrict stored values. To safely observe a foreign-key rejection, use a transaction and roll it back:

```sql
BEGIN;
SAVEPOINT before_invalid_fk;
INSERT INTO users (name, email, password_hash, role, department_id)
VALUES ('FK demo', 'fk-demo@example.invalid', 'not-a-real-login-hash', 'STUDENT', gen_random_uuid());
-- The insert should fail with a foreign-key violation. In a client that keeps the session:
ROLLBACK TO SAVEPOINT before_invalid_fk;
ROLLBACK;
```

Use a unique-constraint demonstration only with a known department ID, and always roll back:

```sql
BEGIN;
SAVEPOINT before_duplicate_department;
INSERT INTO departments (name) VALUES ('DBMS demo temporary department');
INSERT INTO departments (name) VALUES ('DBMS demo temporary department');
-- Expected unique violation; then:
ROLLBACK TO SAVEPOINT before_duplicate_department;
ROLLBACK;
```

## 2. Indexes

```sql
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

SELECT indexrelid::regclass AS index_name, indrelid::regclass AS table_name,
       am.amname AS access_method, pg_get_indexdef(indexrelid) AS definition
FROM pg_index
JOIN pg_class idx ON idx.oid = indexrelid
JOIN pg_am am ON am.oid = idx.relam
WHERE indrelid IN ('faculty_projects'::regclass, 'student_interests'::regclass)
ORDER BY table_name::text, index_name::text;
```

The project search vector has a GIN index. Project and interest embeddings have IVFFlat cosine indexes. For a plan demonstration, use a sufficiently populated database and compare:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM faculty_projects
WHERE search_vector @@ plainto_tsquery('english', 'climate research');
```

PostgreSQL may choose a sequential scan on a small demonstration database; that is a cost-based planner choice, not evidence that the index is absent.

## 3. Trigger and maintained search document

```sql
SELECT tgname, pg_get_triggerdef(oid)
FROM pg_trigger
WHERE NOT tgisinternal AND tgrelid IN
  ('faculty_projects'::regclass, 'student_interests'::regclass, 'applications'::regclass)
ORDER BY tgrelid::regclass::text, tgname;

SELECT id, title, search_vector,
       search_vector @@ plainto_tsquery('english', 'climate adaptation') AS matches
FROM faculty_projects
ORDER BY created_at DESC
LIMIT 5;
```

The `trg_faculty_projects_maintain` trigger updates `updated_at` and rebuilds `search_vector` on insert/update. Timestamp triggers on interests and applications keep `updated_at` current. An API project insert followed by `PATCH /api/v1/projects/{id}` demonstrates the automatic update. The API uses bound SQL expressions for user-supplied search terms.

## 4. View and stored function

```sql
SELECT project_id, title, application_count, pending_application_count
FROM open_projects_with_application_stats
ORDER BY application_count DESC, title
LIMIT 10;

SELECT project_id, title, similarity
FROM match_open_projects(
  (SELECT student_id FROM student_interests ORDER BY updated_at DESC LIMIT 1),
  10
);
```

The view reports counts for open projects. The function returns open projects ranked by cosine similarity to the chosen student's interest embedding. If there are no interest rows, create a student and profile through the API first. It clamps its requested result limit to 1–100.

## 5. Full-text and vector search

```sql
SELECT id, title,
       ts_rank_cd(search_vector, plainto_tsquery('english', 'climate adaptation')) AS rank
FROM faculty_projects
WHERE status = 'OPEN'
  AND search_vector @@ plainto_tsquery('english', 'climate adaptation')
ORDER BY rank DESC, created_at DESC
LIMIT 10;

SELECT format_type(a.atttypid, a.atttypmod) AS embedding_type
FROM pg_attribute AS a
WHERE a.attrelid = 'faculty_projects'::regclass AND a.attname = 'embedding';

SELECT p.id, p.title, 1 - (p.embedding <=> si.embedding) AS cosine_similarity
FROM student_interests AS si
JOIN faculty_projects AS p ON p.status = 'OPEN'
WHERE si.student_id = (SELECT student_id FROM student_interests ORDER BY updated_at DESC LIMIT 1)
  AND vector_norm(si.embedding) > 0
  AND vector_norm(p.embedding) > 0
ORDER BY p.embedding <=> si.embedding
LIMIT 10;
```

The embedding type must report `vector(384)`. Full-text search matches lexemes; vector search compares semantic embeddings generated by `sentence-transformers/all-MiniLM-L6-v2`. The application recommendation route obtains the student ID from the validated bearer token rather than accepting it from the client.

## 6. Transactions and rollback

```sql
BEGIN;
UPDATE faculty_projects
SET status = 'CLOSED'
WHERE id = (SELECT id FROM faculty_projects WHERE status = 'OPEN' ORDER BY created_at DESC LIMIT 1);
SELECT status FROM faculty_projects ORDER BY updated_at DESC LIMIT 1;
ROLLBACK;
```

The update is visible in the current transaction and undone by `ROLLBACK`. The automated API fixtures similarly wrap test rows in a transaction and roll it back; they do not reset the development database.

## 7. Useful API demonstration sequence

1. `GET /api/v1/departments` and copy an existing department UUID.
2. Register one `FACULTY` and one `STUDENT` account using `POST /api/v1/auth/register`; log each in and use its access token as `Authorization: Bearer <token>`.
3. As faculty, create a project with `POST /api/v1/projects`; update it using `PATCH /api/v1/projects/{id}` and observe the trigger-maintained timestamp/search vector.
4. As student, create an interest profile at `POST /api/v1/students/me/interests`; observe `/api/v1/recommendations` rank open projects. Compare with `/api/v1/projects/search?q=...` for lexical matching.
5. Apply at `POST /api/v1/projects/{id}/applications`; list it as the faculty owner and change its pending status to accepted/rejected.

These API actions create persistent demonstration data. Choose clearly labeled demo accounts/projects and use normal application endpoints to close projects when finished; do not delete rows with dependent applications.
