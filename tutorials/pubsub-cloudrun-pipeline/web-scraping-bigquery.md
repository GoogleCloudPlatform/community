# Web Scraping

Web scraping from a list of input IDs from a BigQuery table to another BigQuery table storing the results.

This takes around 20 min for straight copy-and-paste.

## Get the sample code and data

The sample code and data for this lab can be found on this GitHub repository. Use these commands to clone into your Cloud Shell environment.

```bash
git clone https://github.com/kylgoog/GoogleCloudPlatform-community.git
cd GoogleCloudPlatform-community/
git checkout pubsub-cloudrun-pipeline
cd tutorials/pubsub-cloudrun-pipeline/
 
```

The commands throughout the lab assume you will be staying in this directory.

## Assign variables

These are the variables to be used for the commands throughout the lab. If your Cloud Shell session is disconnected for any reason, you can safely re-run these variable assignments, and resume from where you have left off.

```bash

# Get the current project id
PROJECT_ID=$(gcloud config get-value project)
echo PROJECT_ID=$PROJECT_ID

# project number
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(project_number)")
echo PROJECT_NUMBER=$PROJECT_NUMBER

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

# Qwiklabs limits
CLOUD_RUN_SERVICE_LOAD_MAX_INSTANCES="1"
CLOUD_RUN_SERVICE_PROCESS_MAX_INSTANCES="10"
CLOUD_RUN_SERVICE_GET_MAX_INSTANCES="1"

BQ_DATASET="web_scraping"
BQ_INPUT_RECORDS_TABLE="input_records"
BQ_DATASET_REGION="us"
#BQ_JOB_EXECUTIONS_TABLE="job_executions"
BQ_OUTPUT_RECORDS_TABLE="output_records"
BQ_PUBSUB_ARCHIVE_DATASET="pubsub_archive"

# PubSub
export INPUT_RECORDS_PUBSUB_TOPIC="input-records-topic"
export OUTPUT_RECORDS_PUBSUB_TOPIC="output-records-topic"

# GCS
export GCS_BUCKET="${PROJECT_ID}-${REGION}"

WORKFLOW="web-scraping"
SCHEDULER="web-scraping-scheduler"

# URL pattern to be scraped.  The ID of each record will be substituted using Python's string format
export URL_PATTERN="https://get-product.endpoints.kyl-alto-ecommerce-site-358914.cloud.goog/product/{}"
  
# alternate architecture
CLOUD_RUN_JOB_SCRAPE="scrape-job"
JOB_SCHEDULER="web-scraping-job-scheduler"

# alternate architecture v2
CLOUD_RUN_SERVICE_LOAD_TASKS="load-records-to-cloudtasks"
BQ_REMOTE_FUNCTIONS_DATASET="remote_functions"
BQ_REMOTE_FUNCTIONS_REGION="US"
CLOUD_RUN_SERVICE_LOAD_TASKS_REMOTE_FUNCTION="load_records_to_cloudtasks"
CLOUD_RUN_SERVICE_LOAD_TASKS_REMOTE_FUNCTION_MAX_BATCHING_ROWS="1000"

# optional - for benchmarking only.  It can't go too concurrent
# CLOUD_RUN_SERVICE_PROCESS_REMOTE_FUNCTION="scrape"
# CLOUD_RUN_SERVICE_PROCESS_REMOTE_FUNCTION_MAX_BATCHING_ROWS="1"

```

## Set up the project

Enable the APIs, and create the repository for Cloud Run to deploy from source code.

```bash
# enable APIs
gcloud services enable workflows.googleapis.com spanner.googleapis.com pubsub.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com eventarc.googleapis.com cloudscheduler.googleapis.com

# create the Artifact Registry repository for Cloud Run to deploy from source code
gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker --location=$REGION
  
```

## Create PubSub topics and the archival tables

Define the PubSub Topic Schema for the output records.

```bash

# PubSub Output Records Schema - mostly string and integer fields
# TODO - BQ Subscription doesn't support Avro logical data types yet (e.g. timestamp, decimal)
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
 
```

## Create the PubSub topics and the corresponding archival tables.

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

done
 
# permissions for BQ subscription
# TODO It seems the pubsub service account is not created until there's an attempt to create a subscription
# As of now, if the pubsub service account doesn't exist yet, run the next block (creating the subscription), which would result in error, and then come back here and grant the permissions, and then create the subscriptions again
# create the Google-managed service account
gcloud beta services identity create --service="pubsub.googleapis.com"
# grant it the required permissions
# https://cloud.google.com/pubsub/docs/create-subscription#subscription
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com" --role="roles/bigquery.metadataViewer"

