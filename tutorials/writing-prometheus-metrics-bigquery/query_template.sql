SELECT
  metricname,
  tags,
  JSON_EXTRACT(tags,
    '$.service') AS service,
  value,
  timestamp
FROM
  `${PROJECT_ID}.${BIGQUERY_DATASET}.${BIGQUERY_TABLE}`
WHERE
  JSON_EXTRACT(tags,
    '$.status') = "\"200\""
  AND JSON_EXTRACT(tags,
    '$.service') = "\"example-app\""
LIMIT
  10
