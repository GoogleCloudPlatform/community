# Web Scraping

Web scraping from a list of input IDs from a BigQuery table to another BigQuery table storing the results.

## Variables

```bash

# PROJECT_ID=kyl-alto-web-scrape-359204

# Get the current project id
PROJECT_ID=$(gcloud config get-value project)
echo PROJECT_ID=$PROJECT_ID

# project number
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(project_number)")
echo PROJECT_NUMBER=$PROJECT_NUMBER

NETWORK="default"
REGION="us-central1"
REGIONS=( $REGION )

# Spanner properties
export SPANNER_INSTANCE="job-metadata-instance"
export SPANNER_DATABASE="job-metadata-database"
export SPANNER_BQ_CONNECTION="job-metadata-connection"
SPANNER_PROCESSING_UNITS="100"

SPANNER_TABLE="job_executions"

SPANNER_DDL_TRANSACTIONS="CREATE TABLE $SPANNER_TABLE (
  jobExecutionId STRING(MAX),
  jobExecutionStartTimestamp TIMESTAMP,
  jobExecutionEndTimestamp TIMESTAMP,
  inputIdCount INT64
) PRIMARY KEY (jobExecutionId)
"
#, ROW DELETION POLICY (OLDER_THAN(jobExecutionStartTimestamp, INTERVAL 3650 DAY));


# Cloud Run
CLOUD_RUN_SERVICE_LOAD="load-records-to-pubsub"
CLOUD_RUN_SERVICE_PROCESS="scrape"
CLOUD_RUN_SERVICE_GET="get-job-status"
CLOUD_RUN_MIN_INSTANCES="0"

BQ_DATASET="web_scraping"
BQ_INPUT_RECORDS_TABLE="input_records"
BQ_DATASET_REGION="us"
#BQ_JOB_EXECUTIONS_TABLE="job_executions"
BQ_OUTPUT_RECORDS_TABLE="output_records"
BQ_PUBSUB_ARCHIVE_DATASET="pubsub_archive"


# PubSub
export INPUT_RECORDS_PUBSUB_TOPIC="input-records-topic"
export OUTPUT_RECORDS_PUBSUB_TOPIC="output-records-topic"

# PubSub Output Records Schema
# TODO - BQ Subscription doesn't support any Avro logical data types yet (e.g. timestamp, decimal)
# null field support is also insufficient https://stackoverflow.com/questions/72046941/is-there-a-way-to-make-google-cloud-pub-sub-schema-fields-optional
OUTPUT_RECORDS_PUBSUB_TOPIC_SCHEMA='
{
 "type" : "record",
 "name" : "Avro",
 "fields" : [
   { "name" : "jobExecutionId", "type" : "string" },
   { "name" : "scrapeDate", "type" : "string" },
   { "name" : "scrapeTimestamp", "type" : "string" },
   { "name" : "skuId", "type" : "string" },
   { "name" : "sellerCount", "type" : "int" },
   { "name" : "mfgNumber", "type" : "string" },
   { "name" : "productTitle", "type" : "string" },
   { "name" : "bbWinner", "type" : "string" },
   { "name" : "bbPrice", "type" : "string" },
   { "name" : "shipCost", "type" : "string" },
   { "name" : "siteChoice", "type" : "string" },
   { "name" : "fba", "type" : "string" },
   { "name" : "brand", "type" : "string" },
   { "name" : "productUrl", "type" : "string" },
   { "name" : "productCustomerReviews", "type" : "int" },
   { "name" : "productStarRating", "type" : "string" },
   { "name" : "productDimensions", "type" : "string" },
   { "name" : "itemWeight", "type" : "string" },
   { "name" : "shipWeight", "type" : "string" },
   { "name" : "itemNumber", "type" : "string" },
   { "name" : "skuCreationDate", "type" : "string" },
   { "name" : "returnsPolicy", "type" : "string" },
   { "name" : "currentlyUnavailable", "type" : "string" },
   { "name" : "r1Number", "type" : "int" },
   { "name" : "r1Cat", "type" : "string" },
   { "name" : "r2Number", "type" : "int" },
   { "name" : "r2Cat", "type" : "string" },
   { "name" : "r3Number", "type" : "int" },
   { "name" : "r3Cat", "type" : "string" },
   { "name" : "r4Number", "type" : "int" },
   { "name" : "r4Cat", "type" : "string" }
 ]
}'

# { "name" : "bbPrice", "type" : "float" },
# { "name" : "shipCost", "type" : "float" },
# { "name" : "productStarRating", "type" : "float" },


# GCS
export GCS_BUCKET="${PROJECT_ID}-${REGION}"

WORKFLOW="web-scraping"
SCHEDULER="web-scraping-scheduler"

export URL_PATTERN="https://get-product.endpoints.kyl-alto-ecommerce-site-358914.cloud.goog/product/{}"

```

