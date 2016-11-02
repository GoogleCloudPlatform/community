---
title: Run Meteor on Google App Engine
description: Learn how to deploy a Meteor app to App Engine Flexible
author: anassri
tags: App Engine, Meteor, Node.js
date_published: 10/25/2016
---
## Meteor

> [Meteor](https://meteor.com) is an open source platform for web, mobile, and desktop.
>
> – meteor.com

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare
[Install Meteor](https://meteor.com/install).

## Creation

### Initialize a Meteor project
Initialize a Meteor project by `cd`ing to the target folder and running the following command:

    meteor create [YOUR_APP_NAME]
    cd [YOUR_APP_NAME]
    meteor add reactive-dict
    meteor remove autopublish

Replace `[YOUR_APP_NAME]` with your app name.

### Add database functionality
If you want to make sure MongoDB is working correctly, you can add some simple database functionality to your app by editing the `main.js` files `[YOUR_APP_NAME]/client` and `[YOUR_APP_NAME]/server`.

If you are not interested in adding database functionality to your app, then you can skip to the Running section. Otherwise, change `[YOUR_APP_NAME]/client/main.js` to look like:

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

You'll also need to edit `[APP_NAME]/server/main.js` so that it looks like:

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

## Running

Run the Meteor project by `cd`ing into the project's directory (if necessary) and running the commands below:

    cd [YOUR_APP_NAME] # if necessary
    meteor

Go to your Meteor app's location (`http://localhost:3000` by default) to see the `Welcome to Meteor!` message.

When you're done, use CTRL-C to exit Meteor.

## Configuration

### Initialize a Mongo instance
Create a Mongo instance as described [here](https://cloud.google.com/nodejs/getting-started/deploy-mongodb). Remember your `MONGO_URL` - you'll need that for the next step.

### Configure a custom runtime
Create an `app.yaml` file with the following contents:

    runtime: custom
    vm: true
    env_variables:
        MONGO_URL: [MONGO_URL]
        DISABLE_WEBSOCKETS: "1"

Replace `[MONGO_URL]` with a valid Mongo URL as described in [this tutorial](/nodejs/getting-started/deploy-mongodb).

Then, configure a [custom runtime](/appengine/docs/flexible/custom-runtimes/) by creating a `Dockerfile` as follows:

    # Extending the generic Node.js image
    FROM gcr.io/google_appengine/nodejs
    COPY . /app/

    # Install Meteor
    RUN curl "https://install.meteor.com" | sh

    # Install dependencies
    RUN npm install --unsafe-perm

The `app.yaml` makes the app deployable to Google App Engine Flexible, while the Dockerfile specifies the steps to take during the deployment.

### Configure Meteor for Deployment
In order for Meteor to work on App Engine, it must run on the port indicated by the $PORT environment variable. We can configure Meteor to run on a specific port by adding a `port` flag to the `start` script in `package.json` as follows:

    "start": "meteor run --port $PORT"

## Deployment
Run the following command to deploy your app:

    gcloud app deploy

Once the deployment process completes, go to `http://<your-project-id>.appspot.com` to see the `Welcome to Meteor!` message. To test database functionality, click on the button a few times and refresh the page. You should see your previous button-click count appear after a few seconds.