# create the BQ tables and subscription for archiving
for TOPIC in $INPUT_RECORDS_PUBSUB_TOPIC $OUTPUT_RECORDS_PUBSUB_TOPIC
do
    ARCHIVE_TABLE="${TOPIC//-/_}_archive"

    # gcloud pubsub subscriptions delete ${TOPIC}-archive
    gcloud pubsub subscriptions create ${TOPIC}-archive \
    --topic=$TOPIC \
    --bigquery-table=$PROJECT_ID:$BQ_PUBSUB_ARCHIVE_DATASET."$ARCHIVE_TABLE" \
    --write-metadata \
    --expiration-period="never"
done
 
 
```

## Create the BQ tables for input and output records

```bash

# create the BQ dataset and table for the input records
bq mk $BQ_DATASET

# load sample data
# bq rm -t -f $BQ_DATASET.$BQ_INPUT_RECORDS_TABLE
bq load --source_format=CSV -F "|" ${BQ_DATASET}.$BQ_INPUT_RECORDS_TABLE sample-data/input_records.txt "id"


# create the BQ table and subscription for the output records

# bq rm -t -f $BQ_DATASET.$BQ_OUTPUT_RECORDS_TABLE
# awaiting for fix on BQ float types
# bq mk --schema "
# subscription_name:string
# ,message_id:string
# ,publish_time:timestamp
# ,data:string
# ,attributes:string
# ,jobExecutionId:string
# ,scrapeDate:string
# ,scrapeTimestamp:string
# ,skuId:string
# ,sellerCount:integer
# ,mfgNumber:string
# ,productTitle:string
# ,bbWinner:string
# ,bbPrice:float
# ,shipCost:float
# ,siteChoice:string
# ,fba:string
# ,brand:string
# ,productUrl:string
# ,productCustomerReviews:integer
# ,productStarRating:float
# ,productDimensions:string
# ,itemWeight:string
# ,shipWeight:string
# ,itemNumber:string
# ,skuCreationDate:string
# ,returnsPolicy:string
# ,currentlyUnavailable:string
# ,r1Number:integer
# ,r1Cat:string
# ,r2Number:integer
# ,r2Cat:string
# ,r3Number:integer
# ,r3Cat:string
# ,r4Number:integer
# ,r4Cat:string
# " \
# -t \
# --clustering_fields message_id \
# --time_partitioning_field publish_time \
# --time_partitioning_type DAY \
# $BQ_DATASET."$BQ_OUTPUT_RECORDS_TABLE"
# #--time_partitioning_expiration 315619200 \

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
    --write-metadata \
    --expiration-period="never"

```

## Create the GCS bucket

```bash

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

## Create the job metadata table (Cloud Spanner)

```bash

gcloud spanner instances create $SPANNER_INSTANCE --config=regional-$REGION --description=$SPANNER_INSTANCE --processing-units="$SPANNER_PROCESSING_UNITS"
gcloud spanner databases create $SPANNER_DATABASE --instance=$SPANNER_INSTANCE

gcloud spanner databases ddl update $SPANNER_DATABASE --instance=$SPANNER_INSTANCE --ddl="${SPANNER_DDL_TRANSACTIONS}"

# Optional - create connection for federated query
gcloud services enable bigqueryconnection.googleapis.com
bq mk --connection \
  --connection_type='CLOUD_SPANNER' \
  --properties="{\"database\":\"projects/$PROJECT_ID/instances/$SPANNER_INSTANCE/databases/$SPANNER_DATABASE\"}" \
  --project_id=$PROJECT_ID \
  --location=us \
  "$SPANNER_BQ_CONNECTION"



```

## Deploy Cloud Run service - load-records-to-pubsub

