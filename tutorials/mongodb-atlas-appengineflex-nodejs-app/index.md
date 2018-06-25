---
title: Hello World App - MongoDB Atlas and App Engine Flex - NodeJS
description: Learn how to build Node.js application with Google App Engine flexible environment and MongoDB Atlas.
author: arajwade, ksmith
tags: App Engine, Node.js, MongoDB Atlas
date_published: 2018-06-25
---

## Overview

In this tutorial, you will be building a "Hello World" application using Node.js
with Google App Engine flexible environment for our frontend and a MongoDB Atlas
multi-regional cluster on Google Cloud Platform as our primary database.

### Technical Complecity

Beginner

### Duration

45 Minutes

### Objectives

1.  Create and configure MongoDB Atlas multi-regional cluster on GCP.
2.  Configuring our Google Cloud Platform Account.
3.  Configure a Node.js application on a GCE Debian VM on GCP.
4.  Push your application to App Engine Flex on GCP.
5.  Visit our new application from any web-enabled client terminal, including
    mobile devices.

## Part 1: Configuring the MongoDB Atlas

1.  Create a free account on MongoDB Atlas on www.mongodb.com/cloud/atlas

    Click on "Login" at the top of the page:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image18.png)

2.  If you do not already have a MongoDB Atlas account, register for new account
    at the bottom of the page. If you do, skip to Step 5.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image3.png)

3.  Enter necessary details and click "Continue":

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image12.png)

4.  Once on the MongoDB Atlas Homepage, select "Build a New Cluster":

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image15.png)

5.  Create New Cluster by selecting Google Cloud Platform as a "Cloud Provider".
    Next select the region where you want to place your Atlas cluster. Ideally,
    your cluster will be located close to your end user for lower latency. Note
    that we can select a free tier region in your area of choice, as noted by
    the "Free Tier Available" icon. This is a no-cost option to get started.
    However, since we are assuming our end users will span across the globe, we
    want our Atlas cluster to be multi-regional. To enable a multi-regional
    cluster, we will need to select a M10 or larger cluster size. So for now,
    for our use case, let’s assume our primary end users for our application
    will be based in the US and a smaller percentage based in the UK and
    Australia. As such, we will select our primary region to be in North
    America, based in Iowa (us-central1).

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image45.png)

6.  Next, to enable multiple regions, lets configure our cluster size under
    "Cluster Tier". Select "M10" under "Dedicated Development Clusters"
    subheading since this is the minimal size to move forward for
    multiple-regions.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image11.png)

7.  Now that we selected a M10 cluster, let's go back to "Cloud Provider &
    Region" and toggle the option to "Configure clusters across multiple
    regions" from "No" to "Yes". Once we enable this we will see more options.
    You will see your previously selected region as "Preferred" under "Node
    Type". Since for our use-case we will also have some users in the UK and
    Australia, we want to take into the considering the distance between our
    primary cluster in the US and enable lower latency for better read
    performance. As such, we will add a Read-only replica in London
    (europe-west2) and Sydney (australia-southeast1). Under the subheading
    "Deploy read-only replicas", select "Add a node" and add these two regions
    with 1 node each.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image27.png)

8.  We can skip the section "Additional settings" by clicking the "NEXT:
    CLUSTER NAME" button since we will keep the default settings.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image35.png)

9.  Under "'Cluster Name', provide a cluster Name." For this demo, we will keep
    the default of "Cluster0". Click on "Create Cluster" button at the bottom of
    the page.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image38.png)

10.  Our cluster is spinning up...

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image36.png)

11. While this spins up, let's click on "Security" tab and then click on
    "Add New User".

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image22.png)

12. Leave the default user as of "admin" and select a secure password. Record
    your user name and password in a safe location for reference later. Under
    "User Privileges", select "Atlas admin" and click on the "Add User" button
    to complete this section.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image16.png)

13.  Once done, we will see screen similar to this...

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image32.png)

14. Under Security tab, select "IP Whitelist" and click on "Add IP Address".

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image26.png)

15. Select "Allow Access from Anywhere" for the purpose of this demo and click
    on "Confirm".  Note:  When actually putting something into production, you
    will want to narrow the scope of where your database can be accessed and
    specify a specific IP address/CIDR block.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image20.png)

16. Go to "Overview" tab and click on "Connect" button.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image42.png)

17. A window will open. Select "Connect Your Application"

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image19.png)

18. Click on "I am using driver 3.4 or earlier" and copy the connection string
    and keep it in a text file. We will be using it in our Node.js application
    to connect to MongoDB Atlas in Part 2 of this document. Close the pop-up
    dialogue

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image40.png)

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image41.png)

## Part 2: Configuring our Google Cloud Platform Account

1.  Go to cloud.google.com and login with your Google account. If you don't have
    a Google account, please create a free trial account by following
    instructions at this [link](https://console.cloud.google.com/freetrial).

2.  If not already there, go to https://console.cloud.google.com/

3.  Create a new project, by selecting the following dropdown in the top left:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image37.png)

4.  A new window will pop up.  In it, select "New Project" in the top left:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image21.png)

