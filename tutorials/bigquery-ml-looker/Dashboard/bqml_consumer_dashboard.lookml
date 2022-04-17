- dashboard: demo_bqml_consumer_dashboard
  title: Demo_BQML_Consumer_Dashboard
  layout: newspaper
  preferred_viewer: dashboards-next
  description: ''
  elements:
  - name: ''
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: |-
      ##### Risk Score (1-3 Scale) <br/>
      1 = Lowest <br/>
      2 = Moderately <br/>
      3 = High
    row: 9
    col: 19
    width: 5
    height: 3
  - name: " (2)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: |-
      ## **Consumer** <br/>
      Where should I go on vacation in the United States within the next week to minimize my COVID risk?
    row: 0
    col: 0
    width: 14
    height: 3
  - name: " (3)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: ''
    row: 0
    col: 20
    width: 4
    height: 9
  - title: COVID Analysis Map
    name: COVID Analysis Map
    model: covid-bqml-demo
    explore: county_covid_model
    type: looker_map
    fields: [county_covid_model.county_fips_code, county_covid_model.as_of_date, county_covid_model.covid_risk_score,
      county_covid_model.seven_day_confirmed, county_covid_model.seven_day_deceased,
      county_covid_model.county_name, county_covid_model.state, county_covid_model.transit_percent,
      county_covid_model.workplaces_percent, county_covid_model.retail_and_rec_percent,
      county_covid_model.grocery_and_pharmacy_percent]
    sorts: [county_covid_model.as_of_date desc]
    limit: 5000
    query_timezone: UTC
    map_plot_mode: points
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: light
    map_position: fit_data
    map_scale_indicator: 'off'
    map_pannable: true
    map_zoomable: true
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: meters
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_view_names: false
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    defaults_version: 1
    listen:
      County Name: county_covid_model.county_name
      Covid Risk Score: county_covid_model.covid_risk_score
      State: county_covid_model.state
    row: 3
    col: 0
    width: 19
    height: 9
  filters:
  - name: State
    title: State
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: tag_list
      display: popover
      options: []
    model: covid-bqml-demo
    explore: county_covid_model
    listens_to_filters: []
    field: county_covid_model.state
  - name: County Name
    title: County Name
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: tag_list
      display: popover
      options: []
    model: covid-bqml-demo
    explore: county_covid_model
    listens_to_filters: []
    field: county_covid_model.county_name
  - name: Covid Risk Score
    title: Covid Risk Score
    type: field_filter
    default_value: "[1,3]"
    allow_multiple_values: true
    required: false
    ui_config:
      type: range_slider
      display: inline
      options:
        min: 1
        max: 3
    model: covid-bqml-demo
    explore: county_covid_model
    listens_to_filters: []
    field: county_covid_model.covid_risk_score