```bash
# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_SERVICE_LOAD
source ~/.venv/$CLOUD_RUN_SERVICE_LOAD/bin/activate
pip install -r $CLOUD_RUN_SERVICE_LOAD/requirements.txt

# run this to test via browser
# gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app --chdir $CLOUD_RUN_SERVICE_LOAD --reload
# run this to test the individual function
python3 $CLOUD_RUN_SERVICE_LOAD/main.py "kyl-alto-web-scrape-359204-us-central1" "input-records/ed83c289-fd12-47ec-9006-792a31c981c3/000000000000.json"

gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_LOAD}-sa"

#gsutil iam ch serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-sa@$PROJECT_ID.iam.gserviceaccount.com:objectViewer gs://${GCS_BUCKET}
gsutil iam ch serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-sa@$PROJECT_ID.iam.gserviceaccount.com:admin gs://${GCS_BUCKET}

gcloud pubsub topics add-iam-policy-binding "${INPUT_RECORDS_PUBSUB_TOPIC}" --member "serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/pubsub.publisher --project ${PROJECT_ID}

# Cloud Run ingress can stay internal
PUBLISHING_SLEEP_TIME_BETWEEN_RECORDS="0"
gcloud run deploy $CLOUD_RUN_SERVICE_LOAD --source=$CLOUD_RUN_SERVICE_LOAD/ --platform managed --region $REGION --set-env-vars INPUT_RECORDS_PUBSUB_TOPIC="$INPUT_RECORDS_PUBSUB_TOPIC",PUBLISHING_SLEEP_TIME_BETWEEN_RECORDS="$PUBLISHING_SLEEP_TIME_BETWEEN_RECORDS" --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_LOAD}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --max-instances="$CLOUD_RUN_SERVICE_LOAD_MAX_INSTANCES" --timeout=3600
# --no-cpu-throttling

gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_LOAD}-trigger"
gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_LOAD} --region=$REGION \
  --member="serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-trigger@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/run.invoker'
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_LOAD}-trigger@${PROJECT_ID}.iam.gserviceaccount.com"  --role="roles/eventarc.eventReceiver"

# Note: Direct Events approach does not support path pattern
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

## Deploy Cloud Run service - scrape

```bash
# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_SERVICE_PROCESS
source ~/.venv/$CLOUD_RUN_SERVICE_PROCESS/bin/activate
pip install -r $CLOUD_RUN_SERVICE_PROCESS/requirements.txt

# run this to test via browser
# gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app --chdir $CLOUD_RUN_SERVICE_LOAD --reload
# run this to test the individual function
# python3 $CLOUD_RUN_SERVICE_PROCESS/main.py '{"id":"000003b7-4f08-4bc7-b286-9f68ed1df999","jobExecutionId":"d42dc9ce-f3d8-4fa2-966d-964c16efe572"}'


gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_PROCESS}-sa"
#gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/spanner.databaseUser"
#gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/storage.admin"

gcloud pubsub topics add-iam-policy-binding "${OUTPUT_RECORDS_PUBSUB_TOPIC}" --member "serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/pubsub.publisher --project ${PROJECT_ID}

# Cloud Run ingress can stay internal
# TODO Cloud Run ingress can stay internal after BQ Remote Functions and Cloud Tasks support it
gcloud beta run deploy $CLOUD_RUN_SERVICE_PROCESS --source=$CLOUD_RUN_SERVICE_PROCESS/ --platform managed --region $REGION --set-env-vars OUTPUT_RECORDS_PUBSUB_TOPIC="$OUTPUT_RECORDS_PUBSUB_TOPIC",URL_PATTERN="${URL_PATTERN}" --ingress="all" --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --max-instances="$CLOUD_RUN_SERVICE_PROCESS_MAX_INSTANCES" --concurrency=1 --max-instances=4000 --memory=256Mi --cpu=0.25 --execution-environment="gen1"
# Qwiklabs
# ERROR: (gcloud.beta.run.deploy) You may not have more than 32 total max instances in your project.
# gcloud beta run deploy $CLOUD_RUN_SERVICE_PROCESS --source=$CLOUD_RUN_SERVICE_PROCESS/ --platform managed --region $REGION --set-env-vars OUTPUT_RECORDS_PUBSUB_TOPIC="$OUTPUT_RECORDS_PUBSUB_TOPIC",URL_PATTERN="${URL_PATTERN}" --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_PROCESS}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --max-instances="$CLOUD_RUN_SERVICE_PROCESS_MAX_INSTANCES" --concurrency=1 --memory=256Mi --cpu=0.25 --execution-environment="gen1"
#--execution-environment="gen2" #gen2 min cpu is 1
# --no-cpu-throttling

# gcloud iam service-accounts delete "${CLOUD_RUN_SERVICE_PROCESS}-trigger"
gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_PROCESS}-trigger"
gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_PROCESS} --region=$REGION \
  --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS}-trigger@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/run.invoker'

