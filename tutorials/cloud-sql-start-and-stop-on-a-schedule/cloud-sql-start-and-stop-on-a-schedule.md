# Start and Stop Cloud SQL Instances on a Schedule using Cloud Workflows

This guide shows how to automatically start and stop Cloud SQL instances based on a schedule.  This is achieved using Cloud Scheduler -> Cloud Workflows -> Cloud SQL Admin API. 

This can be useful for cost optimization on development or testing Cloud SQL instances, or for any instances that don't need to run 24x7.

To complete this tutorial, you need IAM permissions at the project level (creating Service Accounts, adding IAM Policies, administering Cloud SQL, Cloud Scheduler and Cloud Workflows). This tutorial requires a basic understanding of using shell commands.

## Costs

The mechanism in this tutorial uses the following billable components of Google Cloud:

* [Cloud SQL](https://cloud.google.com/sql/pricing)
* [Cloud Workflows](https://cloud.google.com/workflows/pricing)
* [Cloud Scheduler](https://cloud.google.com/scheduler/pricing)

## Before you begin

To host the resources in this tutorial, you must set up a Google Cloud project with billing enabled. This tutorial uses Cloud Shell to run shell commands.

1. Use the Cloud Console to [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project) to host the Cloud SQL, Cloud Workflows and Cloud Scheduler resources in this tutorial. Choose a billing account to enable billing for the project. Note the project ID; you use it in a later step.

1. In the Cloud Console, [activate Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell#launching_from_the_console).

1. This tutorial also assumes that you already have a Cloud SQL instance that you can experiment with.  If not, you can follow [this guide](https://cloud.google.com/sql/docs/postgres/create-instance) to create an instance with one of the supported database engines on Cloud SQL.

1. The steps in this tutorial will stop your Cloud SQL instance.  Please make sure that you are using an appropriate environment when following this tutorial, and no end users will be impacted while experimenting with these steps.

## Set the variables

These are the variables to be used for the commands throughout the lab. If your Cloud Shell session is disconnected for any reason, you can safely re-run these variable assignments, and resume from where you have left off.

```bash

# Get the current project id
PROJECT_ID=$(gcloud config get-value project)
echo PROJECT_ID=$PROJECT_ID

# Region for Cloud Workflows / Cloud Scheduler
# this does not need to be the same as the region/zone of your Cloud SQL instances
REGION="us-central1"

# Names of the Cloud Workflows and Cloud Scheduler job definitions
WORKFLOW="cloud-sql-ops"
SCHEDULER="${WORKFLOW}-scheduler"

```

## Define the variable pointing to your Cloud SQL instance for experimentation

This is your existing Cloud SQL Instance that will be used throughout this tutorial, meaning that this Cloud SQL instance will be stopped and started on a schedule.

If you don't have an instance yet, follow [this guide](https://cloud.google.com/sql/docs/postgres/create-instance) to create an instance.

```bash
CLOUD_SQL_INSTANCE="my-instance-01"

```

## Set up the project

Enable the APIs required for Cloud SQL Admin, Cloud Workflows and Cloud Scheduler.

```bash
# enable APIs
gcloud services enable sqladmin.googleapis.com workflows.googleapis.com cloudscheduler.googleapis.com

```

## Create the workflow

You will first create a [user-managed service account](https://cloud.google.com/workflows/docs/authentication#deploy_a_workflow_with_a_custom_service_account) which will be used for Cloud Workflows.

```bash
gcloud iam service-accounts create ${WORKFLOW}-sa

gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/cloudsql.admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com"  --role="roles/logging.logWriter"

```

Under this repository, you can find the [Cloud Workflows YAML](start-stop-cloud-sql-instance.yaml) referenced in the command below.  This is a shared Cloud Workflows YAML file that will be used for both starting and stopping Cloud SQL Instances.

You can use the following snippet to create the `start-stop-cloud-sql-instance.yaml` in your current directory in Cloud Shell.

```bash
cat > start-stop-cloud-sql-instance.yaml <<'EOF'
main:
  params: [input]
  steps:
    - init:
        assign:
          - projectId: ${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}
          - cloudSqlInstance: ${input.cloudSqlInstance}
          - activationPolicyMap:
              "START": "ALWAYS"
              "STOP": "NEVER"
          - activationPolicy: ${map.get(activationPolicyMap,input.action)}
    # https://cloud.google.com/workflows/docs/reference/googleapis/sqladmin/v1/instances/patch
    - startOrStopCloudSqlInstance:
        call: googleapis.sqladmin.v1.instances.patch
        args:
          project: ${projectId}
          instance: ${cloudSqlInstance}
          body:
            settings:
              activationPolicy: ${activationPolicy}
EOF

```

Then, use the following command to deploy the workflow.

```bash
gcloud workflows deploy $WORKFLOW --location=$REGION --source="start-stop-cloud-sql-instance.yaml" --service-account=${WORKFLOW}-sa@$PROJECT_ID.iam.gserviceaccount.com

```

At this point, you can already manually invoke the workflow for testing.  

```bash
# To manually stop your instance via Cloud Workflows
gcloud workflows run $WORKFLOW --location=$REGION --data='{"cloudSqlInstance":"'$CLOUD_SQL_INSTANCE'","action":"STOP"}'

# To manually start your instance via Cloud Workflows
gcloud workflows run $WORKFLOW --location=$REGION --data='{"cloudSqlInstance":"'$CLOUD_SQL_INSTANCE'","action":"START"}'

```

You can go to the [Cloud SQL UI](https://console.cloud.google.com/sql/instances) and confirm your instance can be started or stopped via Cloud Workflows.  These operations may take a few minutes just like the behavior when doing it via Cloud SQL directly.

You can find your Cloud Workflows execution details under the [Cloud Workflows UI](https://console.cloud.google.com/workflows).

## Create the Cloud Scheduler Job

You will first create a [user-managed service account](https://cloud.google.com/scheduler/docs/http-target-auth#set_up_the_service_account) which will be used for your Cloud Scheduler job.

```bash
gcloud iam service-accounts create ${SCHEDULER}-sa
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SCHEDULER}-sa@$PROJECT_ID.iam.gserviceaccount.com"  --role="roles/workflows.invoker"

```

Then you can create the Cloud Scheduler Jobs.  In the examples below,

* one job is for starting the instance (9am New York time) from Monday to Friday)
* one job is for stopping the instance (5pm New York time from Monday to Friday)

These commands use Python3's [json module](https://docs.python.org/3/library/json.html) to format and escape the JSON messages conveniently for Cloud Scheduler API.  Python is not a requirement for Cloud Scheduler or Cloud Workflows as long as the JSON messages can be formatted properly.  You can see how they should be escaped from [another tutorial](https://cloud.google.com/scheduler/docs/tut-workflows#schedule_workflow) on the Cloud Scheduler documentation.

```bash
# Cloud Scheduler Job for starting a Cloud SQL instance at 9am New York time from every Monday to Friday
python3 -c "import json
message_body={
    'cloudSqlInstance':'$CLOUD_SQL_INSTANCE',
    'action':'START',
    }
print(json.dumps({'argument':json.dumps(message_body)}))
" | gcloud scheduler jobs create http ${SCHEDULER}-start \
    --location="$REGION" \
    --schedule='0 9 * * 1-5' \
    --time-zone="America/New_York" \
    --uri="https://workflowexecutions.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/workflows/${WORKFLOW}/executions" \
    --message-body-from-file=/dev/stdin \
    --oauth-service-account-email="${SCHEDULER}-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# You can delete your scheduler job using this
# gcloud scheduler jobs delete ${SCHEDULER}-start --location="$REGION" --quiet


# Cloud Scheduler Job for stopping a Cloud SQL instance at 5pm New York time from every Monday to Friday
python3 -c "import json
message_body={
    'cloudSqlInstance':'$CLOUD_SQL_INSTANCE',
    'action':'STOP',
    }
print(json.dumps({'argument':json.dumps(message_body)}))
" | gcloud scheduler jobs create http ${SCHEDULER}-stop \
    --location="$REGION" \
    --schedule='0 17 * * 1-5' \
    --time-zone="America/New_York" \
    --uri="https://workflowexecutions.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/workflows/${WORKFLOW}/executions" \
    --message-body-from-file=/dev/stdin \
    --oauth-service-account-email="${SCHEDULER}-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# You can delete your scheduler job using this
# gcloud scheduler jobs delete ${SCHEDULER}-stop --location="$REGION" --quiet
    
```

## Test the Cloud Scheduler jobs manually

At this point, you have two Cloud Scheduler jobs (start, stop), pointing to one shared Workflow definition for starting and stopping instances on a schedule.

You can go to the [Cloue Scheduler UI](https://console.cloud.google.com/cloudscheduler) and run the jobs for testing.  Alternatively you can also run the Cloud Scheduler jobs via command line.

```bash
gcloud scheduler jobs run ${SCHEDULER}-start --location=$REGION

gcloud scheduler jobs run ${SCHEDULER}-stop --location=$REGION

```

## Observe the outcome based on the schedule

Once the above tests are successful, you can observe how the Cloud SQL instances are started and stopped based on the schedule. The [Cloud SQL UI](https://console.cloud.google.com/sql/instances) can be used for verification of the instance states.

Congratulations! You have completed this tutorial and have created jobs that can start and stop Cloud SQL instances on a schedule.

## Delete the resources

You can delete the resources created during this tutorial.

* [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler)
* [Cloud Workflows](https://console.cloud.google.com/workflows)
* [IAM Policies granted to the Service Accounts](https://console.cloud.google.com/iam-admin/iam)
* [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)

Finally, if you have created a Cloud SQL instance for this tutorial, you can also delete it by following [this page](https://cloud.google.com/sql/docs/postgres/delete-instance).
