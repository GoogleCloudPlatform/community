---
title: Use Cloud Scheduler to invoke private Cloud Functions with OIDC
description: Learn how to use OpenID Connect to invoke private Cloud Functions periodically with Cloud Scheduler, with no Pub/Sub required.
author: glasnt,dinagraves
tags: Python 
date_published: 2020-08-07
---

Katie McLaughlin | Developer Advocate | Google<br>
Dina Graves | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to use Cloud Scheduler to invoke a private Cloud Function using HTTP targets and triggers and OIDC authentication.

Invoking a Cloud Function with authenticated HTTP that then performs an action is a common use case for Cloud Functions. Using Cloud Scheduler to schedule these 
invocations is a common use case for Cloud Scheduler. 

To use Cloud Pub/Sub as an intermediary, see the [Using Pub/Sub to trigger a Cloud Function tutorial](https://cloud.google.com/scheduler/docs/tut-pub-sub).  

## Objectives

In this tutorial, you do the following:

*   Create a service account with limited access.
*   Create a Cloud Function that triggers on HTTP.
*   Create a Cloud Scheduler job that targets an HTTP endpoint.
*   Run the Cloud Scheduler job. 
*   Verify success of the job.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Functions](https://cloud.google.com/functions)
*   [Cloud Build](https://cloud.google.com/build)
*   [Cloud Scheduler](https://cloud.google.com/scheduler)

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

You can run the commands in this tutorial in [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell) or with a
[local installation of gcloud](https://cloud.google.com/sdk/docs). 

We recommend that you create a new Google Cloud project for this tutorial, so that all created resources can be easily deleted when the tutorial is complete.

1.  In the Cloud console, on the project selector page, create a Cloud project. For details,
    see [Create a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).
1.  Make sure that billing is enabled for your project. For details, see [Confirm billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project#confirm_billing_is_enabled_on_a_project).

1.  Enable the Cloud Build, Cloud Scheduler, and Cloud Functions APIs:

    - [Enable the APIs in the Cloud console.](https://console.cloud.google.com/flows/enableapi?apiid=cloudbuild.googleapis.com,cloudscheduler.googleapis.com,cloudfunctions.googleapis.com)
    - Enable the APIs from the command line:

          gcloud services enable \
            cloudbuild.googleapis.com \
            cloudscheduler.googleapis.com \
            cloudfunctions.googleapis.com

## Get the source code

The function used in this tutorial prints `Hello, world` in the function logs and returns a formatted message.

This function is called from many different sources, so to ensure that every type of invocation is handled, this example uses the
[Flask `get_data()` method](https://flask.palletsprojects.com/en/1.1.x/api/?highlight=get_data#flask.Request.get_data), decoding the data payload manually. If the 
data is valid JSON, the function returns a message using the value of the name given. If it is not available, it will default to `World`. If the payload is 
invalid, an error is returned.

**main.py**:

```python
import json

def hello_world(request):
    request = request.get_data()
    try: 
        request_json = json.loads(request.decode())
    except ValueError as e:
        print(f"Error decoding JSON: {e}")
        return "JSON Error", 400
    name = request_json.get("name") or "World"
    msg = f'Hello, {name}!'
    print(msg)
    return msg
```


This example shows the Cloud Scheduler and Cloud Functions concepts in a simple proof of concept, but this architecture can be extended for more complex use 
cases, such as the following: 

*   [Sending Slack notifications ](https://github.com/GoogleCloudPlatform/python-docs-samples/blob/62971f4b6263b42912a66be4ecb95800d8f7c78b/functions/billing/main.py#L54)
*   [Performing BigQuery batch processes](https://github.com/GoogleCloudPlatform/python-docs-samples/blob/6879d73123135459fa45a36211505d1ead37978a/bigquery/cloud-client/simple_app.py#L24)
*   [Running AutoML jobs](https://github.com/GoogleCloudPlatform/python-docs-samples/blob/899cee82641d9ea6b97a7813283585ece2f8923d/automl/cloud-client/batch_predict.py)
*   [Running nightly tests](https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/functions/helloworld/sample_storage_test.py)
*   [Cleaning up Cloud Storage buckets](https://github.com/googleapis/python-storage/blob/main/samples/snippets/storage_delete_file.py)


## Test the function locally

This function can be tested on your local machine by using the [Functions Framework](https://github.com/GoogleCloudPlatform/functions-framework-python). 

1.  Install the Function Frameworks package on your machine:

        pip install functions-framework==3.0.0

1. Use Functions Framework to target the `hello_world` method in `main.py`: 

        functions-framework --target hello_world --debug

    The function will be made available at a local address ("Running on http://...").

1.  In a new terminal, use `curl` to send POST data to test the function: 

        curl -d '{"name": "local function"}' http://0.0.0.0:8080

    You should get the following result: 

        Hello, local function!

    The terminal running the Functions Framework will show the logs for the invocation:

        * Serving Flask app "hello_world" (lazy loading)
        * Environment: production
        * Debug mode: on
        * Running on http://x.x.x.x:8080/ (Press CTRL+C to quit)
        * Restarting with fsevents reloader
        * Debugger is active!
        Hello, local function!
        127.0.0.1 - - [00/Jan/2020 00:00:00] "POST / HTTP/1.1" 200 -

## Authentication architecture overview

To use a private Cloud Function, you need to send the request with sufficient authentication identification. Cloud Scheduler automates this for you by allowing 
you to specify multiple kinds of authentication headers. An OpenID Connect (OIDC) token is the most general way to provide this. By creating a service account 
that has only the ability to invoke functions, then assigning that as the identity of the function and as the OIDC service account, you can implement 
authentication scheduled invocation of your function.

See also:

*   [Authentication in Cloud Scheduler](https://cloud.google.com/scheduler/docs/http-target-auth#creating_a_scheduler_job_with_authentication)
*   [OpenID Connect (OIDC)](https://developers.google.com/identity/protocols/oauth2/openid-connect?_ga=2.188408680.1723942539.1591664285-164188851.1582751686)


## Deploying the example

To deploy the example, you create a dedicated service account to serve as the identity for the function and scheduler, create and test a Cloud Function, and 
create and test a Cloud Scheduler job.


### Create a service account

1.  [Create a service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating):

        gcloud iam service-accounts create myserviceaccount \
          --display-name "my service account"

1.  Assign the role to allow this service account to invoke Cloud Functions: 

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
          --member serviceAccount:myserviceaccount@${PROJECT_ID}.iam.gserviceaccount.com \
          --role roles/cloudfunctions.invoker

### Create a Cloud Function

Using the source code provided earlier, [deploy the Cloud Function](https://cloud.google.com/functions/docs/deploying/filesystem), ensuring that the previously 
created service account is [associated with this function](https://cloud.google.com/functions/docs/securing/function-identity#per-function_identity), and that 
unauthenticated access is disallowed:

    gcloud functions deploy hello_world \
      --trigger-http \
      --region us-central1 \
      --runtime python39 \
      --service-account myserviceaccount@${PROJECT_ID}.iam.gserviceaccount.com \
      --no-allow-unauthenticated

### Test the function

After the function is deployed, it can be tested. Since the request must be authenticated, the most straightforward way of testing this function
is in the Cloud console. 

1.  Go to the Cloud console and navigate to the [**Cloud Functions**](https://console.cloud.google.com/functions) page.
1.  Find the [`hello_world` function](https://console.cloud.google.com/functions/details/us-central1/hello_world), and click the
    [**Testing** tab](https://console.cloud.google.com/functions/details/us-central1/hello_world?tab=testing).
1.  In the **Triggering event** field, enter valid JSON that contains a name key and a value: 

        {"name": "testing event"}

1.  Click the **Test the function** button.

    The result should be `Hello, testing event!`.

![Successfully triggered a Cloud Run function in the Testing tab](https://storage.googleapis.com/gcp-community/tutorials/using-scheduler-invoke-private-functions-oidc/testing-cloud-functions.png)

You can also test this event in the console with `curl` by specifying the authorization header: 

    FUNCTION_URL=$(gcloud functions describe hello_world --format 'value(httpsTrigger.url)')
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
        $FUNCTION_URL \
        -d '{"name": "testing event"}'

### Create a scheduled job

[Create a scheduled job](https://cloud.google.com/scheduler/docs/creating#creating_jobs) to invoke the Cloud Function previously created, using the service
account that you created. 


1.  In the Cloud console, go to the [**Cloud Scheduler**](https://console.cloud.google.com/scheduler) page.
1.  Click **Schedule a job**.
1.  In the **Define the schedule** section, enter the following: 
    * **Name**: `my-hourly-job`
    * **Region**: `us-central1`
    * **Frequency**: `0 * * * *` (hourly)
    * **Timezone**: `Australia/Sydney` 
1.  Click **Continue**.
1.  In the **Configure the execution** section, enter the following:
    * **Target type**: `HTTP`
    * **URL**: the URL of the Cloud Function deployed earlier (`$FUNCTION_URL`)
    * **HTTP Method**: `POST`
    * **Body**:  `{"name": "Scheduler"}`
    * **Auth Header**: **Add OIDC token**
    * **Service account**: `my service account`
1.  Click **Continue**, and then click **Create**. 

Alternatively, you can run the following equivalent `gcloud` command: 

    gcloud scheduler jobs create http my-hourly-job \
      --location us-central1 \
      --schedule "0 * * * *" \
      --time-zone "Australia/Sydney" \
      --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/hello_world" \
      --http-method POST \
      --message-body '{"name": "Scheduler"}' \
      --oidc-service-account-email myserviceaccount@${PROJECT_ID}.iam.gserviceaccount.com

You can confirm that the job was created by checking the Cloud Scheduler section of the Cloud console, or by listing the active jobs: 

    gcloud scheduler jobs list

### Invoke a Cloud Function from a scheduled job

To test the configurations without having to wait for the next scheduled invocation, you can trigger the scheduled job by clicking **Run Now** on the
scheduled job listing in the Cloud console. You can also use the following command: 

    gcloud scheduler jobs run my-hourly-job

This command return no output of its own. 

## Check success

You can check the Cloud Functions logs on the
[**Cloud Logging**](https://console.cloud.google.com/logs/viewer?&resource=cloud_function%2Ffunction_name%2Fhello_world%2Fregion%2Fus-central1)
page in the Cloud console or with the following command: 

    gcloud functions logs read hello_world

You should see something similar to the following: 

    LEVEL  NAME         EXECUTION_ID  TIME_UTC                 LOG
    D      hello_world  rndmid64qasr  2020-00-00 00:00:00.000  Function execution started
    I      hello_world  rndmid64qasr  2020-00-00 00:00:00.000  Hello, Scheduler!
    D      hello_world  rndmid64qasr  2020-00-00 00:00:00.000  Function execution took 16 ms, finished with status code: 200

Checking the logs again each hour should show that the scheduled event occurred and successfully ran. 

## Clean up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, delete the project created specifically for this
tutorial. 

1. In the Cloud console, go to the **Manage resources** page.
1. In the project list, select the project that you want to delete, and then click **Delete**.
1. In the dialog, type the project ID, and then click **Shut down**.

## What's next

*   [Writing Cloud Functions](https://cloud.google.com/functions/docs/writing)
*   [Configuring scheduled jobs](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)
*   [Scheduler authentication with HTTP targets](https://cloud.google.com/scheduler/docs/http-target-auth)