## Project Setup

```bash
gcloud services enable workflows.googleapis.com spanner.googleapis.com pubsub.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com eventarc.googleapis.com cloudscheduler.googleapis.com

gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker --location=$REGION
```

## Create PubSub Topics, GCS bucket and BQ tables

```bash

gcloud pubsub topics create $INPUT_RECORDS_PUBSUB_TOPIC

# gcloud pubsub schemas delete "${OUTPUT_RECORDS_PUBSUB_TOPIC}-schema" --quiet
gcloud pubsub schemas create "${OUTPUT_RECORDS_PUBSUB_TOPIC}-schema" --type="AVRO" --definition="$OUTPUT_RECORDS_PUBSUB_TOPIC_SCHEMA"
gcloud pubsub schemas describe "${OUTPUT_RECORDS_PUBSUB_TOPIC}-schema"

# gcloud pubsub topics create $OUTPUT_RECORDS_PUBSUB_TOPIC
# gcloud pubsub topics delete $OUTPUT_RECORDS_PUBSUB_TOPIC
gcloud pubsub topics create $OUTPUT_RECORDS_PUBSUB_TOPIC \
        --message-encoding="JSON" \
        --schema="${OUTPUT_RECORDS_PUBSUB_TOPIC}-schema"

# permissions for BQ subscription
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com" --role="roles/bigquery.metadataViewer"

# create the BQ tables and subscription for archiving
bq mk $BQ_PUBSUB_ARCHIVE_DATASET
for TOPIC in $INPUT_RECORDS_PUBSUB_TOPIC $OUTPUT_RECORDS_PUBSUB_TOPIC
do
    ARCHIVE_TABLE="${TOPIC//-/_}_archive"

    # bq rm -t -f $BQ_DATASET.$ARCHIVE_TABLE
    bq mk --schema subscription_name:string,message_id:string,publish_time:timestamp,data:string,attributes:string \
    -t \
    --clustering_fields message_id \
    --time_partitioning_field publish_time \
    --time_partitioning_type DAY \
    $BQ_PUBSUB_ARCHIVE_DATASET."$ARCHIVE_TABLE"
    #--time_partitioning_expiration 315619200 \

    # gcloud pubsub subscriptions delete ${TOPIC}-archive
    gcloud pubsub subscriptions create ${TOPIC}-archive \
    --topic=$TOPIC \
    --bigquery-table=$PROJECT_ID:$BQ_PUBSUB_ARCHIVE_DATASET."$ARCHIVE_TABLE" \
    --write-metadata
done

# create the BQ table and subscription for the output records

# bq rm -t -f $BQ_DATASET.$BQ_OUTPUT_RECORDS_TABLE
# awaiting for fix on BQ float types
bq mk --schema "
subscription_name:string
,message_id:string
,publish_time:timestamp
,data:string
,attributes:string
,jobExecutionId:string
,scrapeDate:string
,scrapeTimestamp:string
,skuId:string
,sellerCount:integer
,mfgNumber:string
,productTitle:string
,bbWinner:string
,bbPrice:float
,shipCost:float
,siteChoice:string
,fba:string
,brand:string
,productUrl:string
,productCustomerReviews:integer
,productStarRating:float
,productDimensions:string
,itemWeight:string
,shipWeight:string
,itemNumber:string
,skuCreationDate:string
,returnsPolicy:string
,currentlyUnavailable:string
,r1Number:integer
,r1Cat:string
,r2Number:integer
,r2Cat:string
,r3Number:integer
,r3Cat:string
,r4Number:integer
,r4Cat:string
" \
-t \
--clustering_fields message_id \
--time_partitioning_field publish_time \
--time_partitioning_type DAY \
$BQ_DATASET."$BQ_OUTPUT_RECORDS_TABLE"
#--time_partitioning_expiration 315619200 \

# TODO using string for now until float is supported
bq mk --schema "
subscription_name:string
,message_id:string
,publish_time:timestamp
,data:string
,attributes:string
,jobExecutionId:string
,scrapeDate:string
,scrapeTimestamp:string
,skuId:string
,sellerCount:integer
,mfgNumber:string
,productTitle:string
,bbWinner:string
,bbPrice:string
,shipCost:string
,siteChoice:string
,fba:string
,brand:string
,productUrl:string
,productCustomerReviews:integer
,productStarRating:string
,productDimensions:string
,itemWeight:string
,shipWeight:string
,itemNumber:string
,skuCreationDate:string
,returnsPolicy:string
,currentlyUnavailable:string
,r1Number:integer
,r1Cat:string
,r2Number:integer
,r2Cat:string
,r3Number:integer
,r3Cat:string
,r4Number:integer
,r4Cat:string
" \
-t \
--clustering_fields message_id \
--time_partitioning_field publish_time \
--time_partitioning_type DAY \
$BQ_DATASET."$BQ_OUTPUT_RECORDS_TABLE"

# this has to be recreated if the BQ schema is updated (e.g. fields added)
# gcloud pubsub subscriptions delete ${OUTPUT_RECORDS_PUBSUB_TOPIC}-bigquery
gcloud pubsub subscriptions create ${OUTPUT_RECORDS_PUBSUB_TOPIC}-bigquery \
    --topic=$OUTPUT_RECORDS_PUBSUB_TOPIC \
    --bigquery-table=$PROJECT_ID:$BQ_DATASET."$BQ_OUTPUT_RECORDS_TABLE" \
    --use-topic-schema \
    --drop-unknown-fields \
    --write-metadata


# GCS bucket
gsutil mb -l ${REGION} gs://$GCS_BUCKET

echo '
{
  "rule":
  [
    { "action": {"type": "SetStorageClass","storageClass":"NEARLINE"}, "condition": {"age": 30} }
    ,{ "action": {"type": "SetStorageClass","storageClass":"COLDLINE"}, "condition": {"age": 90} }
    ,{ "action": {"type": "SetStorageClass","storageClass":"ARCHIVE"}, "condition": {"age": 365} }
  ]
}' | gsutil lifecycle set /dev/stdin gs://$GCS_BUCKET
    #,{ "action": {"type": "Delete"}, "condition": {"age": 3650} }

# required for eventarc audit log approach
# echo "
# $(gcloud projects get-iam-policy $PROJECT_ID)
# auditConfigs:
# - auditLogConfigs:
#   - logType: ADMIN_READ
#   - logType: DATA_WRITE
#   - logType: DATA_READ
#   service: storage.googleapis.com
# " | gcloud projects set-iam-policy $PROJECT_ID  /dev/stdin

# Grant the pubsub.publisher role to the Cloud Storage service account:
GCS_SERVICE_ACCOUNT="$(gsutil kms serviceaccount -p $PROJECT_ID)"
echo GCS_SERVICE_ACCOUNT=$GCS_SERVICE_ACCOUNT
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${GCS_SERVICE_ACCOUNT}" --role='roles/pubsub.publisher'

```

