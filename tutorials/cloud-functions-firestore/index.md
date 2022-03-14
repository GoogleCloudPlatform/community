---
title: Use Firestore with Cloud Functions
description: Learn how to use Cloud Functions to store and retrieve data with Firestore.
author: zeroasterisk
tags: Cloud Functions, Datastore, Firestore
date_published: 2018-12-29
---

Alan Blount | Product Solutions Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using [Cloud Functions][functions] to store and retrieve data with
[Firestore][firestore]. The Cloud Function is implemented in [Node.js][node] and tested with
versions 10, 12, and 14.

[functions]: https://cloud.google.com/functions
[firestore]: https://cloud.google.com/firestore/
[node]: https://nodejs.org/en/

The sample Cloud Function is triggered by a web request,
which you can simulate with `curl`.

## Prerequisites

1.  Create a project in the [Cloud Console][console].
1.  [Enable billing][billing] for your project.
1.  [Enable the Cloud Functions API][enable_functions].
1.  [Enable the Firestore API][enable_firestore] (with Firestore in [Native mode][native_mode]).
1.  Open [Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell).
1.  Set the project ID for the Cloud SDK:

        gcloud config set project [PROJECT_ID]

[console]: https://console.cloud.google.com/
[enable_functions]: https://console.cloud.google.com/apis/api/cloudfunctions.googleapis.com/overview
[enable_firestore]: https://console.cloud.google.com/firestore/welcome
[sdk]: https://cloud.google.com/sdk/
[native_mode]: https://cloud.google.com/firestore/docs/firestore-or-datastore
[billing]: https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project

This guide uses `cloud-functions-firestore` as the Firestore collection.

## Preparing the Cloud Function

This Cloud Function will either store a basic POST payload as a document in Firestore
or retrieve a document from Firestore by ID.

You can find the [source code](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/cloud-functions-firestore) on GitHub.

Alternatively, you can download
[`package.json`](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-functions-firestore/package.json)
and
[`index.js`](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-functions-firestore/index.js)

### Start a new npm app

If you do not already have an npm project,
go ahead and create one in a new directory:

    mkdir cloud-functions-firestore
    cd cloud-functions-firestore
    npm init

### Install @google-cloud/firestore

Add the Firestore client to your Node.js app, saving the dependency:

    npm install --save --save-exact @google-cloud/firestore

### Writing the Cloud Function code

