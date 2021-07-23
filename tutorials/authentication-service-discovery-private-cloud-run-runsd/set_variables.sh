# The Google Cloud project ID to use for this tutorial.
# If you run this in Cloud Shell, you can use ${GOOGLE_CLOUD_PROJECT}
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}

# The project number of the Google Cloud project
PROJECT_NUMBER="$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format='get(projectNumber)')"

# The region where the resources for this tutorial are deployed
REGION=${REGION}

# Name of the Memorystore for Redis instance
REDIS_INSTANCE_ID=${REDIS_INSTANCE_ID}

# Name of the network where the resources are deployed
NETWORK=${NETWORK}

# Name of the the Serverless VPC connector
CONNECTOR_ID=${CONNECTOR_ID}

# Name of the Redis client deployed on Cloud Run
REDIS_CLIENT=${REDIS_CLIENT}

# Name of calling service deployed on Cloud Run
CALLER=${CALLER}

# Name of the calling service’s service account
CALLER_SA =${CALLER_SA}
