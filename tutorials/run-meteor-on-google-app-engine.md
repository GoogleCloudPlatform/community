---
title: Run Meteor on the App Engine flexible environment
description: Learn how to deploy a Meteor app to App Engine flexible environment.
author: anassri
tags: App Engine, Meteor, Node.js
date_published: 2016-10-25
---
## Meteor

> [Meteor](https://meteor.com) is an open source platform for web, mobile, and
> desktop.
>
> – meteor.com

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. [Install Meteor](https://meteor.com/install) on your local machine.

1. Create a MongoDB instance as described [here][deploy-mongodb]. Remember your
`MONGO_URL`, you will need that later. An example MongoDB URI would be
`mongodb://username:password@host:port`.

## Create

1.  Initialize a Meteor project by running the following commands:

        meteor create [YOUR_APP_NAME]
        cd [YOUR_APP_NAME]
        meteor add reactive-dict
        meteor remove autopublish

    replacing `[YOUR_APP_NAME]` with your app name.

1.  To add database functionality, edit `[YOUR_APP_NAME]/client/main.js` to look like:

        import { Template } from 'meteor/templating';
        import { ReactiveVar } from 'meteor/reactive-var';
        import { Meteor } from 'meteor/meteor'

        import './main.html';

        Template.hello.onCreated(function helloOnCreated() {
          // counter starts at 0
          this.counter = new ReactiveDict({value: '0' });
          var instance = this;

          Meteor.subscribe('counters', function () {
            var counterConn = new Mongo.Collection('counters');
            instance.counterConn = counterConn;

            var counterList = counterConn.find({}).fetch();
            var dbCounter = counterList[0];
            instance.dbCounter = dbCounter;

            instance.counter.set('_id', dbCounter._id);
            instance.counter.set('value', dbCounter.value);
          });
        });

        Template.hello.helpers({
          counter() {
            return Template.instance().counter.get('value');
          },
        });

        Template.hello.events({
          'click button'(event, instance) {

            // Increment counter
            instance.counter.set('value', instance.counter.get('value') + 1);

            // Update counter on DB
            instance.counterConn.update(instance.dbCounter._id, {
              '$set': {'value': instance.counter.get('value') }
            });
          },
        });

1.  Edit `[APP_NAME]/server/main.js` so that it looks like:

        import { Meteor } from 'meteor/meteor';
        import { Mongo } from 'meteor/mongo';

        Meteor.startup(() => {
          // code to run on server at startup
          const Counters = new Mongo.Collection('counters');

          // Make sure a Counter entry exists
          if (Counters.find({}).fetch().length == 0)
            Counters.insert({value: 0})

          // Publish counters
          Meteor.publish('counters', function () {
            return Counters.find({});
          })
        });
    
## Run

1. Run the app with the following command:

        MONGO_URL=[MONGO_URL] meteor run

    replacing `[MONGO_URL]` with your MongoDB URI.

1. Visit [http://localhost:3000](http://localhost:3000) to see the
`Welcome to Meteor!` message.

    When you're done, use `CTRL+C` to exit Meteor.

## Deploy

1.  Add the following to the `package.json` file:

        "scripts": {
          "cleanup": "rm -rf ../bundle/",
          "dist": "npm run cleanup && meteor build ../ --directory --architecture os.linux.x86_64 --server-only",
          "predeploy": "npm run dist && cp app.yaml ../bundle/ && cp Dockerfile ../bundle/",
          "deploy": "npm run predeploy && (cd ../bundle && gcloud app deploy -q)"
        },
  

    These scripts provide you with some tasks that prepare the app for
    deployment to the App Engine flexible environment. See
    [Custom deployment][custom] for more information about custom Meteor
    deployments.

1.  Configure a [custom runtime](/appengine/docs/flexible/custom-runtimes/) by running the following command:

        gcloud beta app gen-config --custom

1.  Replace the contents of the `Dockerfile` file with the following:

        FROM gcr.io/google_appengine/nodejs
        COPY . /app/
        RUN (cd programs/server && npm install --unsafe-perm)
        CMD node main.js

    The custom `Dockerfile` is required in order to properly build the Meteor
    app in production.

1.  Add the following to the generated `app.yaml` file:

        env_variables:
          ROOT_URL: https://[YOUR_PROJECT_ID].appspot-preview.com
          MONGO_URL: [MONGO_URL]
          DISABLE_WEBSOCKETS: "1"
   
    replacing `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID and
    `[MONGO_URL]` with your MongoDB URI.

1.  Run the following command to deploy your app:

        npm run deploy

1.  Visit `https://[YOUR_PROJECT_ID].appspot.com` to see the `Welcome to Meteor!`
message, replacing `[YOUR_PROJECT_ID]` with your Google Cloud Platform project
ID. To test database functionality, click on the button a few times and refresh
the page. You should see your previous button-click count appear after a few
seconds.

[deploy-mongodb]: https://cloud.google.com/nodejs/getting-started/deploy-mongodb
[custom]: https://guide.meteor.com/deployment.html#custom-deployment
[nodejs-gcp]: https://cloud.google.com/nodejs/