# gcloud eventarc triggers delete ${CLOUD_RUN_SERVICE_PROCESS}-trigger --location=$REGION
gcloud eventarc triggers create ${CLOUD_RUN_SERVICE_PROCESS}-trigger \
     --location=$REGION \
     --destination-run-service=${CLOUD_RUN_SERVICE_PROCESS} \
     --destination-run-region=$REGION \
     --destination-run-path="/eventarc-handler" \
     --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
     --transport-topic="projects/$PROJECT_ID/topics/$INPUT_RECORDS_PUBSUB_TOPIC" \
     --service-account="${CLOUD_RUN_SERVICE_PROCESS}-trigger@${PROJECT_ID}.iam.gserviceaccount.com"

# update ackDeadline from the default 10 seconds 
gcloud pubsub subscriptions update $(gcloud eventarc triggers describe ${CLOUD_RUN_SERVICE_PROCESS}-trigger --location=$REGION --format="value(transport.pubsub.subscription)") --ack-deadline=60

# URL
CLOUD_RUN_SERVICE_PROCESS_URL=$(gcloud run services describe $CLOUD_RUN_SERVICE_PROCESS --region $REGION  --format="value(status.url)")
echo CLOUD_RUN_SERVICE_PROCESS_URL=$CLOUD_RUN_SERVICE_PROCESS_URL

# Optional - BQ Remote Functions

# # Create a CLOUD_RESOURCE connection
# bq mk --connection --display_name="$CLOUD_RUN_SERVICE_PROCESS" --connection_type=CLOUD_RESOURCE --project_id=${PROJECT_ID} --location="$BQ_REMOTE_FUNCTIONS_REGION" ${CLOUD_RUN_SERVICE_PROCESS}-connection

# # get the SA created by BQ
# CLOUD_RUN_SERVICE_PROCESS_CONNECTION_SA=$(bq show --format=json --location=$BQ_REMOTE_FUNCTIONS_REGION --connection ${CLOUD_RUN_SERVICE_PROCESS}-connection  | jq -r '.cloudResource.serviceAccountId')
# echo CLOUD_RUN_SERVICE_PROCESS_CONNECTION_SA=$CLOUD_RUN_SERVICE_PROCESS_CONNECTION_SA

# # grant the BQ Connection SA the Cloud Run Invoker
# gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_PROCESS} --region=$REGION --member="serviceAccount:${CLOUD_RUN_SERVICE_PROCESS_CONNECTION_SA}" --role='roles/run.invoker'

# # Remote function
# # The connection and the dataset regions have to match (single to single, multi to multi)
# bq mk --location $BQ_REMOTE_FUNCTIONS_REGION --force=true $BQ_REMOTE_FUNCTIONS_DATASET 
# # tested without specifying max_batching_rows and it was 2519 records per batch in my test (and the remaining records in the final batch)
# bq query --nouse_legacy_sql "CREATE OR REPLACE FUNCTION \`$PROJECT_ID\`.$BQ_REMOTE_FUNCTIONS_DATASET.$CLOUD_RUN_SERVICE_PROCESS_REMOTE_FUNCTION(x STRING) RETURNS STRING REMOTE WITH CONNECTION \`$PROJECT_ID.$BQ_REMOTE_FUNCTIONS_REGION.${CLOUD_RUN_SERVICE_PROCESS}-connection\` OPTIONS (endpoint = '${CLOUD_RUN_SERVICE_PROCESS_URL}', max_batching_rows = $CLOUD_RUN_SERVICE_PROCESS_REMOTE_FUNCTION_MAX_BATCHING_ROWS )"

# # BQ Remote Functions do not support any additional URL path on Cloud Functions / Cloud Run
# # "An endpoint with a custom domain, a URL query string or an additional URL path is not supported."

# # smoke test - 2 records
# bq query --nouse_legacy_sql "With t as (SELECT FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S', CURRENT_TIMESTAMP()) as jobExecutionId, id  FROM \`web_scraping.input_records\` LIMIT 2 ) select jobExecutionId,remote_functions.$CLOUD_RUN_SERVICE_PROCESS_REMOTE_FUNCTION(to_json_string(t)) from t"
# # smoke test - all records
# # Sep 30, 2022 test - this would take 950s for 47000 records
# bq query --nouse_legacy_sql "With t as (SELECT FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S', CURRENT_TIMESTAMP()) as jobExecutionId, id  FROM \`web_scraping.input_records\`) select jobExecutionId,remote_functions.$CLOUD_RUN_SERVICE_PROCESS_REMOTE_FUNCTION(to_json_string(t)) from t"

