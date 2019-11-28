---
title: Using Stackdriver Uptime Checks for Triggering Cloud Functions on a Schedule
description: Learn how to use Stackdriver uptime checks to trigger HTTP Cloud Functions at regular intervals.
author: sujoyg
tags: Stackdriver, Monitoring, Cloud Functions, cron
date_published: 2017-12-22
---

Important: This document was archived on 2 August 2019 because it was made obsolete by a newer tutorial: [Using Pub/Sub to trigger a Cloud Function](https://cloud.google.com/scheduler/docs/tut-pub-sub)

## Overview

This tutorial describes a method of triggering [Cloud Functions](https://cloud.google.com/functions/docs/)
at regular intervals using [Stackdriver uptime checks](https://cloud.google.com/monitoring/alerts/uptime-checks).

App Engine [Cron Service](https://cloud.google.com/appengine/docs/flexible/nodejs/scheduling-jobs-with-cron-yaml)
also allows you to schedule tasks at defined times or at regular intervals. You
can use Cron Service to deploy an App Engine service to trigger Cloud Functions
at the cost of writing, deploying, and managing an additional service.

If you don't require the additional flexibility afforded by App Engine Cron
Service, or don't want to deploy an additional service, Stackdriver uptime
checks offer a simple way to schedule and trigger Cloud Functions. While this
isn't an officially supported use of uptime checks, it's a valid solution for
specific use cases.

## Using uptime checks as Cloud Function triggers

Uptime checks are a [Stackdriver Monitoring](https://cloud.google.com/monitoring/docs/)
feature for monitoring the availability of a specified service. Uptime checks
work by making HTTP requests to a public URL associated with the monitored
service at regular intervals from locations around the world. The Uptime check
monitors the returned HTTP status code or response body.

You can trigger a Cloud Function in two ways, 1) in response to messages
published on a Cloud Pub/Sub topic, or 2) in response to an HTTP request. For
the latter, you deploy a function with an [HTTP trigger](https://cloud.google.com/functions/docs/calling/http),
which automatically generates a fully-qualified URL. You trigger the Cloud
Function by making a GET, POST, PUT, DELETE, or OPTIONS HTTP request to that
URL.

If you use the HTTP trigger URL as the target URL for a Stackdriver uptime
check, the associated Cloud Function triggers every time the check is performed
at configured intervals. This feature allows uptime checks to trigger scheduled
HTTP Cloud Functions.

Stackdriver strives to make uptime checks on schedule. Please refer to
[Google Stackdriver Service Level Agreement (SLA)](https://cloud.google.com/stackdriver/sla)
for more details about the SLA for Stackdriver services.

A naive implementation of uptime checks for scheduling has two major limitations:

* Scheduling a large number of Cloud Functions using one uptime check for each
  function can be cumbersome and resource intensive; you must create and
  maintain separate uptime checks for each one of them.
* By default, Stackdriver uptime checks are made from several regions around the
  world. You can select the regions, but you must include at least three. At
  every scheduling interval a request from each of these regions is made to the
  URL, triggering the Cloud Function several times per interval instead of once.

## Master Cloud Functions

You can address both of these limitations by creating a master Cloud Function
for each schedule that triggers all other Cloud Functions for that schedule. The
master Cloud Function reads a _trigger list_ file containing all the information
required to trigger the associated Cloud Functions. By using a master Cloud
Function, you only need to create and manage one uptime check and one master
Cloud Function for every schedule.

The master Cloud Function is triggered by Stackdriver uptime checks and
maintains a timestamp in a persistent database of when it last triggered the
scheduled Cloud Functions. Every time it's triggered, the master Cloud Function
checks the database to see if enough time has elapsed for it to trigger the
scheduled functions. If the answer is _yes_, the master Cloud Function updates
the timestamp and triggers all the scheduled functions.  If _no_, the functions
aren't triggered.

By using a master Cloud Function in combination with a persistent database,
Cloud Functions are executed at most once per interval regardless of the number
of uptime check locations in each scheduling interval.

This tutorial implements a trigger list, stored in Cloud Storage, and a master
Cloud Function that uses Cloud Datastore to keep track of the timestamp.

# Objectives

Deploy an HTTP Cloud Function triggered on a schedule by:

* Creating a trigger list in Cloud Storage containing instructions for
  triggering this function.
* Deploying a master Cloud Function which uses the trigger list to launch
  associated Cloud Functions.
* Creating a Stackdriver uptime check to kick off the master Cloud Function on a
  schedule.

# Costs

This tutorial uses billable components of Cloud Platform, including:

* Cloud Functions
* Cloud Storage
* Stackdriver Monitoring

You can use the [pricing calculator](https://cloud.google.com/products/calculator)
to estimate the costs for your projected usage. If you are a new Cloud Platform
user, you might be eligible for a [free trial](https://cloud.google.com/free-trial).

# Before you begin

1.  Select or create a Google Cloud Platform (GCP) project.

    [GO TO THE PROJECTS PAGE](https://console.cloud.google.com/project)

1.  Enable billing for your project.

    [ENABLE BILLING](https://support.google.com/cloud/answer/6293499#enable-billing)

1.  Install and initialize the [Cloud SDK](https://cloud.google.com/sdk/) on your workstation.

    [INSTALL CLOUD SDK](https://cloud.google.com/sdk/downloads)

    [INITIALIZE CLOUD SDK](https://cloud.google.com/sdk/docs/initializing)

1.  Update and install `gcloud` components.

        gcloud components update && gcloud components install beta

1.  Enable the Cloud Functions API.

        gcloud service-management enable cloudfunctions

1.  Prepare your environment for `Node.js` development.

    [GO TO THE SETUP GUIDE](https://cloud.google.com/nodejs/docs/setup)

1.  Activate Stackdriver Monitoring. Since uptime checks are part of Stackdriver
    Monitoring, you need to activate Stackdriver Monitoring before proceeding
    further.

    1.  In the Cloud Console, ensure that the project you have been using for
        this tutorial is the currently active project.

        [VIEW CLOUD CONSOLE](https://console.cloud.google.com/)

    1.  In the **Products and service** menu, under **Stackdriver**, click
        **Monitoring**. If this is your first time using Stackdriver, you will
        be prompted to link your GCP account to Stackdriver.

        [VIEW STACKDRIVER MONITORING](https://console.cloud.google.com/monitoring)

        After you sign in, you'll be prompted to link the currently active
        project to an existing Stackdriver account, which you just created.

# Configuring your environment

To configure your environment, follow these steps:

1.  Set the project as the default project.

    Many `gcloud` commands require specifying a project, and defining a default
    value saves you from having to do this every time. Replace **`[PROJECT]`**
    with the GCP project identifier that you want to use for this tutorial.

        gcloud config set core/project [PROJECT]

1.  Set up environment variables.

    In the following snippet, replace **`[STAGE_BUCKET]`** with the name of the
    bucket you'll use for staging Cloud Functions during deployment. Replace
    **`[CRON_BUCKET]`** with the name of the bucket you'll use to store the
    trigger list. For both, omit the `gs://` prefix. The buckets do not need to
    exist before defining them as environment variables. The following command
    uses the currently active project set in Step 1 to define the environment
    variable.

        export PROJECT=$(gcloud config get-value core/project)
        export STAGE_BUCKET=[STAGE_BUCKET]
        export CRON_BUCKET=[CRON_BUCKET]

# Creating buckets

Create two buckets for staging Cloud Functions and storing the trigger list.
Run the following commands:

    gsutil mb gs://${STAGE_BUCKET}
    gsutil mb gs://${CRON_BUCKET}

These commands fail if a bucket with the same name already exists on GCP. In
this case you must choose a name that's not already in use.

# Writing a target Cloud Function

1.  Create a directory on your local workstation for the Cloud Function code:

        mkdir ~/gcf_cron_target

    Next, move into the directory:

        cd ~/gcf_cron_target

1.  A `Node.js`-based Cloud Function is expected to be a `Node.js` module loaded
    with a `require()` call. You'll define a `Node.js` module and export its
    entry point into an `index.js` file to implement the Cloud Function.

    Create the `index.js` file in the `gcf_cron_target` directory with the following contents:

        /**
        * HTTP Cloud Function.
        *
        * @param {Object} req Cloud Function request context.
        * @param {Object} res Cloud Function response context.
        */
        exports.cronTarget = function cronTarget(req, res) {
          switch (req.method) {
            case 'GET':
              handleGET(req, res);
              break;
            case 'POST':
              handlePOST(req, res);
              break;
            default:
              res.status(405).send('Method Not Allowed');
              break;
          }
        };

        function handleGET(req, res) {
          const now = (new Date()).toUTCString();
          console.log(`GET received at ${now}`);
          res.status(200).end();
        }

        function handlePOST(req, res) {
          const now = (new Date()).toUTCString();
          console.log(`POST received at ${now} with ${req.body.data}`);
          res.status(200).end();
        }

This function can be triggered using HTTP GET or POST requests. In each case, it
responds with a message showing the HTTP method used to trigger it, the time it
was triggered, and any data associated with POST requests. For all other HTTP
methods, the function returns a 405 HTTP status code.

After a successful execution, the function logs a message to the console with
the HTTP method and the timestamp of the request. These console logs appear in
the Cloud Function's logs and can be queried using the `gcloud` tool. They can
be used to verify whether the function was executed on schedule.

Because the function handles GET and POST requests differently you're able to
simulate different Cloud Functions for the trigger list simply by invoking it in
different ways.

# Deploying the function

1.  Run the following command to deploy the function:

        gcloud beta functions deploy cronTarget --stage-bucket ${STAGE_BUCKET} --trigger-http

    The `--trigger-http` option generates and assigns a URL endpoint to the
    function so that it can be triggered with an HTTP request to that endpoint.

    It might take a few minutes for the command to finish running. After
    deployment is finished, you'll see something like the following:

        ...
        Deploying function (may take a while - up to 2 minutes)...done.
        availableMemoryMb: 256
        entryPoint: cronTarget
        httpsTrigger:
          url: https://us-central1-your-project.cloudfunctions.net/cronTarget
        latestOperation: operations/Z2NmLXNlY3VyZS91cy1jZW50cmFsMS9zZWN1cmUvT0FYclM0N2ttRmc
        ...

    Note the URL. This is the URL that you'll use to trigger the Cloud Function.
    From this point on, the triggering URL is referred to as
    **`[TARGET_FUNCTION_URL]`**.

1.  Verify the status of the deployment by running the following command:

        gcloud beta functions describe cronTarget

    This command describes the configuration and current status of the named
    Cloud Function, in this case `cronTarget`.

    The command outputs something like the following:

        ...
        status: READY
        timeout: 60s
        ...

    A `READY` status indicates that the function has been successfully deployed
    and is ready to be invoked.

# Creating the trigger list

When the master Cloud Function is executed it invokes the Cloud Functions
specified by the trigger list. The trigger list contains a list of URLs
corresponding to target HTTP Cloud Functions and the information required to
trigger them, such as the HTTP method and any POST data.

The target functions are invoked serially in an asynchronous manner without
waiting for the previous one to complete. For all practical purposes, they are
essentially triggered at the same time.

Each master Cloud Function requires a trigger list. Since the master function is
implemented using `Node.js`, the trigger list is easier to process and maintain
if it's formatted as JSON.

1.  Create a directory on your local workstation for the trigger list. Later,
    you'll use the same directory for the master Cloud Function code.

        mkdir ~/gcf_cron_master

    Next, move into the directory:

        cd ~/gcf_cron_master

1.  Create a `trigger.json` file with the following contents, replacing
    **`[TARGET_FUNCTION_URL]`** with the target Cloud Function URL that you
    recorded in an earlier step:

        [
          {
            "method": "GET",
            "url": "[TARGET_FUNCTION_URL]"
          },
          {
            "method": "POST",
            "url": "[TARGET_FUNCTION_URL]",
            "body": {"data": "Hello, World"}
          }
        ]

    This example invokes the previously-created target Cloud Function twice
    using different HTTP methods, GET and POST, to simulate scheduling of
    multiple target functions from a single trigger list.

1.  Upload `trigger.json` to the Cloud Storage bucket you designated for this purpose

        gsutil cp trigger.json gs://${CRON_BUCKET}

# Writing the master Cloud Function

1.  Create a `package.json` file. The `package.json` file is used by
    [npm](https://en.wikipedia.org/wiki/Npm_(software)), the default package
    manager for `Node.js`, to install the JavaScript modules required by a
    `Node.js` application.

    The master Cloud Function uses the `@google-cloud/storage` module, a
    [Cloud Storage client library for Node.js](https://www.npmjs.com/package/@google-cloud/storage),
    to read the `trigger.json` file in your Cloud Storage bucket. Create a
    `package.json` file in the `gcf_cron_master` directory with the following
    contents:

        {
          "dependencies": {
            "@google-cloud/datastore": "1.1",
            "@google-cloud/storage": "1.2",
            "request": "2.81"
          }
        }

1.  Create an `index.js` file, which implements the function and exports its
    entry point in the `gcf_cron_master` directory.

## How does `index.js` work?

In this section the functions found in `index.js` are listed and explained.
These functions are:

* `cronMaster`
* `checkTimestamp`
* `readTriggerList`
* `runTriggerList`

### Understanding `cronMaster`

The `cronMaster` function is the Cloud Function entry point. This function and
all of its dependencies, which are explained in a later section, are part of
`index.js`. Make sure to replace **`[CRON_BUCKET]`** with the name of your
bucket.

    const Datastore = require('@google-cloud/datastore');
    const GCS = require('@google-cloud/storage');
    const Request = require('request');
    const BUCKET = '[CRON_BUCKET]'; // Replace with your bucket.
    const TRIGGER_LIST = 'trigger.json';

    /**
    * Cloud Function.
    *
    * @param {Object} req Cloud Function request context.
    * @param {Object} res Cloud Function response context.
    */
    exports.cronMaster = function cronMaster(req, res) {
      checkTimestamp()
        .then(() => readTriggerList())
        .then((triggerList) => runTriggerList(res, triggerList))
        .catch(() => res.status(200).end());
    };

The `cronMaster` function begins by calling the `checkTimestamp` helper function
to see if it's time to process the trigger list. If so, `cronMaster` calls the
`readTriggerList` helper function to parse the contents of the JSON-formatted
trigger list in Cloud Storage into a `triggerList` object. Finally, it passes
the `triggerList` object to the `runTriggerList` helper function to trigger the
scheduled Cloud Functions.

Each of these helper functions return a "[`Promise`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)"
that only resolves for this [happy path](https://en.wikipedia.org/wiki/Happy_path),
making it easy to implement the logic by chaining them together using `then`
handlers. In all other cases—if it's not time to process the trigger list, or
if an exception is raised along the way—the exception handler is called. In
this implementation, the exception handler does nothing except return a `200`
HTTP status code.

### Understanding `checkTimestamp`

The `checkTimestamp` function works by reading a `Cron` entity from Cloud
Datastore, that has a `timestamp` field indicating the last time the trigger
list was processed.

    function checkTimestamp() {
      const now = (new Date()).getTime() / 1000;

      const datastore = new Datastore();  // Authenticating on a global basis.
      const key = datastore.key(['Cron', '1 Minute']);
      const transaction = datastore.transaction();

      return transaction.run()
        .then(() => transaction.get(key))
        .then((results) => {
          const entity = results[0];
          if (!entity || now - entity.timestamp >= 60) {
            transaction.save({ key: key, data: { timestamp: now } });
            return transaction.commit();
          } else {
            throw new Error('It is not time yet');
          }
        })
        .catch((err) => {
          transaction.rollback();
          return Promise.reject(err);
        });
    }

If enough time has elapsed, 60 seconds in this example, or if the entity is not
found, which is the case the first time this function is executed,
`checkTimestamp` does the following:

1.  Updates the `timestamp` field of the entity with the current time.
1.  Resolves the `Promise`, indicating that it's time to process the trigger
    list again.

In all other cases `checkTimestamp` throws an exception, causing the `Promise`
to be rejected. You can implement a different schedule by using a different
value for the desired elapsed time, currently set at 60 seconds.

#### Transactional execution

All the Cloud Datastore operations are executed in context of a [transaction](https://cloud.google.com/datastore/docs/concepts/transactions) to guarantee
[strong consistency](https://cloud.google.com/datastore/docs/concepts/structuring_for_strong_consistency)
in reading the `timestamp` during every invocation of the master function.
Transactions also eliminate any race conditions that might arise if the master
function is triggered multiple times in quick succession.

### Understanding `readTriggerList`

The `readTriggerList` helper function reads the trigger list from Cloud Storage,
parses the JSON-formatted content, and returns it as a `triggerList` object. All
of this is done in context of a `Promise`, since reading from Cloud Storage is
an asynchronous operation.

    function readTriggerList() {
      const gcs = new GCS();
      const triggerListFile = gcs.bucket(BUCKET).file(TRIGGER_LIST);

      const triggerList = Buffer.from('');

      return new Promise((resolve, reject) => {
        triggerListFile.createReadStream()
          .on('data', (chunk) => {
            triggerList = Buffer.concat([triggerList, chunk]);
          })
          .on('end', () => {
            resolve(JSON.parse(triggerList));
          });
      });
    }

The `triggerList` object is an array of items, one for each Cloud Function to be
triggered. In this example only HTTP Cloud Functions are supported, and each
item includes:

* The URL of the Cloud Function.
* The HTTP method used to trigger the function.
* Any data associated with POST requests.

### Understanding `runTriggerList`

The `runTriggerList` helper function loops through each entry in the
`triggerList` array and uses the request `npm` module to trigger each scheduled
Cloud Function using its configured HTTP method and URL.

    function runTriggerList(res, triggerList) {
      console.log('Processing trigger list');

      triggerList.forEach((item) => {
        switch (item.method) {
          case 'GET':
            Request.get(item.url);
            res.status(200).end();
            break;
          case 'POST':
            Request.post(item.url).form(item.data || {});
            res.status(200).end();
            break;
          default:
            res.status(405).send(`Method ${item.method} is not supported`);
        }
      });
    }

# Deploying the function

1.  Similar to how you deployed the target function, run the following command
    to deploy the master function. Record the URL displayed in the status,
    referred to as **`[MASTER_FUNCTION_URL]`**, for later use:

        gcloud beta functions deploy cronMaster --stage-bucket ${STAGE_BUCKET} --trigger-http

        ...
        Deploying function (may take a while - up to 2 minutes)...done.
        availableMemoryMb: 256
        entryPoint: cronMaster
        httpsTrigger:
          url: https://us-central1-gcf-cron.cloudfunctions.net/cronMaster
        labels:
          deployment-tool: cli-gcloud
        ...

1.  To verify the status of the deployment, run the following command:

        gcloud beta functions describe cronMaster

    Ensure that the `status` is shown as **`READY`**:

        ...
        sourceArchiveUrl: gs://sujoy-gcf-stage/us-central1-cronMaster-dabjebvfuxqj.zip
        status: READY
        timeout: 60s
        ...

# Adding uptime checks

If you have previously activated Stackdriver Monitoring and connected it to your
project, you're ready to add uptime checks. All the following steps require use
of the Stackdriver dashboard.

1.  In the left-side navigation menu click **Uptime Checks**, and on the submenu
    that appears click **Uptime Checks Overview**.

    ![Uptime checks overview page](https://storage.googleapis.com/gcp-community/tutorials/using-stackdriver-uptime-checks-for-scheduling-cloud-functions/image4.png)

1.  In the resulting **Uptime Checks** page, click **Add Uptime Check** at the
    top right.

    ![Creating an uptime check](https://storage.googleapis.com/gcp-community/tutorials/using-stackdriver-uptime-checks-for-scheduling-cloud-functions/image6.png)

1.  If a popup such as the following appears, uncheck everything under
    **DETECTED RESOURCES** and click **No thanks**:

    ![Detected resources popup](https://storage.googleapis.com/gcp-community/tutorials/using-stackdriver-uptime-checks-for-scheduling-cloud-functions/image3.png)

1.  In the **New Uptime Check** popup, fill in the form for creating a
    per-minute check by replacing the **Hostname** and **Path** with the
    hostname and path from your master function URL. Click **Save** after you
    are done:

    ![New uptime check popup](https://storage.googleapis.com/gcp-community/tutorials/using-stackdriver-uptime-checks-for-scheduling-cloud-functions/image2.png)

1.  If a **Uptime Check Created** confirmation window appears click **No Thanks**.

    ![Alerting policies confirmation window](https://storage.googleapis.com/gcp-community/tutorials/using-stackdriver-uptime-checks-for-scheduling-cloud-functions/image1.png)

    At this point, uptime checks have been created. It may take a few minutes
    for them the uptime checks to be activated.

# Verifying the setup

1.  After you create uptime checks there may be a lag of a few minutes before
    they're activated. To check whether they've been activated, navigate to the
    Stackdriver dashboard.  On the left navigation menu click **Uptime Checks**,
    and in the submenu click **Uptime Checks Overview**. Once the checks have
    been activated, you'll see something like the following screenshot, showing
    the uptime check locations and current status:

    ![Uptime checks overview](https://storage.googleapis.com/gcp-community/tutorials/using-stackdriver-uptime-checks-for-scheduling-cloud-functions/image5.png)

1.  The master Cloud Function logs a message "Processing trigger list" to the
    console every time it processes the trigger list and triggers scheduled
    Cloud Functions. Verify that the master Cloud Function is processing the
    trigger list on schedule by looking for these log messages and the
    timestamps they were logged.  Run the following command and confirm the
    output:

        gcloud beta functions logs read cronMaster --min-log-level INFO

    With approximate output:

        LEVEL  NAME        EXECUTION_ID  TIME_UTC                 LOG
        I      cronMaster  6ja82gv4amig  2017-08-24 22:06:15.896  Processing trigger list
        I      cronMaster  6ja8vbkn30i3  2017-08-24 22:07:15.334  Processing trigger list
        I      cronMaster  6ja8a7s2810n  2017-08-24 22:08:15.287  Processing trigger list
        I      cronMaster  6ja8gsk4z60x  2017-08-24 22:09:15.422  Processing trigger list
        I      cronMaster  6ja86j4j3xqw  2017-08-24 22:10:15.452  Processing trigger list

1.  The target Cloud Function writes a log message to console every time it's
    triggered. The log messages include the triggering HTTP method and the
    associated timestamp. Run the following command to look for these messages
    and verify that example functions were triggered on schedule:

        gcloud beta functions logs read cronTarget --min-log-level INFO

    With approximate output:

        LEVEL  NAME        EXECUTION_ID  TIME_UTC                 LOG
        I      cronTarget  kuufou3idad8  2017-08-21 21:27:52.669  GET received at Mon, 21 Aug 2017 21:27:52 GMT
        I      cronTarget  kuufgco9fk1s  2017-08-21 21:27:53.365  POST received at Mon, 21 Aug 2017 21:27:53 GMT with Hello, World!
        I      cronTarget  kuufhn9ojq8d  2017-08-21 21:29:07.662  GET received at Mon, 21 Aug 2017 21:29:07 GMT
        I      cronTarget  kuufen00qbs6  2017-08-21 21:29:07.777  POST received at Mon, 21 Aug 2017 21:29:07 GMT with Hello, World!
        I      cronTarget  kuufsxsrw27x  2017-08-21 21:30:09.276  GET received at Mon, 21 Aug 2017 21:30:09 GMT
        I      cronTarget  kuuffj5egn2v  2017-08-21 21:30:10.070  POST received at Mon, 21 Aug 2017 21:30:10 GMT with Hello, World!
        I      cronTarget  kuufbliv4f43  2017-08-21 21:31:15.089  GET received at Mon, 21 Aug 2017 21:31:15 GMT

# Cleaning up

After you've finished the tutorial, clean up the GCP resources so you won't
continue to be billed for them. The easiest way to eliminate billing is to
delete the project you created for the tutorial.

To delete the project:

1.  In the Cloud Platform Console, go to the
    [Projects](https://console.cloud.google.com/iam-admin/projects) page.
1.  Click the trash can icon to the right of the project name.

Warning: If you used an existing project, deleting the project also deletes
any other work you've done in the project.

# Next steps

## Using App Engine Cron Service

At the time of writing, Stackdriver uptime checks can only run every 1, 5, 10 or
15 minutes. Cloud Functions scheduled using this method have, at most, a
one-minute resolution.

App Engine has a Cron Service allowing you to schedule tasks that operate at
defined times or at regular intervals. It offers support for a much more
expressive schedule out of the box and is designed specifically for scheduling
jobs, but the Cron Service requires deploying and managing an App Engine
service.

## Using a crontab

This tutorial uses a separate master function and a trigger list for each
schedule. You should be able to extend this approach and use a single list
formatted like a [traditional crontab](https://en.wikipedia.org/wiki/Cron), with
entries defining the schedule of triggering of each function:

    ┌───────────── minute (0 - 59)
    │ ┌───────────── hour (0 - 23)
    │ │ ┌───────────── day of month (1 - 31)
    │ │ │ ┌───────────── month (1 - 12)
    │ │ │ │ ┌───────────── day of week (0 - 6)
    │ │ │ │ │
    │ │ │ │ │
    * * * * *  function to trigger

You can find `npm` modules which parse these types of crontabs. Using this
approach, you could use a single master Cloud Function that's triggered every
minute and processes the crontab to determine which target functions should be
triggered.