You can copy and paste the simplified version of the code,
into `index.js` (or
[download it](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-functions-firestore/index.js)).

    const Firestore = require('@google-cloud/firestore');
    // Use your project ID here
    const PROJECTID = '[YOUR_PROJECT_ID]';
    const COLLECTION_NAME = 'cloud-functions-firestore';

    const firestore = new Firestore({
      projectId: PROJECTID,
      timestampsInSnapshots: true
      // NOTE: Don't hardcode your project credentials here.
      // If you have to, export the following to your shell:
      //   GOOGLE_APPLICATION_CREDENTIALS=<path>
      // keyFilename: '/cred/cloud-functions-firestore-000000000000.json',
    });

    /**
    * Retrieve or store a method in Firestore
    *
    * Responds to any HTTP request.
    *
    * GET = retrieve
    * POST = store (no update)
    *
    * success: returns the document content in JSON format & status=200
    *    else: returns an error:<string> & status=404
    *
    * @param {!express:Request} req HTTP request context.
    * @param {!express:Response} res HTTP response context.
    */
    exports.main = (req, res) => {
      if (req.method === 'POST') {
        // store/insert a new document
        const data = (req.body) || {};
        const ttl = Number.parseInt(data.ttl);
        const ciphertext = (data.ciphertext || '')
          .replace(/[^a-zA-Z0-9\-_!.,; ']*/g, '')
          .trim();
        const created = new Date().getTime();

        // .add() will automatically assign an ID
        return firestore.collection(COLLECTION_NAME).add({
          created,
          ttl,
          ciphertext
        }).then(doc => {
          console.info('stored new doc id#', doc.id);
          return res.status(200).send(doc);
        }).catch(err => {
          console.error(err);
          return res.status(404).send({
            error: 'unable to store',
            err
          });
        });
      }

      // everything below this requires an ID
      if (!(req.query && req.query.id)) {
        return res.status(404).send({
          error: 'No II'
        });
      }
      const id = req.query.id.replace(/[^a-zA-Z0-9]/g, '').trim();
      if (!(id && id.length)) {
        return res.status(404).send({
          error: 'Empty ID'
        });
      }

      if (req.method === 'DELETE') {
        // delete an existing document by ID
        return firestore.collection(COLLECTION_NAME)
          .doc(id)
          .delete()
          .then(() => {
            return res.status(200).send({ status: 'ok' });
          }).catch(err => {
            console.error(err);
            return res.status(404).send({
              error: 'unable to delete',
              err
            });
          });
      }

      // read/retrieve an existing document by ID
      return firestore.collection(COLLECTION_NAME)
        .doc(id)
        .get()
        .then(doc => {
          if (!(doc && doc.exists)) {
            return res.status(404).send({
              error: 'Unable to find the document'
            });
          }
          const data = doc.data();
          if (!data) {
            return res.status(404).send({
              error: 'Found document is empty'
            });
          }
          return res.status(200).send(data);
        }).catch(err => {
          console.error(err);
          return res.status(404).send({
            error: 'Unable to retrieve the document',
            err
          });
        });
    };

**Note**: Replace `[YOUR_PROJECT_ID]` in the code with your project ID.

In this code, the function listens for a POST request
with the data fields of `ciphertext` and `ttl`.
It will store the values into a new document in Firestore
using the `add()` function (which auto-assigns an ID).

The function also listens for a GET request with an `id` in the query string.
It will look up that document in Firestore and, if found, return the document.

**Note**: You probably want more input sanitation for a production application.

## Deploying the Cloud Function

After the code is deployed, Cloud Functions will automatically run that code when triggered.

You now have a `package.json` file listing your dependencies
and you have an `index.js` file which will respond to an HTTP trigger.

You use the `gcloud` command-line tool to deploy the function, and configure it to listen to HTTP requests.

### (optional) Install functions-emulator for local testing

You can
[run and test your function locally](https://cloud.google.com/functions/docs/running/overview).

To do that, you need to install the functions framework:

    npm install --save-dev @google-cloud/functions-framework

Follow the [instructions](https://cloud.google.com/functions/docs/running/function-frameworks#per-language_instructions)
to configure the `package.json` file if you are not using the downloaded version.

Start the function:

    npm start

By default, the function listens on port 8080. You can test it by sending `curl` requests.

You can open a new terminal by clicking the `+` sign in the menu bar and running the following command
to create a new document:

    curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}' \
      http://localhost:8080

The output is the following:

    {"_firestore":{"projectId":"xxxxx"},"_path":{"segments":["cloud-functions-firestore","bdgb7hQKbTL6PCROwLsO"]},"_converter":{}}

You can retrieve the document:

    curl http://localhost:8080?id=bdgb7hQKbTL6PCROwLsO
    
The output is similar to the following:

    {"ttl":1,"created":1625077880857,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}

Note that the function code added the field `created`.

### Deploy the code to Google Cloud Functions

Deploying the code is easy with the gcloud command-line interface.

    gcloud functions deploy cloud-functions-firestore \
      --entry-point=main \
      --trigger-http \
      --runtime=nodejs12 \
      --allow-unauthenticated

In this case, `cloud-functions-firestore` is the name of the function that you want to trigger in your code, triggered by an HTTP request. `main` is the entry point of the function.

The output is similar to the following:

    Deploying function (may take a while - up to 2 minutes)...⠹
    For Cloud Build Logs, visit: https://console.cloud.google.com/cloud-build/builds;region=us-central1/1538f6d2-e6b6-4deb-8583-b872ae5e2de1?project=xxxxx
    Deploying function (may take a while - up to 2 minutes)...done.
    availableMemoryMb: 256
    buildId: 1538f6d2-e6b6-4deb-8583-b872ae5e2de1
    entryPoint: main
    httpsTrigger:
      securityLevel: SECURE_OPTIONAL
      url: us-central1-[YOUR_PROJECT_ID].cloudfunctions.net/cloud-functions-firestore
    ingressSettings: ALLOW_ALL
    labels:
      deployment-tool: cli-gcloud
    name: projects/xxxxx/locations/us-central1/functions/cloud-functions-firestore
    runtime: nodejs12
    serviceAccountEmail: xxxxx@appspot.gserviceaccount.com
    sourceUploadUrl: https://storage.googleapis.com/......
    status: ACTIVE
    timeout: 60s
    updateTime: '2021-06-30T18:54:10.142Z'
    versionId: '1'

## Testing the deployed Cloud Function in production

You should now be able to send HTTP requests to the endpoint and test out the function in production.

Now you can test your function by sending `curl` requests to the HTTPS trigger URL, which you can find 
from the deployment output or from the Cloud Functions console.

You can create a new document:

    curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}' \
      https://us-central1-[YOUR_PROJECT_ID].cloudfunctions.net/cloud-functions-firestore

The output is similar to the following:

    {"_firestore":{"projectId":"[YOUR_PROJECT_ID]"},"_path":{"segments":["cloud-functions-firestore","61Eej99ONcqY4jVvj1Ij"]},"_converter":{}}

Retrieve the document:

    curl https://us-central1-[YOUR_PROJECT_ID].cloudfunctions.net/cloud-functions-firestore?id=61Eej99ONcqY4jVvj1Ij

The output is similar to the following:

    {"created":1625079401209,"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}

Note that our function code added field `created`.

## Iterate

This is a very short cycle of code, deploy, and test, so you should be able to iterate rapidly.

When you deploy, you overwrite the current version, at the function's URL *(blue/green deployment in the background, can take a few seconds to switch over)*.

If you need to access a previously deployed version, you can append `/revisions/${REVISION}` with the value of the `versionId` that the `deploy` command 
returns.

There are a lot of other settings available. Review [docs][function-docs] and help:

     gcloud functions deploy --help

## What's next

As you can see, it is very easy to create and deploy small functions.

You can deploy larger applications just as easily.

Your functions can be triggered by many other events, not just web requests.

And you only pay for your functions for the seconds they are being run, and they can scale out as needed even if you get super-popular.

Read more [about Cloud Functions][function-docs], and make something awesome!

[function-docs]: https://cloud.google.com/functions/docs/
