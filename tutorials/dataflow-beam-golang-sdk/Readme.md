# Apache Beam Golang Examples

## Example 1
Dataflow Runner : PubSub to BigQuery using coGroupbyKey, pubsubio and bigqueryio

### Instructions to Run
```
go run main.go --project=$PROJECT_ID \
--runner=dataflow --region=$REGION \
--staging_location=$BUCKET_AND_FOLDER \
--service_account_email=$SERVICE_ACCOUNT_EMAIL
```