## Create job metadata tables (BigQuery)

```bash

# bq rm --table -f $BQ_DATASET.$BQ_JOB_EXECUTIONS_TABLE
# bq mk --table \
#   --schema jobExecutionId:string,jobExecutionStartTimestamp:timestamp,inputIdCount:integer \
#   --clustering_fields jobExecutionId \
#   --time_partitioning_field jobExecutionStartTimestamp \
#   --time_partitioning_type MONTH \
#   $BQ_DATASET.$BQ_JOB_EXECUTIONS_TABLE
#   #--time_partitioning_expiration 315619200 \

```

## Create job metadata tables (Cloud Spanner)

```bash

gcloud spanner instances create $SPANNER_INSTANCE --config=regional-$REGION --description=$SPANNER_INSTANCE --processing-units="$SPANNER_PROCESSING_UNITS"
gcloud spanner databases create $SPANNER_DATABASE --instance=$SPANNER_INSTANCE

gcloud spanner databases ddl update $SPANNER_DATABASE --instance=$SPANNER_INSTANCE --ddl="${SPANNER_DDL_TRANSACTIONS}"

# create connection for federated query
bq mk --connection \
  --connection_type='CLOUD_SPANNER' \
  --properties="{\"database\":\"projects/$PROJECT_ID/instances/$SPANNER_INSTANCE/databases/$SPANNER_DATABASE\"}" \
  --project_id=$PROJECT_ID \
  --location=us \
  "$SPANNER_BQ_CONNECTION"



```

