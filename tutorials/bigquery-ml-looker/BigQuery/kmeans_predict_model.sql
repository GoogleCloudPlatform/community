#standardSQL
SELECT
  CENTROID_ID AS covid_risk_score,
  date_week AS as_of_date,
  county_name,
  state,
  county_fips_code,
  seven_day_confirmed,
  seven_day_deceased
FROM
  ML.PREDICT( MODEL `<bq_dataset>.county_covid_model`,
    (
    SELECT
      cv.*
    FROM
      `<bq_dataset>.county_2022_view` cv
    INNER JOIN (
      SELECT
        DISTINCT county_name AS county_name,
        MAX(date_week) AS date_week
      FROM
        `<bq_dataset>.county_2022_view`
      GROUP BY
        county_name ) grouped_cv
    ON
      cv.county_name = grouped_cv.county_name
      AND cv.date_week = grouped_cv.date_week ) )