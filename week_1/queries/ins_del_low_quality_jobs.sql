INSERT INTO jobs_quarantine
SELECT *
FROM jobs
WHERE quality = 'LOW';

DELETE FROM jobs
WHERE quality = 'LOW';