# Replace the values as needed
PROJECT_ID = "$PROJECT_ID"
PUBSUB_TOPIC = "$PUBSUB_TOPIC"
BIGQUERY_DATASET = "$BIGQUERY_DATASET"
BIGQUERY_TABLE = "$BIGQUERY_TABLE"

# Add/Update the queries for your metrics
MQL_QUERYS = {
"instance/cpu/utilization":
"""
fetch gce_instance::compute.googleapis.com/instance/cpu/utilization
| bottom 3, max(val()) | within 5m
""",

# "bigquery/slots/total_available":
# """
# fetch global
# | metric 'bigquery.googleapis.com/slots/total_available'
# | group_by 5m, [value_total_available_mean: mean(value.total_available)]
# | every 5m | within 1h
# """,

# "bigquery/slots/allocated_for_project":
# """
# fetch global
# | metric 'bigquery.googleapis.com/slots/allocated_for_project'
# | group_by 5m,
#     [value_allocated_for_project_mean: mean(value.allocated_for_project)]
# | every 5m | within 1h
# """
}

BASE_URL = "https://monitoring.googleapis.com/v3/projects"
QUERY_URL = f"{BASE_URL}/{PROJECT_ID}/timeSeries:query"


BQ_VALUE_MAP = {
    "INT64": "int64_value",
    "BOOL": "boolean_value",
    "DOUBLE": "double_value",
    "STRING": "string_value",
    "DISTRIBUTION": "distribution_value"
}

API_VALUE_MAP = {
    "INT64": "int64Value",
    "BOOL": "booleanValue",
    "DOUBLE": "doubleValue",
    "STRING": "stringValue",
    "DISTRIBUTION": "distributionValue"
}