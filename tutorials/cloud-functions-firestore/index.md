---
title: Use Cloud Firestore with Cloud Functions
description: Learn how to use Cloud Functions to store and retrieve data with Cloud Firestore.
author: zeroasterisk
tags: Cloud Functions, Cloud Datastore, Cloud Firestore
date_published: 2018-12-29
---
## Introduction

This tutorial demonstrates using
[Google Cloud Functions][functions]
to store and retrieve data to
[Google Cloud Firestore][firestore].
The Cloud Function is
implemented in [Node.js][node] version 6 *(or 8)*.

[functions]: https://cloud.google.com/functions
[firestore]: https://cloud.google.com/firestore/
[node]: https://nodejs.org/en/

The sample Cloud Function is triggered by a web request,
which you can simulate with `curl`.

## Prerequisites

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  [Enable the Google Cloud Functions API][enable_functions].
1.  [Enable the Google Cloud Firestore API][enable_firestore] *(Datastore mode)*.
1.  Install and initialize the [Google Cloud SDK][sdk].

    1.  After initializing the SDK, configure the gcloud CLI for your project_id.

        gcloud config set project <projectid>

[console]: https://console.cloud.google.com/
[enable_functions]: https://console.cloud.google.com/apis/api/cloudfunctions.googleapis.com/overview
[enable_firestore]: https://console.cloud.google.com/firestore/welcome
[sdk]: https://cloud.google.com/sdk/

This guide uses `cloud-functions-firestore` as the project_id, as well as the firestore collection.

## Preparing the Cloud Function

This Cloud Function will either
store a basic POST payload as a document in Firestore
or retrieve a document from Firestore by ID.

    <!--
    You can find the
    [zerobin codebase on github](...)
    which is the source of this example.
    -->

Alternatively, you can download
[package.json](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-functions-firestore/package.json)
&amp;
[index.js](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-functions-firestore/index.js)

### Start a new npm app

If you do not already have an npm project,
go ahead and create one. *(in a new directory)*

    npm init

### Install @google-cloud/firestore

Let's add the firestore client to our node app, saving the dependency.

    npm install --save --save-exact @google-cloud/firestore

### Writing the Cloud Function Code

You can copy and paste the simplified version of the code,
into `index.js` (or
[download](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-functions-firestore/index.js)).

    const Firestore = require('@google-cloud/firestore');
    const PROJECTID = 'cloud-functions-firestore';
    const COLLECTION_NAME = 'cloud-functions-firestore';
    const firestore = new Firestore({
      projectId: PROJECTID,
      timestampsInSnapshots: true,
    });

    exports.main = (req, res) => {
      if (req.method === 'DELETE') throw 'not yet built';
      if (req.method === 'POST') {
        // store/insert a new document
        const data = (req.body) || {};
        const ttl = Number.parseInt(data.ttl);
        const ciphertext = (data.ciphertext || '').replace(/[^a-zA-Z0-9\-]*/g, '');
        const created = new Date().getTime();
        return firestore.collection(COLLECTION_NAME)
          .add({ created, ttl, ciphertext })
          .then(doc => {
            return res.status(200).send(doc);
          }).catch(err => {
            console.error(err);
            return res.status(404).send({ error: 'unable to store', err });
          });
      }
      // read/retrieve an existing document by id
      if (!(req.query && req.query.id)) {
        return res.status(404).send({ error: 'No Id' });
      }
      const id = req.query.id.replace(/[^a-zA-Z0-9]/g, '').trim();
      if (!(id && id.length)) {
        return res.status(404).send({ error: 'Empty Id' });
      }
      return firestore.collection(COLLECTION_NAME)
        .doc(id)
        .get()
        .then(doc => {
          if (!(doc && doc.exists)) {
            return res.status(404).send({ error: 'Unable to find the document' });
          }
          const data = doc.data();
          return res.status(200).send(data);
        }).catch(err => {
          console.error(err);
          return res.status(404).send({ error: 'Unable to retrieve the document' });
        });
    };

In that code, the function is going to listen for a POST
with the data fields of `ciphertext` and `ttl`.
It will store the values into a new document in firestore
using the `add()` function (which auto-assigns an ID).

And the function is also listening for a GET request with an `id` in the querystring.
It will lookup that document in firestore and, if found, return the document.

