INSERT OR IGNORE INTO JOBS (
    source_id,
    job_title,
    description,
    company,
    content_hash
)
VALUES(
    ?, ?, ?, ?, ?
);