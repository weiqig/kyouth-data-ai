UPDATE jobs
SET quality = CASE
    WHEN LENGTH(description) > 100 THEN 'HIGH'
    ELSE 'LOW'
END;