NOTE: you probably want more input sanitation for a production application.

## Deploying the Cloud Function

Once the code is deployed, Google Cloud Functions will automatically run that code for us, when triggered.

You now have a `package.json` file listing your dependencies
and you have an `index.js` file which will respond to an HTTP trigger.

You will use the `gcloud` CLI tool to deploy our function, and configure it to listen to HTTP requests.
(there are other ways to deploy including
[git-push CI/CD tooling](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-functions-github-auto-deployer/index.md)).

### (optional) Install functions-emulator for local testing

Testing things is nice.
You can install a
[local emulator for Google Cloud Functions](https://github.com/GoogleCloudPlatform/cloud-functions-emulator).

    npm install -g @google-cloud/functions-emulator
    export GOOGLE_APPLICATION_CREDENTIALS=/Users/myname/.cred/myserviceaccount.json
    functions start
    functions deploy main --trigger-http

In this case, `main` is the name of the function you want to trigger in your code, triggered by an HTTP request.

> NOTE: if you're on `zsh`, you may not be able to execute `functions`.
> Either start `bash`, or execute `sh -c 'which functions'`
> to find the proper path for you.
> eg: `/Users/myname/.npm-global/bin/functions`

Now you can test your function by sending `curl` requests.

You can create a new document:

    curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}' \
      http://localhost:8010/cloud-functions-firestore/us-central1/main
    {"id":"wLcIOzic6BeoEk3tV4sH"}

And retrieve that document:

    curl http://localhost:8010/cloud-functions-firestore/us-central1/main?id=wLcIOzic6BeoEk3tV4sH
    {"created":15369690190000,"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}

NOTE that our function code added `created`.

### Deploy the code to Google Cloud Functions

This is very easy thanks to the gcloud CLI.

    gcloud functions deploy main --trigger-http

In this case, `main` is the name of the function you want to trigger in your code, triggered by an HTTP request.

> NOTE: If you used the emulator above, you can simply prefix the command with `gcloud`

    Deploying function (may take a while - up to 2 minutes)...done.
    availableMemoryMb: 256
    entryPoint: main
    httpsTrigger:
      url: https://us-central1-cloud-functions-firestore.cloudfunctions.net/main
    labels:
      deployment-tool: cli-gcloud
    name: projects/cloud-functions-firestore/locations/us-central1/functions/main
    runtime: nodejs6
    serviceAccountEmail: cloud-functions-firestore@appspot.gserviceaccount.com
    sourceUploadUrl: https://storage.googleapis.com/gcf-upload-us-central1-0000000000.zip?GoogleAccessId=service-...
    status: ACTIVE
    timeout: 60s
    updateTime: '2018-09-15T01:25:59Z'
    versionId: '1'

## Testing the deployed Cloud Function in production

You should now be able to send HTTP requests to the endpoint and test out the function in production.

Now you can test your function by sending `curl` requests.

You can create a new document:

    curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}' \
      https://us-central1-cloud-functions-firestore.cloudfunctions.net/main
    {"id":"wLcIOzic6BeoEk3tV4sH"}

And retrieve that document:

    curl https://us-central1-cloud-functions-firestore.cloudfunctions.net/main?id=wLcIOzic6BeoEk3tV4sH
    {"created":15369690190000,"ttl":1,"ciphertext":"daa5370871aa301e5e12d4274d80691f75e295d648aa84b73e291d8c82"}

NOTE that our function code added `created`.

## Iterate

This is a very short cycle of `[code, deploy, test]`
so you should be able to iterate rapidly.

When you deploy, you overwrite the current version, at the function's URL *(blue/green deployment in the background, can take a few seconds to switch over)*.

If you need to access a previously deployed version, you can append `/revisions/${REVISION}` with the value of the `versionId` that deploy gives you back.

There are lot of other settings available. Review [docs][function-docs] and help:

     gcloud functions deploy --help

## Your turn

As you can see, it is very easy to create and deploy small functions.

You can deploy larger applications just as easily.

Your functions can be triggered by many other events, not just web requests.

And you only pay for your functions for the seconds they are being run, and they can scale out as needed even if you get super-popular.

Read more [about functions][function-docs] and make something awesome!

[function-docs]: https://cloud.google.com/functions/docs/
