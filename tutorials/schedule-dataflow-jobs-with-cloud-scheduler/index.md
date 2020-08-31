---
title: Schedule Dataflow batch jobs with Cloud Scheduler
description: Learn how to set up Cloud Scheduler to trigger your Dataflow batch jobs.
author: zhongchen
tags: Cloud Dataflow, Cloud Scheduler 
date_published: 2020-08-31
---

In this tutorial, you learn how to set up a [Cloud Scheduler](https://cloud.google.com/scheduler/) job to trigger to your 
Dataflow batch jobs.

Here is a high-level architecture diagram:

![diagram](https://storage.googleapis.com/gcp-community/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/scheduler-dataflow-diagram.png) 

You can find the code for this tutorial
[here](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/scheduler-dataflow-demo).

- It's feasible to trigger a Dataflow batch job directly from Cloud Scheduler. It's easy and fast. There's no need to use Cloud Functions for that.
- Cloud Scheduler jobs need to be created in the same region of App engine. In your [Terraform script](https://www.terraform.io/docs/providers/google/r/cloud_scheduler_job.html#region), 
be sure to assign the right value for the region field. You need to use **us-central1** if your App Engine lives in **us-central**.
- Use the [regional endpoint](https://cloud.google.com/dataflow/docs/reference/rest/v1b3/projects.locations.jobs/create) to specify the region of the Dataflow 
job. If you don't explicitly set the location in the request, the jobs will be created in the default region (US-central).

[Cloud Dataflow](https://cloud.google.com/dataflow) is a managed service for handling 
both streaming and batch jobs. For your streaming jobs, you just need to launch them once, and you don't need to worry about operating them afterwards. 
However, for your batch jobs, you probably need to trigger them based on certain conditions.

First, to be able to run your Dataflow jobs on a regular basis, you need to build your Dataflow templates. 
Follow the [instructions](https://cloud.google.com/dataflow/docs/guides/templates/creating-templates) to create your templates and save them in a 
Cloud Storage bucket.

![Upload Dataflow templates in a Cloud Storage bucket](https://storage.googleapis.com/gcp-community/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/store_a_template_in_gcs.png)

When you have your templates ready, you can set up Cloud Schedulers to trigger Dataflow templates. 

Here is one example to define a Cloud Scheduler job using Terraform:

```hcl-terraform
resource "google_cloud_scheduler_job" "scheduler" {
  name = "scheduler-demo"
  schedule = "0 0 * * *"
  # This needs to be us-central1 even if the app engine is in us-central.
  # You will get a resource not found error if just using us-central.
  region = "us-central1"

  http_target {
    http_method = "POST"
    uri = "https://dataflow.googleapis.com/v1b3/projects/${var.project_id}/locations/${var.region}/templates:launch?gcsPath=gs://${var.bucket}/templates/dataflow-demo-template"
    oauth_token {
      service_account_email = google_service_account.cloud-scheduler-demo.email
    }

    # need to encode the string
    body = base64encode(<<-EOT
    {
      "jobName": "test-cloud-scheduler",
      "parameters": {
        "region": "${var.region}",
        "autoscalingAlgorithm": "THROUGHPUT_BASED",
      },
      "environment": {
        "maxWorkers": "10",
        "tempLocation": "gs://${var.bucket}/temp",
        "zone": "${var.region}-a"
      }
    }
EOT
    )
  }
}
```

## Instructions

You can use these step-by-step instructions to create a sample Dataflow pipeline with Cloud Build.

1.  Open Cloud Shell and clone the repository.

        git clone https://github.com/GoogleCloudPlatform/community
        cd community/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/scheduler-dataflow-demo/

1.  Create a bucket in Cloud Storage, which will be used to store terraform states and Dataflow templates.
    Replace BUCKET with your own choice. ${GOOGLE_CLOUD_PROJECT} is predefined in Cloud Shell for the project ID.
    You can skip this step if you already have one GCS bucket created.

        export BUCKET=[BUCKET]
        gsutil mb -p ${GOOGLE_CLOUD_PROJECT} gs://${BUCKET}

1.  Create a backend for Terraform to store the states of Google Cloud resources.

        cd terraform
        cat > backend.tf << EOF
        terraform {
         backend "gcs" {
           bucket  = "${BUCKET}"
           prefix  = "terraform/state"
         }
        }
        EOF

1.  Follow the [instructions](https://cloud.google.com/scheduler/docs/quickstart) to create an App Engine app, which is needed to
    set up Cloud Scheduler jobs.

    Cloud Scheduler jobs need to be created in the same region as the App engine app. 
    
1.  Set the region:

        export REGION=us-central1

    You need to set the region to be *us-central1* even when the region shows as
    *us-central* on the UI.

    ![App Engine location](https://storage.googleapis.com/gcp-community/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/app_engine_location.png)


1.  Follow the [instructions](https://cloud.google.com/cloud-build/docs/securing-builds/configure-access-for-cloud-build-service-account#granting_a_role_using_the_iam_page) 
    to give the Cloud Build service account the following roles:

    - Cloud Scheduler Admin
    - Service Account Admin 
    - Service Account User
    - Project IAM Admin

     Verify that all the roles are enabled in the UI.

    ![Cloud Build_status](https://storage.googleapis.com/gcp-community/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/cloudbuild_sa_setup.png)

1.  Submit a Cloud Build job to create the resources:

        cd ..
        gcloud builds submit --config=cloudbuild.yaml \
          --substitutions=_BUCKET=${BUCKET},_REGION=${REGION},_PROJECT_ID=${GOOGLE_CLOUD_PROJECT} .

    The job will run based on the schedule you defined in the Terraform script. 

You can manually run the Cloud Schedule job by using the Cloud Console interface and watch it trigger your Dataflow batch job. 

You can check the status of jobs in the Cloud Console.

![See the status of your jobs](https://storage.googleapis.com/gcp-community/tutorials/schedule-dataflow-jobs-with-cloud-scheduler/check_scheduler_status.png)

## Cleaning up

Since this tutorial uses multiple Google Cloud components, please be sure to delete the associated resources once you are done.
