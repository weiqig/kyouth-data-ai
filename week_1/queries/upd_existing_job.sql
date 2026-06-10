UPDATE JOBS
SET job_title = ?,
    description = ?,
    company = ?,
    content_hash = ?
WHERE source_id = ?;