```

## Deploy Cloud Run service - get job status

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
gcloud run deploy $CLOUD_RUN_SERVICE_GET --source=$CLOUD_RUN_SERVICE_GET/ --platform managed --region $REGION  --ingress=internal --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_GET}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --max-instances="$CLOUD_RUN_SERVICE_GET_MAX_INSTANCES"
# --cpu-throttling 
#--execution-environment="gen2" #gen2 min cpu is 1
# --no-cpu-throttling

gcloud run services describe $CLOUD_RUN_SERVICE_GET --region $REGION 

CLOUD_RUN_SERVICE_GET_URL=$(gcloud run services describe $CLOUD_RUN_SERVICE_GET --region $REGION  --format="value(status.url)")
echo CLOUD_RUN_SERVICE_GET_URL=$CLOUD_RUN_SERVICE_GET_URL


```

## Create the workflow

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


# To manually run the workflow
# gcloud workflows run $WORKFLOW --location=$REGION --data='{"storageBucket":"'$GCS_BUCKET'","jobExecutionSpannerInstance":"'$SPANNER_INSTANCE'","jobExecutionSpannerDatabase":"'$SPANNER_DATABASE'","inputRecordsSqlLimitClause":"","getJobStatusUrl":"'$CLOUD_RUN_SERVICE_GET_URL'"}'
# "inputRecordsSqlLimitClause":"LIMIT 10"
```

## Create the Scheduler

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
    
```

## Run the scheduler job manually

```bash
    
gcloud scheduler jobs run ${SCHEDULER} --location=$REGION

```

## Optional - BQML Unsupervised Anomaly Detection - Training

Took 17min for 47k time series.

```bash

BQML_TRAINING_SQL='select skuId,scrapeDate,bbPrice
 from (select skuId,safe_cast(scrapeDate as date) scrapeDate, round(safe_cast(bbPrice as numeric),2) bbPrice,
row_number() OVER (partition by skuId,safe_cast(scrapeDate as date) order by safe_cast(scrapeTimestamp as timestamp) desc) as rn
 from `web_scraping.output_records`
) where rn=1 
and scrapeDate <=date_sub(current_date, interval 1 day)
and scrapeDate >=date_sub(current_date, interval 6 day)'

#DETECT_ANOMALY_SQL="SELECT * FROM ML.DETECT_ANOMALIES(MODEL `transactions.transaction_quantity_arima_plus_model`, STRUCT(0.99 AS anomaly_prob_threshold)) where is_anomaly=true;"

CREATE_MODEL_SQL="CREATE OR REPLACE MODEL ${BQ_DATASET}.bbPrice_arima_plus_model
OPTIONS(
  MODEL_TYPE='ARIMA_PLUS',
  TIME_SERIES_ID_COL='skuId',
  TIME_SERIES_TIMESTAMP_COL='scrapeDate',
  TIME_SERIES_DATA_COL='bbPrice',
  DATA_FREQUENCY='DAILY'
) AS
${BQML_TRAINING_SQL}"
#HOLIDAY_REGION='US' 

bq query --use_legacy_sql=false "$CREATE_MODEL_SQL"


```

## Check for anomalies

```SQL

-- modify a record in Spanner
SELECT
  *
FROM
  Products
order by skuid limit 1 offset 46999;

-- run job

-- On training data

SELECT skuId,scrapeDate
,bbPrice
,anomaly_probability
,is_anomaly
 FROM ML.DETECT_ANOMALIES(MODEL `web_scraping.bbPrice_arima_plus_model`, 
STRUCT(0.95 AS anomaly_prob_threshold)) 
where is_anomaly=true and skuId='00d6e4a3-859d-4417-8a9e-8e27576a55f7'
;

-- find anomalies from incoming data

WITH
  new_data AS (
SELECT skuId
,scrapeDate
,bbPrice
FROM 
(select * from (
SELECT skuId,safe_cast(scrapeDate as date) scrapeDate, safe_cast(bbPrice as numeric) bbPrice,row_number() OVER (partition by skuId,safe_cast(scrapeDate as date) order by safe_cast(scrapeTimestamp as timestamp) desc) as rn
FROM `web_scraping.output_records` 
) where rn=1 
--and skuId='050cff1b-8328-4b68-88b0-feeadfed625c'
and scrapeDate =current_date
) 
  )
SELECT skuId,
scrapeDate
,bbPrice
,anomaly_probability
,lower_bound
,upper_bound
,is_anomaly
 FROM ML.DETECT_ANOMALIES(MODEL `web_scraping.bbPrice_arima_plus_model`, 
STRUCT(0.90 AS anomaly_prob_threshold),(select * from new_data)) 
--order by skuId,scrapeDate
where is_anomaly=true and not (bbPrice = round(lower_bound,2) and bbPrice = round(upper_bound,2))
;


```

