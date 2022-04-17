view: county_covid_model {

  derived_table: {
    sql:
      SELECT
          CENTROID_ID as covid_risk_score,
          date_week as as_of_date,
          county_name,
          state,
          county_fips_code,
          seven_day_confirmed,
          seven_day_deceased,
          transit_stations_percent_change_from_baseline,
          workplaces_percent_change_from_baseline,
          retail_and_recreation_percent_change_from_baseline,
          grocery_and_pharmacy_percent_change_from_baseline
      FROM ML.PREDICT(
          MODEL `@{COVID_BQML_DATASET}.county_covid_model`, (
              SELECT
                  cv.*
              FROM `@{COVID_BQML_DATASET}.county_2022_view` cv
              INNER JOIN (
                  SELECT
                      distinct county_name as county_name,
                      max(date_week) as date_week
                  FROM `@{COVID_BQML_DATASET}.county_2022_view`
                  GROUP BY county_name
              ) grouped_cv
              ON cv.county_name = grouped_cv.county_name
              AND cv.date_week = grouped_cv.date_week
              )
          );;
  }

  dimension: row {
    type: number
    primary_key: yes
    sql: ${TABLE}.row ;;
  }
  dimension: covid_risk_score {
    type: number
    sql: ${TABLE}.covid_risk_score ;;
  }
  dimension: as_of_date {
    type: date
    sql: ${TABLE}.as_of_date ;;
  }
  dimension: state {
    type: string
    sql: ${TABLE}.state ;;
  }
  dimension: county_name {
    type: string
    sql: ${TABLE}.county_name ;;
  }
  dimension: county_fips_code {
    map_layer_name: us_counties_fips
    type:  string
    sql: ${TABLE}.county_fips_code ;;
  }
  dimension: seven_day_confirmed {
    type:  number
    sql:  ${TABLE}.seven_day_confirmed ;;
  }
  dimension: seven_day_deceased {
    type:  number
    sql:  ${TABLE}.seven_day_deceased ;;
  }
  dimension: grocery_and_pharmacy_percent {
    type:  number
    value_format: "0.00\%"
    sql:  ${TABLE}.grocery_and_pharmacy_percent_change_from_baseline ;;
  }
  dimension: retail_and_rec_percent {
    type:  number
    value_format: "0.00\%"
    sql:  ${TABLE}.retail_and_recreation_percent_change_from_baseline ;;
  }
  dimension: workplaces_percent {
    type:  number
    value_format: "0.00\%"
    sql:  ${TABLE}.workplaces_percent_change_from_baseline ;;
  }
  dimension: transit_percent {
    type:  number
    value_format: "0.00\%"
    sql:  ${TABLE}.transit_stations_percent_change_from_baseline ;;
  }
}