5.  Give your Hello World app a new project name and click the "Create" button:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image13.png)

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image46.png)

6.  After your new project is done being created. Go back to the dropdown in
    Step 3, select your new project name:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image4.png)

7.  When the right project is selected, the name will change to reflect this in
    the dropdown in the top left of your console:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image23.png)

8.  Next, let's enable the specific APIs we will need:. Click on
    "APIs & Services" in the left toolbar:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image10.png)

9.  Then select, "ENABLE APIS AND SERVICES":

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image30.png)

10. Select both "Google App Engine Flexible Environment" and "Google App Engine
    Admin API", then select "Enable":

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image39.png)

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image44.png)

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image8.png)

11. Next, lets enable App Engine for our specific language. Use the search bar
    in the console and type in "App Engine". Select "App Engine" from the list
    of options

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image31.png)

12. In the blue box on the left, choose the "Select a language" dropdown:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image29.png)

13. Choose Node.js:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image2.png)

14. Select a region where the majority of your users will be, then select
    "Next":

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image5.png)

15. Close out of the optional tutorial on the right side, by selecting "Cancel
    Tutorial" in the bottom right:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image25.png)

## Part 3: Configuring and deploying our Node.js application

1. Create a Debian Linux GCE VM instance using the instructions given here.

    NOTE: When creating your instance, please be sure to enable "Allow full
    access to all Cloud APIs" under "Identity and API access":

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image33.png)

2. After your instance is created, SSH to your instance by clicking on the SSH button of your instance.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image24.png)

3. You should see a Linux window similar to this open...

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image6.png)

4.  Configure your instance for Node.js and MongoDB client by executing
    following comments.

        sudo apt-get update

        curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -

        sudo apt-get install -y nodejs

        sudo apt-get install -y build-essential

        npm install nconf

5.  Preparing the app - Initialize a package.json file with the following
    command:

        npm init

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image47.png)

    For "package name", enter: "test"

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image34.png)

    - For "version", enter: "1.0.0"
    - For "description", leave blank
    - For "entry point", enter: "server.js"
    - For "test command", leave blank
    - For "git repository", leave blank
    - For "keywords", leave blank
    - For "author", leave blank
    - For "license", leave blank

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image7.png)

    When done, you should see something similar to this...

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image14.png)

    Enter "yes" and press enter

6.  Install dependencies:

        npm install mongodb@2.2.33 --save

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image17.png)

7.  Create a `server.js` file with the following contents by using command.
    NOTE: See the highlighted section where you need to insert your own Atlas
    Connection string.

        nano server.js

    Copy the given code into the Nano editor and save the file using Ctrl + X

        'use strict';

        const mongodb = require('mongodb');
        const http = require('http');
        const nconf = require('nconf');
        let uri = ` PASTE YOUR MONGODB ATLAS CONNECTION STRING HERE `;
        if (nconf.get('mongoDatabase')) {
          uri = `${uri}/${nconf.get('mongoDatabase')}`;
        }
        console.log(uri);

        mongodb.MongoClient.connect(uri, (err, db) => {
          if (err) {
            throw err;
          }

          // Create a simple little server.
          http.createServer((req, res) => {
            if (req.url === '/_ah/health') {
              res.writeHead(200, {
                'Content-Type': 'text/plain'
              });
              res.write('OK');
              res.end();
              return;
            }


            const collection = db.collection('Messages');
            var datetime = new Date();
            const msg = {
              msgDescription: '\nHello World received on ' + datetime
            };

            collection.insert(msg, (err) => {
              if (err) {
                throw err;
              }

              // push out a range
              let msglist = '';
              collection.find().toArray((err, data) => {
                if (err) {
                  throw err;
                }
                data.forEach((msg) => {
                  msglist += `${msg.msgDescription}; `;
                });

                res.writeHead(200, {
                  'Content-Type': 'text/plain'
                });
        res.write('Messages received so far:\n');
                res.end(msglist);
              });
            });
          }).listen(process.env.PORT || 8080, () => {
            console.log('started web process');
          });
        });

    1.  Enter "Exit" to leave
    1.  On prompt to save, enter "Y"
    1.  Keep same file name, Hit Enter

8.  Running our app - Run the app locally by running the following command:

        npm start

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image43.png)

9.  Open another instance of SSH session by repeating the steps listed in X.2
    in the cloud console and run following command

        curl localhost:8080

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image9.png)

## Part 4: Push our application to App Engine Flex on GCP

Deploying the app to App Engine Flex

1.  Create an app.yaml file by running the following command:

        nano app.yaml

2.  Add following content to to app.yaml file by running the following command:

    runtime: nodejs
    env: flex

3.  Run the following command to deploy your app by running the following command:

        gcloud app deploy

4.  View the deployed app by running the following command:

        gcloud app browse

## Part 5: Visit our new application from any web-enabled client terminal; including mobile devices.

1.  Retrieve your external URL from the output of gcloud app browse command:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image28.png)

2.  Use a web-enabled client terminal to visit your new "Hello World"
    application using the external  URL in the previous step. You should see
    webpage showing screen similar to this:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-appengineflex-nodejs-app/image1.png)