## Cloud Run Jobs approach

```bash
# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_JOB_SCRAPE
source ~/.venv/$CLOUD_RUN_JOB_SCRAPE/bin/activate
pip install -r $CLOUD_RUN_JOB_SCRAPE/requirements.txt


python3 $CLOUD_RUN_JOB_SCRAPE/main.py 


#gcloud builds submit ${CLOUD_RUN_JOB_SCRAPE}/ --pack image=gcr.io/$PROJECT_ID/${CLOUD_RUN_JOB_SCRAPE}
gcloud builds submit ${CLOUD_RUN_JOB_SCRAPE}/ --pack image=${REGION}-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/${CLOUD_RUN_JOB_SCRAPE}


gcloud iam service-accounts create "${CLOUD_RUN_JOB_SCRAPE}-sa"

gcloud pubsub topics add-iam-policy-binding "${OUTPUT_RECORDS_PUBSUB_TOPIC}" --member "serviceAccount:${CLOUD_RUN_JOB_SCRAPE}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role "roles/pubsub.publisher" --project ${PROJECT_ID}
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_JOB_SCRAPE}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.jobUser"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${CLOUD_RUN_JOB_SCRAPE}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor"


# gcloud beta run jobs delete ${CLOUD_RUN_JOB_SCRAPE} --region=$REGION
gcloud beta run jobs create ${CLOUD_RUN_JOB_SCRAPE} \
    --region=$REGION \
    --image="${REGION}-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/${CLOUD_RUN_JOB_SCRAPE}" \
    --service-account="${CLOUD_RUN_JOB_SCRAPE}-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --tasks="1000" \
    --set-env-vars OUTPUT_RECORDS_PUBSUB_TOPIC="$OUTPUT_RECORDS_PUBSUB_TOPIC",URL_PATTERN="${URL_PATTERN}" \
    --max-retries=5

gcloud beta run jobs execute ${CLOUD_RUN_JOB_SCRAPE} --region=$REGION

# Cloud Scheduler
gcloud iam service-accounts create ${JOB_SCHEDULER}-sa

gcloud beta run jobs add-iam-policy-binding ${CLOUD_RUN_JOB_SCRAPE} --region=$REGION \
  --member="serviceAccount:${JOB_SCHEDULER}-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/run.invoker'

# gcloud scheduler jobs delete ${JOB_SCHEDULER} --location="$REGION" --quiet
gcloud scheduler jobs create http $JOB_SCHEDULER \
  --location $REGION \
  --schedule='30 6 * * *' \
  --time-zone="America/New_York" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${CLOUD_RUN_JOB_SCRAPE}:run" \
  --http-method POST \
  --oauth-service-account-email="${JOB_SCHEDULER}-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud scheduler jobs run ${JOB_SCHEDULER} --location=$REGION

```

## Cloud Tasks approach

