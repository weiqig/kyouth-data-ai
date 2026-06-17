SELECT source_id as id, description as desc, tech_stack
FROM JOBS
WHERE tech_stack IS NULL
LIMIT ?;