## Service - load-records-to-pubsub

```bash
# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_SERVICE_LOAD
source ~/.venv/$CLOUD_RUN_SERVICE_LOAD/bin/activate
pip install -r $CLOUD_RUN_SERVICE_LOAD/requirements.txt

# run this to test via browser
# gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app --chdir $CLOUD_RUN_SERVICE_LOAD --reload
# run this to test the individual function
# python3 $CLOUD_RUN_SERVICE_UPSERT/main.py '{"Table":"Results","Url":"https://www.amazon.com/dp/B00367ZH2U/"}'
python3 $CLOUD_RUN_SERVICE_LOAD/main.py "kyl-alto-web-scrape-359204-us-central1" "input-records/ed83c289-fd12-47ec-9006-792a31c981c3/000000000000.json"

# Build the docker image and tag it for Container Registry
#docker build -t web-scraping:0.1 .
#docker run -it web-scraping:0.1 bash
#python3 main.py '{"Table":"Results","Url":"https://www.amazon.com/McKesson-Confiderm-Powder-MEDIUM-14-1382/dp/B01ETFG640"}'
python3 $CLOUD_RUN_SERVICE_LOAD/main.py "kyl-alto-web-scrape-359204-us-central1" "input-records/ed83c289-fd12-47ec-9006-792a31c981c3/000000000000.json"

gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_LOAD}-sa"

#gsutil iam ch serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-sa@$PROJECT_ID.iam.gserviceaccount.com:objectViewer gs://${GCS_BUCKET}
gsutil iam ch serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-sa@$PROJECT_ID.iam.gserviceaccount.com:admin gs://${GCS_BUCKET}

gcloud pubsub topics add-iam-policy-binding "${INPUT_RECORDS_PUBSUB_TOPIC}" --member "serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/pubsub.publisher --project ${PROJECT_ID}

# Cloud Run ingress can stay internal
gcloud run deploy $CLOUD_RUN_SERVICE_LOAD --source=$CLOUD_RUN_SERVICE_LOAD/ --platform managed --region $REGION --set-env-vars INPUT_RECORDS_PUBSUB_TOPIC="$INPUT_RECORDS_PUBSUB_TOPIC" --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_LOAD}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --cpu-throttling --timeout=3600
# --no-cpu-throttling

gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_LOAD}-trigger"
gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_LOAD} --region=$REGION \
  --member="serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-trigger@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/run.invoker'

# does not support path pattern
gcloud eventarc triggers create ${CLOUD_RUN_SERVICE_LOAD}-trigger \
     --location=$REGION \
     --destination-run-service=${CLOUD_RUN_SERVICE_LOAD} \
     --destination-run-region=$REGION \
     --event-filters="type=google.cloud.storage.object.v1.finalized" \
     --event-filters="bucket=${GCS_BUCKET}" \
     --service-account="${CLOUD_RUN_SERVICE_LOAD}-trigger@${PROJECT_ID}.iam.gserviceaccount.com"

# update ackDeadline from the default 10 seconds
gcloud pubsub subscriptions update $(gcloud eventarc triggers describe ${CLOUD_RUN_SERVICE_LOAD}-trigger --location=$REGION --format="value(transport.pubsub.subscription)") --ack-deadline=600

#gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-trigger@${PROJECT_ID}.iam.gserviceaccount.com"  --role="roles/eventarc.eventReceiver"
# gcloud eventarc triggers delete ${CLOUD_RUN_SERVICE_LOAD}-trigger --location=$REGION
# WARNING: It may take up to 10 minutes for the new trigger to become active.
# gcloud eventarc triggers create ${CLOUD_RUN_SERVICE_LOAD}-trigger \
#      --location=$REGION \
#      --destination-run-service=${CLOUD_RUN_SERVICE_LOAD} \
#      --destination-run-region=$REGION \
#      --event-filters="type=google.cloud.audit.log.v1.written" \
#      --event-filters="serviceName=storage.googleapis.com" \
#      --event-filters="methodName=storage.objects.create" \
#      --event-filters-path-pattern="resourceName=/projects/_/buckets/${GCS_BUCKET}/objects/input-records/*" \
#      --service-account="${CLOUD_RUN_SERVICE_LOAD}-trigger@${PROJECT_ID}.iam.gserviceaccount.com"


```