```bash

# Local Development
mkdir -p ~/.venv
virtualenv ~/.venv/$CLOUD_RUN_SERVICE_LOAD_TASKS
source ~/.venv/$CLOUD_RUN_SERVICE_LOAD_TASKS/bin/activate
pip install -r $CLOUD_RUN_SERVICE_LOAD_TASKS/requirements.txt

# run this to test via browser
# gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app --chdir $CLOUD_RUN_SERVICE_LOAD_TASKS --reload
# run this to test the individual function
python3 $CLOUD_RUN_SERVICE_LOAD_TASKS/main.py ""

{'requestId': 'fe780bc9-6004-41d7-8ab0-e04e83a48cef', 'caller': '//bigquery.googleapis.com/projects/kyl-alto-web-scrape-359204/jobs/bqjob_r76c39412f29600cc_000001838eda136b_1', 'sessionUser': 'alto@kayunlam.altostrat.com', 'calls': [['{"jobExecutionId":"2022-09-30 14:43:20.612498","id":"0089bb06-a330-48cd-acf5-728c0351e732"}'], ['{"jobExecutionId":"2022-09-30 14:43:20.612498","id":"00e187ef-2096-4609-b697-aa24b9bfa17f"}']]}


gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_LOAD_TASKS}-sa"

# TODO Cloud Run ingress can stay internal after BQ Remote Functions GA
gcloud beta run deploy $CLOUD_RUN_SERVICE_LOAD_TASKS --source=$CLOUD_RUN_SERVICE_LOAD_TASKS/ --platform managed --region $REGION --set-env-vars INPUT_RECORDS_PUBSUB_TOPIC="$INPUT_RECORDS_PUBSUB_TOPIC" --ingress="all" --no-allow-unauthenticated --service-account="${CLOUD_RUN_SERVICE_LOAD_TASKS}-sa@${PROJECT_ID}.iam.gserviceaccount.com"  --min-instances="$CLOUD_RUN_MIN_INSTANCES" --concurrency=1 --max-instances="4000" --memory=256Mi --cpu=0.25 --execution-environment="gen1" --timeout=3600
# --no-cpu-throttling

# URL
CLOUD_RUN_SERVICE_LOAD_TASKS_URL=$(gcloud run services describe $CLOUD_RUN_SERVICE_LOAD_TASKS --region $REGION  --format="value(status.url)")
echo CLOUD_RUN_SERVICE_LOAD_TASKS_URL=$CLOUD_RUN_SERVICE_LOAD_TASKS_URL

# Create a CLOUD_RESOURCE connection
bq mk --connection --display_name="$CLOUD_RUN_SERVICE_LOAD_TASKS" --connection_type=CLOUD_RESOURCE --project_id=${PROJECT_ID} --location="$BQ_REMOTE_FUNCTIONS_REGION" ${CLOUD_RUN_SERVICE_LOAD_TASKS}-connection

# get the SA created by BQ
CLOUD_RUN_SERVICE_LOAD_TASKS_CONNECTION_SA=$(bq show --format=json --location=$BQ_REMOTE_FUNCTIONS_REGION --connection ${CLOUD_RUN_SERVICE_LOAD_TASKS}-connection  | jq -r '.cloudResource.serviceAccountId')
echo CLOUD_RUN_SERVICE_LOAD_TASKS_CONNECTION_SA=$CLOUD_RUN_SERVICE_LOAD_TASKS_CONNECTION_SA

# grant the BQ Connection SA the Cloud Run Invoker
gcloud run services add-iam-policy-binding ${CLOUD_RUN_SERVICE_LOAD_TASKS} --region=$REGION --member="serviceAccount:${CLOUD_RUN_SERVICE_LOAD_TASKS_CONNECTION_SA}" --role='roles/run.invoker'


# Remote function
# The connection and the dataset regions have to match (single to single, multi to multi)
bq mk --location $BQ_REMOTE_FUNCTIONS_REGION --force=true $BQ_REMOTE_FUNCTIONS_DATASET 
# tested without specifying max_batching_rows and it was 2519 records per batch in my test (and the remaining records in the final batch)
bq query --nouse_legacy_sql "CREATE OR REPLACE FUNCTION \`$PROJECT_ID\`.$BQ_REMOTE_FUNCTIONS_DATASET.$CLOUD_RUN_SERVICE_LOAD_TASKS_REMOTE_FUNCTION(x STRING) RETURNS STRING REMOTE WITH CONNECTION \`$PROJECT_ID.$BQ_REMOTE_FUNCTIONS_REGION.${CLOUD_RUN_SERVICE_LOAD_TASKS}-connection\` OPTIONS (endpoint = '$CLOUD_RUN_SERVICE_LOAD_TASKS_URL', max_batching_rows = $BQ_REMOTE_FUNCTIONS_MAX_BATCHING_ROWS )"

# smoke test - all records
bq query --nouse_legacy_sql "With t as (SELECT FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S', CURRENT_TIMESTAMP()) as jobExecutionId, id  FROM \`web_scraping.input_records\`) select remote_functions.load_records_to_cloudtasks(to_json_string(t)) from t"
# smoke test - 2 records
bq query --nouse_legacy_sql "With t as (SELECT FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S', CURRENT_TIMESTAMP()) as jobExecutionId, id  FROM \`web_scraping.input_records\` LIMIT 2 ) select remote_functions.load_records_to_cloudtasks(to_json_string(t)) from t"
```
