---
title: Creating a custom ML pipeline with Cloud Workflows and serverless services on GCP
description: Learn about using Cloud Workflows to create a custom ML pipeline.
author: enakai00
tags: Cloud Workflows, Cloud Run, Dataflow, AI Platform
date_published: 2021-xx-xx
---

Etsuji Nakai | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how you can use [Cloud Workflows](https://cloud.google.com/workflows) and other serverless services, such as [Cloud Run](https://cloud.google.com/run), to create a custom ML pipeline. The ML usecase is based on the [babyweight model example](https://github.com/GoogleCloudPlatform/training-data-analyst/blob/master/blogs/babyweight_keras/babyweight.ipynb). The following diagram shows the overall architecture of what you build in this tutorial.

<img src="https://github.com/enakai00/workflows-ml-pipeline-example/blob/main/docs/img/architecture.png" width="640px">

* You deploy two microservices on Cloud Run. One is to launch a Dataflow pipeline to preprocess the training data. The orignal data stored in BigQuery are coverted to CSV files and stored in Cloud Storage bucket. The other is to launch a ML training job on Cloud AI Platform, and deploy the trained model for predctions. The ML model files are cloned from the GitHub repository.

* You deploy a Cloud Workflows template to automate the whole process.

## Objectives

*   Deploy a microservice that launchs a Dataflow pipeline.
*   Deploy a microservice that launchs a ML training job on Cloud AI Platform and deploy the trained model for predictions.
*   Deploy a Cloud Workflows template to automate the whole process.
*   Execute a Cloud Workflows job.

## Costs

This tutorial uses billable components of Google Cloud, including:

* [Cloud Workflows](https://cloud.google.com/workflows)
* [Cloud Run](https://cloud.google.com/run)
* [Dataflow](https://cloud.google.com/dataflow)
* [AI Platform](https://cloud.google.com/ai-platform)
* [Cloud Build](https://cloud.google.com/cloud-build)
* [Cloud Storage](https://cloud.google.com/storage)

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage.

## Before you begin

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
2.  Enable billing for your project.
3.  Open the Cloud Shell terminal.
4.  Set your project ID, the GitHub repository URL and the directory path to the ML model in the environment variable. Replace `[your project id]` with your project ID.

    ```bash
    PROJECT_ID="[your project id]"
    GIT_REPO="https://github.com/enakai00/community"
    MODEL_PATH='tutorials/ml-pipeline-with-workflows/babyweight_model'
    ```

5. Set the project ID for cloud SDK.

    ```bash
    gcloud config set project $PROJECT_ID
    ```

6. Enable APIs.

    ```bash
    gcloud services enable run.googleapis.com
    gcloud services enable workflows.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable dataflow.googleapis.com
    gcloud services enable ml.googleapis.com
    ```

7. Set the storage bucket name in the environment variable, and create the bucket.

    ```bash
    BUCKET=gs://$PROJECT_ID-pipeline
    gsutil mb $BUCKET
    ```

8. Clone the repository.

    ```bash
    cd $HOME
    git clone $GIT_REPO
    ```

## Deploy microservices on Cloud Run.

1. Deploy a microservice to preprocess the training data.

```bash
cd $HOME/community/tutorials/ml-pipeline-with-workflows/services/preprocess
gcloud builds submit --tag gcr.io/$PROJECT_ID/preprocess-service
gcloud run deploy preprocess-service \
  --image gcr.io/$PROJECT_ID/preprocess-service \
  --platform=managed --region=us-central1 \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "PROJECT_ID=$PROJECT_ID"
```

2. Deploy a microservice to train and deploy the ML model.

```bash
cd $HOME/community/tutorials/ml-pipeline-with-workflows/services/train
gcloud builds submit --tag gcr.io/$PROJECT_ID/train-service
gcloud run deploy train-service \
  --image gcr.io/$PROJECT_ID/train-service \
  --platform=managed --region=us-central1 \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "PROJECT_ID=$PROJECT_ID,GIT_REPO=$GIT_REPO,BRANCH='master',MODEL_PATH=$MODEL_PATH"
```

3. Set service URLs in the environment variable.

```bash
SERVICE_NAME="preprocess-service"
PREPROCESS_SERVICE_URL=$(gcloud run services list --platform managed \
    --format="table[no-heading](URL)" --filter="SERVICE:${SERVICE_NAME}")

SERVICE_NAME="train-service"
TRAIN_SERVICE_URL=$(gcloud run services list --platform managed \
    --format="table[no-heading](URL)" --filter="SERVICE:${SERVICE_NAME}")
```

## Test microservices

Before automating the whole process with Cloud Workflows, you test the microservices using the `curl` command.

### Preprocess the training data

The following command send an API request to launch a Dataflow pipeline to preprocess the training data. The option "limit" specifies the number of rows to extract from BigQuery. You specify a small number (1,000) for a testing purpose in this example.

```bash
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d "{\"limit\":\"1000\", \"outputDir\":\"$BUCKET/preproc\"}" \
  -s $PREPROCESS_SERVICE_URL/api/v1/preprocess | jq .
```

The output looks like:

```
{
  "jobId": "2020-12-13_23_57_52-4099585880410245609",
  "jobName": "preprocess-babyweight-054aeefe-16d2-4a26-a5c2-611a5ece1583",
  "outputDir": "gs://workflows-ml-pipeline-pipeline/preproc/054aeefe-16d2-4a26-a5c2-611a5ece1583"
}
```

The `jobId` shows the Job ID of the dataflow pipeline job, and the preprocessed data will be stored under `outputDir`. Copy the Job ID in `jobID` and the storage path in `outputDir` to set them in the environment variable.

```bash
OUTPUT_DIR="gs://workflows-ml-pipeline-pipeline/preproc/054aeefe-16d2-4a26-a5c2-611a5ece1583"
JOB_ID="2020-12-13_23_57_52-4099585880410245609"
```

The following command sends an API request to show the job status.

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -s $PREPROCESS_SERVICE_URL/api/v1/job/$JOB_ID | jq .
```

The output looks like:

```
{
  "createTime": "2020-12-14T07:57:54.086857Z",
  "currentState": "JOB_STATE_RUNNING",
  "currentStateTime": "2020-12-14T07:57:59.416039Z",
...
}
```

Wait about 5 minutes until the `currentState` becomes `JOB_STATE_DONE`. You can also check the job status from the [Cloud Console](https://console.cloud.google.com/dataflow/jobs).

### Train the ML model

The following command sends an API request to launch an AI Platform job to train the ML model. The option `numTrainExamples`, `numEvalExamples` and `numEvals` specify the number of training examples, the number of evaluation examples and the number of evaluation during the training respectively. You specify small numbers for a testing purpose in this example.

```bash
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d "{\"jobDir\": \"$BUCKET/trained_model\", \"dataDir\": \"$OUTPUT_DIR\", \"numTrainExamples\": 5000, \"numEvalExamples\": 1000, \"numEvals\": 2}" \
  -s $TRAIN_SERVICE_URL/api/v1/train | jq .
```

The output looks like:

```
{
  "createTime": "2020-12-14T08:24:12Z",
  "etag": "zKM8N6bPpVk=",
  "jobId": "train_babyweight_e281aab4_5b4f_40cd_8fe3_f8290037b5fc",
  "state": "QUEUED",
...
    "jobDir": "gs://workflows-ml-pipeline-pipeline/trained_model/e281aab4-5b4f-40cd-8fe3-f8290037b5fc",
    "packageUris": [
      "gs://workflows-ml-pipeline-pipeline/trained_model/e281aab4-5b4f-40cd-8fe3-f8290037b5fc/trainer-0.0.0.tar.gz"
    ],
    "pythonModule": "trainer.task",
    "pythonVersion": "3.7",
    "region": "us-central1",
    "runtimeVersion": "2.2",
    "scaleTier": "BASIC_GPU"
  },
  "trainingOutput": {}
}
```

The `jobId` shows the Job ID of the training job, and the trained model will be stored under `jobDir`. Copy the Job ID in `jobID` and the storage path in `jobDir` to set them in the environment variable.

```bash
JOB_ID="train_babyweight_e281aab4_5b4f_40cd_8fe3_f8290037b5fc"
JOB_DIR="gs://workflows-ml-pipeline-pipeline/trained_model/e281aab4-5b4f-40cd-8fe3-f8290037b5fc"
```

The following command sends an API request to show the job status.

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -s $TRAIN_SERVICE_URL/api/v1/job/$JOB_ID | jq .
```

The output looks like:

```
{
  "createTime": "2020-12-14T08:24:12Z",
  "etag": "rW+uQQbA6bM=",
  "jobId": "train_babyweight_e281aab4_5b4f_40cd_8fe3_f8290037b5fc",
  "state": "PREPARING",
...
}
```

Wait about 10 minutes until the `state` becomes `SUCCEEDED`. You can also check the job status from the [Cloud Console](https://console.cloud.google.com/ai-platform/jobs).

### Deploy the trained model

The following command sends an API request to launch an AI Platform job to train the ML model. The option `modelName` and `versionName` specify the model name and the version name respectively.

```bash
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d "{\"modelName\": \"babyweight_model\", \"versionName\": \"v1\", \"deploymentUri\": \"$JOB_DIR/export\"}" \
 -s $TRAIN_SERVICE_URL/api/v1/deploy | jq .
```

The output looks like:

```
{
  "metadata": {
    "@type": "type.googleapis.com/google.cloud.ml.v1.OperationMetadata",
    "createTime": "2020-12-14T08:34:36Z",
    "modelName": "projects/workflows-ml-pipeline/models/babyweight_model",
    "operationType": "CREATE_VERSION",
    "version": {
      "createTime": "2020-12-14T08:34:35Z",
      "deploymentUri": "gs://workflows-ml-pipeline-pipeline/trained_model/e281aab4-5b4f-40cd-8fe3-f8290037b5fc/export",
      "etag": "BlXqEgx9VQg=",
      "framework": "TENSORFLOW",
      "machineType": "mls1-c1-m2",
      "name": "projects/workflows-ml-pipeline/models/babyweight_model/versions/v1",
      "pythonVersion": "3.7",
      "runtimeVersion": "2.2"
    }
  },
  "name": "projects/workflows-ml-pipeline/operations/create_babyweight_model_v1-1607934875576"
}
```

Run the following command to confirm that the model has been deployed.

```bash
gcloud ai-platform models list --region global
```

The output looks like:

```
Using endpoint [https://ml.googleapis.com/]
NAME              DEFAULT_VERSION_NAME
babyweight_model  v1
```

## Automate the whole process with Cloud Workflows

You use Cloud Workflows to automate the steps you have done in the previous section.

## Deploy the Cloud Workflows template

Run the following commands to create a service account and assing the role to invoke services on Cloud Run.

```bash
SERVICE_ACCOUNT_NAME="cloud-run-invoker"
SERVICE_ACCOUNT_EMAIL=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name "Cloud Run Invoker"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SERVICE_ACCOUNT_EMAIL \
  --role=roles/run.invoker
```

Run the following commands to deploy the workflow template. You associate the service account that you created in the previous step using the `--service-account` option.

```
cd cd $HOME/community/tutorials/ml-pipeline-with-workflows/workflows
cp ml_workflow.yaml.template ml_workflow.yaml
sed -i "s#PREPROCESS-SERVICE-URL#${PREPROCESS_SERVICE_URL}#" ml_workflow.yaml
sed -i "s#TRAIN-SERVICE-URL#${TRAIN_SERVICE_URL}#" ml_workflow.yaml
gcloud beta workflows deploy ml_workflow \
  --source=ml_workflow.yaml \
  --service-account=$SERVICE_ACCOUNT_EMAIL
```

Run the following command to execute a workflow job.

```bash
gcloud beta workflows execute ml_workflow \
  --data="{\"limit\": 1000, \"bucket\": \"$BUCKET\", \"numTrainExamples\": 5000, \"numEvals\": 2, \"numEvalExamples\": 1000, \"modelName\": \"babyweight_model\", \"versionName\": \"v2\"}"
```

You can monitor the status of the job from the [Cloud Console](https://pantheon.corp.google.com/workflows). When the job successfully completed, run the following command to confirm that the model has been deployed.

```bash
gcloud ai-platform versions list --model babyweight_model --region global
```

The output looks like:

```
Using endpoint [https://ml.googleapis.com/]
NAME  DEPLOYMENT_URI                                                                                 STATE
v1    gs://workflows-ml-pipeline-pipeline/trained_model/e281aab4-5b4f-40cd-8fe3-f8290037b5fc/export  READY
```

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Read the tutorial [Structured data prediction using Cloud AI Platform](https://github.com/GoogleCloudPlatform/training-data-analyst/tree/master/blogs/babyweight_keras) to learn the machine learning model you use in this example.
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