## Service - scrape

```bash
# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_SERVICE_PROCESS
source ~/.venv/$CLOUD_RUN_SERVICE_PROCESS/bin/activate
pip install -r $CLOUD_RUN_SERVICE_PROCESS/requirements.txt

# run this to test via browser
# gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app --chdir $CLOUD_RUN_SERVICE_LOAD --reload
# run this to test the individual function
# python3 $CLOUD_RUN_SERVICE_PROCESS/main.py '{"id":"000003b7-4f08-4bc7-b286-9f68ed1df546","jobExecutionId":"d42dc9ce-f3d8-4fa2-966d-964c16efe572"}'


gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_PROCESS}-sa"
#gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/spanner.databaseUser"
#gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/storage.admin"

gcloud pubsub topics add-iam-policy-binding "${OUTPUT_RECORDS_PUBSUB_TOPIC}" --member "serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/pubsub.publisher --project ${PROJECT_ID}

# Cloud Run ingress can stay internal
gcloud beta run deploy $CLOUD_RUN_SERVICE_PROCESS --source=$CLOUD_RUN_SERVICE_PROCESS/ --platform managed --region $REGION --set-env-vars OUTPUT_RECORDS_PUBSUB_TOPIC="$OUTPUT_RECORDS_PUBSUB_TOPIC",URL_PATTERN="${URL_PATTERN}" --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --cpu-throttling --concurrency=1 --max-instances=4000 --memory=256Mi --cpu=0.25 --execution-environment="gen1"
#--execution-environment="gen2" #gen2 min cpu is 1
# --no-cpu-throttling

# gcloud iam service-accounts delete "${CLOUD_RUN_SERVICE_PROCESS}-trigger"
gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_PROCESS}-trigger"
gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_PROCESS} --region=$REGION \
  --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-trigger@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/run.invoker'

gcloud eventarc triggers create ${CLOUD_RUN_SERVICE_PROCESS}-trigger \
     --location=$REGION \
     --destination-run-service=${CLOUD_RUN_SERVICE_PROCESS} \
     --destination-run-region=$REGION \
     --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
     --transport-topic="projects/$PROJECT_ID/topics/$INPUT_RECORDS_PUBSUB_TOPIC" \
     --service-account="${CLOUD_RUN_SERVICE_PROCESS}-trigger@${PROJECT_ID}.iam.gserviceaccount.com"

# update ackDeadline from the default 10 seconds 
gcloud pubsub subscriptions update $(gcloud eventarc triggers describe ${CLOUD_RUN_SERVICE_PROCESS}-trigger --location=$REGION --format="value(transport.pubsub.subscription)") --ack-deadline=60

```

## Service - get job status

