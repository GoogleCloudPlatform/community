# The Google Cloud project to use for this tutorial
export PROJECT_ID="your-project-id"

# The Compute Engine region to use for running Dataflow jobs and create a temporary storage bucket
export REGION_ID=us-central1

# define the bucket ID
export TEMP_GCS_BUCKET=all_bq_dlp_dc_sync

# define the pipeline name
export PIPELINE_NAME=all_bq_dlp_dc_sync

# define the pipeline folder
export PIPELINE_FOLDER=gs://${TEMP_GCS_BUCKET}/dataflow/pipelines/${PIPELINE_NAME}

# Set Dataflow number of workers
export NUM_WORKERS=5

# DLP execution name
export DLP_RUN_NAME=all-bq-dlp-dc-sync

# Set the DLP Inspect Template suffix
export INSPECT_TEMPLATE_SUFFIX=dlp_default_inspection

# Set the DLP Inspect Template name
export INSPECT_TEMPLATE_NAME=projects/${PROJECT_ID}/inspectTemplates/${INSPECT_TEMPLATE_SUFFIX}

# name of the service account to use (not the email address)
export ALL_BQ_DLP_DATAFLOW_SERVICE_ACCOUNT="all-bq-dlp-dataflow-sa"
export ALL_BQ_DLP_DATAFLOW_SERVICE_ACCOUNT_EMAIL="${ALL_BQ_DLP_DATAFLOW_SERVICE_ACCOUNT}@$(echo $PROJECT_ID | awk -F':' '{print $2"."$1}' | sed 's/^\.//').iam.gserviceaccount.com"