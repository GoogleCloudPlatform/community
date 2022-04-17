#standardSQL
CREATE OR REPLACE MODEL `<bq_dataset>.county_covid_model`
OPTIONS
  (model_type='KMEANS',
    NUM_CLUSTERS = 3,
    KMEANS_INIT_METHOD = 'KMEANS++',
    STANDARDIZE_FEATURES = TRUE
    ) AS
SELECT
  percent_new_confirmed,
  percent_new_deceased,
  percent_fully_vaccinated
FROM
  `<gcp_project>.<bq_dataset>.county_2021_view`