```bash
# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_SERVICE_GET
source ~/.venv/$CLOUD_RUN_SERVICE_GET/bin/activate
pip install -r $CLOUD_RUN_SERVICE_GET/requirements.txt

# run this to test via browser
# gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app --chdir $CLOUD_RUN_SERVICE_GET --reload
# run this to test the individual function
# python3 $CLOUD_RUN_SERVICE_GET/main.py '53a708d8-d352-4ef8-9589-b5c0c2ad1cdf'


gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_GET}-sa"

gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_GET}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.jobUser"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_GET}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_GET}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.connectionUser"

gcloud spanner instances add-iam-policy-binding $SPANNER_INSTANCE --member="serviceAccount:${CLOUD_RUN_SERVICE_GET}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/spanner.databaseUser"

# Cloud Run ingress can stay internal
gcloud beta run deploy $CLOUD_RUN_SERVICE_GET --source=$CLOUD_RUN_SERVICE_GET/ --platform managed --region $REGION  --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_GET}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --cpu-throttling 
#gcloud beta run deploy $CLOUD_RUN_SERVICE_GET --source=$CLOUD_RUN_SERVICE_GET/ --platform managed --region $REGION --set-env-vars SPANNER_BQ_CONNECTION="$SPANNER_BQ_CONNECTION" --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_GET}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --cpu-throttling 
#--execution-environment="gen2" #gen2 min cpu is 1
# --no-cpu-throttling

gcloud run services describe $CLOUD_RUN_SERVICE_GET --region $REGION 

CLOUD_RUN_SERVICE_GET_URL=$(gcloud run services describe $CLOUD_RUN_SERVICE_GET --region $REGION  --format="value(status.url)")
echo CLOUD_RUN_SERVICE_GET_URL=$CLOUD_RUN_SERVICE_GET_URL


```

## Cloud Workflow

```bash

gcloud iam service-accounts create ${WORKFLOW}-sa

gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com"  --role="roles/logging.logWriter"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.jobUser"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor"

gsutil iam ch serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://${GCS_BUCKET}

gcloud spanner instances add-iam-policy-binding $SPANNER_INSTANCE --member="serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/spanner.databaseUser"

gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_GET} --region=$REGION \
  --member="serviceAccount:${WORKFLOW}-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/run.invoker'

gcloud workflows deploy $WORKFLOW --location=$REGION --source=workflows/web-scraping.yaml --service-account=${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com


# use the scheduler command below
gcloud workflows run $WORKFLOW --location=$REGION --data='{"storageBucket":"'$GCS_BUCKET'","jobExecutionSpannerInstance":"'$SPANNER_INSTANCE'","jobExecutionSpannerDatabase":"'$SPANNER_DATABASE'","inputRecordsSqlLimitClause":"","getJobStatusUrl":"'$CLOUD_RUN_SERVICE_GET_URL'"}'
# "inputRecordsSqlLimitClause":"LIMIT 10"
```

## Scheduler

```bash

gcloud iam service-accounts create ${SCHEDULER}-sa
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SCHEDULER}-sa@$PROJECT_ID.iam.gserviceaccount.com"  --role="roles/workflows.invoker"

# gcloud scheduler jobs delete ${SCHEDULER} --location="$REGION" --quiet
python3 -c "import json
output={
    'storageBucket':'$GCS_BUCKET',
    'jobExecutionSpannerInstance':'$SPANNER_INSTANCE',
    'jobExecutionSpannerDatabase':'$SPANNER_DATABASE',
    'inputRecordsSqlLimitClause':'',
    'getJobStatusUrl':'$CLOUD_RUN_SERVICE_GET_URL'
    }
print(json.dumps({'argument':json.dumps(output)}))
" | gcloud scheduler jobs create http ${SCHEDULER} \
    --location="$REGION" \
    --schedule='0 6 * * *' \
    --time-zone="America/New_York" \
    --uri="https://workflowexecutions.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/workflows/${WORKFLOW}/executions" \
    --message-body-from-file=/dev/stdin \
    --oauth-service-account-email="${SCHEDULER}-sa@${PROJECT_ID}.iam.gserviceaccount.com"
    
gcloud scheduler jobs run ${SCHEDULER} --location=$REGION

```
