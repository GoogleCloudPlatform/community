SELECT
  covid.date_week,
  covid.state,
  covid.state_name,
  covid.seven_day_confirmed,
  covid.seven_day_deceased,
  covid.seven_day_new_vaccinated,
  covid.population,
  covid.cumulative_persons_fully_vaccinated,
  covid.cumulative_confirmed,
  covid.cumulative_deceased,
  ROUND((covid.seven_day_confirmed/covid.population)*100,2) AS percent_new_confirmed,
  ROUND((covid.seven_day_deceased/covid.population)*100,2) AS percent_new_deceased,
  ROUND((covid.cumulative_persons_fully_vaccinated/covid.population)*100,2) AS percent_fully_vaccinated,
  ROUND((covid.seven_day_new_vaccinated/covid.population)*100,2) AS percent_new_persons_vaccinated,
  mobility.transit_stations_percent_change_from_baseline,
  mobility.grocery_and_pharmacy_percent_change_from_baseline,
  mobility.retail_and_recreation_percent_change_from_baseline,
  mobility.workplaces_percent_change_from_baseline,
  mobility.census_fips_code AS county_fips_code,
  county.county_geom,
  county.county_name,
  county.state_fips_code
FROM (
  SELECT
    DATE_TRUNC(date, WEEK) AS date_week,
    date AS as_of_date,
    SUM(new_confirmed) AS seven_day_confirmed,
    SUM(new_deceased) AS seven_day_deceased,
    SUM(new_persons_vaccinated) AS seven_day_new_vaccinated,
    subregion1_code AS state,
    subregion1_name AS state_name,
    SUBSTR(location_key,7) AS geo_id,
    cumulative_persons_fully_vaccinated,
    new_confirmed,
    cumulative_confirmed,
    new_deceased,
    cumulative_deceased,
    new_persons_vaccinated,
    population,
  FROM
    `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE
    STRING(date) LIKE '2022-%'
    AND date = DATE_TRUNC(date, WEEK)
    AND aggregation_level = 2 --level 1 is for the entire state
    AND country_code = 'US' --we only want the US for now
  GROUP BY
    date_week,
    date,
    state,
    state_name,
    geo_id,
    cumulative_persons_fully_vaccinated,
    new_confirmed,
    cumulative_confirmed,
    new_deceased,
    cumulative_deceased,
    new_persons_vaccinated,
    population) AS covid
JOIN (
  SELECT
    DATE_TRUNC(date, WEEK) as date,
    transit_stations_percent_change_from_baseline,
    grocery_and_pharmacy_percent_change_from_baseline,
    retail_and_recreation_percent_change_from_baseline,
    workplaces_percent_change_from_baseline,
    SUBSTR(FORMAT("00000%d", CAST(SUBSTR(census_fips_code, 0, LENGTH(census_fips_code) - 2) AS INT64)), -5) AS census_fips_code,
    country_region_code
  FROM
    `bigquery-public-data.covid19_google_mobility.mobility_report`
  WHERE
    STRING(date) LIKE '2022-%'
    AND census_fips_code IS NOT NULL) AS mobility
ON
  covid.date_week = mobility.date
  AND covid.geo_id = mobility.census_fips_code
LEFT JOIN
  `bigquery-public-data.utility_us.us_county_area` AS county
ON
  covid.geo_id = county.geo_id
WHERE
  mobility.country_region_code = 'US'