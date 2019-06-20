---
title: Use Cloud Vision API with MongoDB Atlas
description: Learn how to use the Google Cloud Vision API and MongoDB Atlas to build a metadata database with Express server and Node.js.
author: ksmith,arajwade
tags: Vision API, Node.js, Express, MongoDB Atlas
date_published: 2019-06-20
---

## Overview

This tutorial demonstrates how easy it is to use machine learning to gain additional insights from a batch of 
photos that have no prior metadata attached. By using this workflow, you will be able to quickly build a descriptive 
metadata MongoDB database on Atlas that can be used for a variety of business use cases.

### Objectives

* Create and configure a MongoDB Atlas free tier cluster on Google Cloud Platform (GCP).
* Configure a GCP account.
* Configure a Node.js application on a Compute Engine Debian virtual machine to use the Vision API (labels, landmarks,
  and safe search).
* Start a batch process from a web-enabled client terminal.
* Verify new metadata in the GCP Console and in the MongoDB Atlas database.

## Part 1: Create and configure a MongoDB Atlas free tier cluster on GCP

1.  Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and either sign in to your existing account or 
    click **Try Free** to create a new account. 

1.  Click **Build a Cluster**.

1.  In the **Cloud Provider & Region** section, choose **Google Cloud Platform** and select the region for your
    Atlas cluster. To minimize latency, choose a region close to your end user. For this tutorial, choose a region
    with the **Free Tier Available** label.

    The examples in this tutorial use Iowa (us-central1) in North America.

1.  In the **Cluster Tier** section, accept the default **M0** tier.

1.  Click **Create Cluster** at the bottom of the page.

    The creation of the cluster may take several minutes. While the cluster is being created, you can continue with the
    next setup steps.

1.  Click **Database Access** under the **Security** heading in the menu on the left side of the page. 

1.  Click the **Add New User** button in top-right corner of the page.

1.  Enter a username and password. For this tutorial, use the username `mdbadmin`. Record your username and password
    in a safe location for reference later.
    
1.  In the **User Privileges** section of the **Add New User** dialog box, select **Atlas admin**.

1.  Click the **Add User** button to complete this section.

1.  Click **Network Access** under the **Security** heading in the menu on the left side of the page. 

1.  Click the **Add IP Address** button in top-right corner of the page.

1.  Select **Allow Access from Anywhere** and click **Confirm**.

    Note: When actually putting something into production, you should narrow the scope of where your database
    can be accessed by specifying an IP address or CIDR block.

1.  Click **Clusters** under the **Atlas** heading in the menu on the left side of the page. 

1.  Click the **Connect** button.

1.  In the dialog box that opens, click **Connect Your Application**.

1.  In the **Driver** menu, select **Node.js**.

1.  In the **Version** menu, select **2.2.12 or later**.

1.  Click the **Copy** button to copy the connection string, and save it in a text file. Later in this tutorial, you
    will use this connection string in a Node.js application to connect to MongoDB Atlas.

1.  Click **Close**.

## Part 2: Configure your Google Cloud Platform Account

1.  If you have a Google Account, go to the [GCP Console](https://console.cloud.google.com/) and log in.

    If you don't have a Google Account, [create a free trial account](https://console.cloud.google.com/freetrial).

1.  In the [GCP Console](https://console.cloud.google.com/), click the project selector in the top left.

1.  In the top right corner of the dialog box that appears, click **New Project**.

1.  In the **Project name** field, enter `mongodb-vision-demo`, and click **Create**.

1.  If the new project name isn't shown in the project selector in the top left of the GCP Console, click the project
    selector and select the new project in the dialog box that opens.

## Part 3: Configure a Node.js application on a virtual machine

1.  Follow the the instructions in
    [Create a virtual machine instance](https://cloud.google.com/compute/docs/quickstart-linux#create_a_virtual_machine_instance)
    to create a Debian Linux virtual machine instance on Compute Engine. When creating the instance, select
    **Allow full access to all Cloud APIs** in **Identity and API access > Access scopes** on the
    **Create an instance** page.
    
    Creation of the instance might take more than a minute.

1.  Go to the [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) in the GCP Console.

1.  Click **Create Firewall Rule** at the top of the page, and use the following settings to create a new rule to open
    the port for your new server:
    
    * **Name**: `port8080`
    * **Targets**: **All instances in the network**
    * **Source IP ranges**: For testing, you can enter your public IP address. To determine your public IP address,
      you can use [this search](https://www.google.com/search?q=what+is+my+ip).
    * **Protocols and ports**: Select **Specified protocols and ports**, select **tcp**, and enter `8080` in the **tcp**
      field.

1.  Click **Create**.

1.  Go to the [**VM instances** page](https://console.cloud.google.com/compute/instances).

1.  Click the **SSH** button for your instance to connect to it with SSH and open a Cloud Shell window for the connection.

1.  Install Node.js and Express with the following commands:

        sudo apt-get update
        sudo apt-get install -y nodejs
        sudo apt-get install npm
        curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
        sudo apt-get install -y build-essential
        npm install nconf
        npm install express --save
        npm install mongodb@2.2.33 --save

1.  Install the `vision` library:

        npm install --save @google-cloud/vision
   
1.  Install the `storage` library:

        npm install --save @google-cloud/storage

1.  Enable the Cloud Vision API:

        gcloud services enable vision.googleapis.com

1.  Create a bucket for your project, replacing `[BUCKET_NAME]` with a unique name for your project:

        gsutil mb gs://[BUCKET_NAME]
        
    Note: A bucket must have a globally unique name to be accepted.

1.  Make the bucket public:

        gsutil defacl set public-read gs://[BUCKET_NAME]

1.  Go to the [**Storage** page](https://console.cloud.google.com/storage) and select your bucket.

1.  Add a few sample images to the bucket for the demonstration server to process. To add images to a bucket, you
    can use the **Upload** buttons or drag and drop images to the bottom of the **Storage** page.   

1.  Switch back to the Cloud Shell window and create a new folder:

        mkdir nodejs-express-mongodb

1.  Change directory to this folder:

        cd nodejs-express-mongodb

### Prepare the app

1.  Initialize a `package.json` file with the following command:

        npm init
                
    Set up a new project. You can press enter to accept the default settings, but when you get to the entry point,
    type in `server.js`. 
    
    Enter `yes` when prompted, and press Enter.

1.  Create a public folder for your server and enter the new folder with following commands:

        mkdir public
        cd public

1.  Open a text editor to create the client-side file:

        nano client.js

1. Copy and paste the following script content into the text editor:

        console.log('Client-side code running');
        const button = document.getElementById('myButton');
        button.addEventListener('click', function(e) {
          console.log('Vision API Trigger button  was clicked');
          fetch('/clicked', {method: 'POST'})
            .then(function(response) {
              if(response.ok) {
                console.log('Label was recorded');
                return;
              }
              throw new Error('Request failed.');
            })
            .catch(function(error) {
              console.log(error);
            });
        });
        setInterval(function() {
          fetch('/clicks', {method: 'GET'})
            .then(function(response) {
              if(response.ok) return response.json();
              throw new Error('Request failed.');
            })
            .then(function(data) {
              document.getElementById('counter').innerHTML = `Number of total files processed ${data.length}`;
            })
            .catch(function(error) {
              console.log(error);
            });
        }, 1000);

1. Press Ctrl+X to save the file.

1.  Open a text editor to create the web server home page:

        nano index.html

1.  Copy and paste the following web page content into the text editor:

        <!DOCTYPE HTML>
        <html>
          <head>
            <title>Gaining ML insight with the Cloud Vision API and MongoDB Atlas</title>
          </head>
          <body>
            <div style="text-align:center;">
              <meta charset='utf-8'><meta charset="utf-8"><b style="font-weight:normal;"><p><p><p><p><p><p><p><p><p><p><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#3C4043;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">DEMO: Gaining </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#FBBC05;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">ML insight</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#3C4043;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> with </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#4285F4;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">Google Vision API</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#3C4043;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> and </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#34A853;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">MongoDB</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#4285F4;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#000000;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">on</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#4285F4;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#EA4335;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">Google Cloud</span></b><p><p>    <p><p><p>

              <button id="myButton">Trigger batch Vision API job!</button>
            </div>
          </body>
          <script src="client.js"></script>    
        </html>

1. Press Ctrl+X to save the file.

1.  Navigate back to your `nodejs-express-mongodb` folder:

        cd ..

1.  Open a text editor to create the server-side file:

        nano server.js

1.  Copy and paste the following script content into the text editor, replacing `[BUCKET_NAME]` with the name that you
    gave to your bucket previously and replacing `[MONGODB_ATLAS_CONNECTION_STRING]` with the connection string that you
    saved previously. Be sure to edit your connection string with your database password.  

        console.log('Server-side code running');
        const express = require('express');
        const MongoClient = require('mongodb').MongoClient;
        const app = express();
        const gcpbucket = 'gs://[BUCKET_NAME]';
        var strOutput;
        var strOutput2;
        var strOutput3;
        
        // serve files from the public directory
        app.use(express.static('public'));
        
        // connect to the db and start the express server
        let db;
        
        // Replace the URL below with the URL for your database
        const url =  '[MONGODB_ATLAS_CONNECTION_STRING]';
        
        MongoClient.connect(url,(err, database) => {
          if(err) {
            return console.log(err);
          }
          console.log('Successfully connected to MongoDB Atlas');
          db = database;
          
          // start the express web server listening on 8080
          app.listen(8080, () => {
            console.log('listening on 8080');
            console.log('Input GCP bucket is set to ' + gcpbucket);
          });
        });
        
        // serve the homepage
        app.get('/', (req, res) => {
          res.sendFile(__dirname + '/index.html');
        });
        
        // add a document to the DB collection recording the click event
        app.post('/clicked', (req, res) => {
          listFiles(gcpbucket);  
          res.sendStatus(201);
        });
        
        // get the click data from the database
        app.get('/clicks', (req, res) => {
          db.collection('clicks').find().toArray((err, result) => {
            if (err) return console.log(err);
            res.send(result);
          });
        });
        
        async function detectLandmark(fileName3) {
        
          // [START vision_landmarks_detection]
          
          // Imports the Google Cloud client library
          const vision = require('@google-cloud/vision').v1p1beta1;
          
          // Creates a client
          const client = new vision.ImageAnnotatorClient();
          
          // Performs safe search detection on the local file
          const [result] = await client.landmarkDetection(fileName3);
          const landmarks = result.landmarkAnnotations;
          console.log(fileName3);
          console.log('Landmarks:');
          strOutput3 = fileName3  + "  " + '\n' ;
          landmarks.forEach(landmark => {
          console.log(landmark);
          strOutput3 =  strOutput3 + "  " + "Description:" + landmark.description + "  " + "Score: " + landmark.score + "  " + '\n';
          });
          
          const click3 = {visionAPIResult: strOutput3};
          console.log(click3);
          
          db.collection('Landmarks').save(click3, (err, result) => {
            if (err) {
              return console.log(err);
            }
            console.log('Vision API Landmarks added to MongoDB Atlas Cluster');
            //  res.sendStatus(201);
          });
          
          // [END vision_landmarks_detection]
        }
        
        async function detectSafeSearch(fileName2) {
        
          // [START vision_safe_search_detection]

          // Imports the Google Cloud client library
          const vision = require('@google-cloud/vision').v1p1beta1;

          // Creates a client
          const client = new vision.ImageAnnotatorClient();

          // Performs safe search detection on the local file
          const [result] = await client.safeSearchDetection(fileName2);
          const detections = result.safeSearchAnnotation;
          console.log(fileName2);
          console.log('Safe search:');
          console.log(`Adult: ${detections.adult}`);
          console.log(`Medical: ${detections.medical}`);
          console.log(`Spoof: ${detections.spoof}`);
          console.log(`Violence: ${detections.violence}`);
          console.log(`Racy: ${detections.racy}`);
          strOutput2 = fileName2  + "  " + '\n' ;
          strOutput2 = strOutput2 + "  " + "Adult:"  + detections.adult + "  " + '\n' + "  " + "Medical:" + detections.medical + "  " + '\n' + "  " + "Spoof:" + detections.spoof + "  " + '\n' + "  " + "Violence:" + detections.violence + "  " + '\n' + "  " + "Racy:" + detections.racy + "  " + '\n';

          const click2 = {visionAPIResult: strOutput2};
          console.log(click2);
          
        db.collection('SafeSearch').save(click2, (err, result) => {
            if (err) {
              return console.log(err);
            }
            console.log('Vision API SafeSearch labels added to MongoDB Atlas Cluster');
            
          //  res.sendStatus(201);
            });
            
          // [END vision_safe_search_detection]
        }

        async function detectFulltext(fileName) {

          // Imports the Google Cloud client library
          const vision = require('@google-cloud/vision');
 
          // Creates a client
          const client = new vision.ImageAnnotatorClient();

          // Performs label detection on the image file
          const [result] = await client.labelDetection(fileName);
          const labels = result.labelAnnotations;
          console.log(fileName);
          strOutput = fileName + "  " + '\n' ;
          labels.forEach(label => {
            console.log(label.description);
            console.log(label.score);
            strOutput = strOutput + label.description + "  " + label.score + "  " + '\n';
          });
          const click = {visionAPIResult: strOutput};
          console.log(click);
          // console.log(db);
          db.collection('Labels').save(click, (err, result) => {
            if (err) {
              return console.log(err);
            }
            console.log('Vision API output labels  added to MongoDB Atlas Cluster');
            //  res.sendStatus(201);
          });
        }

        async function listFiles(bucketName) {
        
          // Imports the Google Cloud client library
          const {Storage} = require('@google-cloud/storage');

          // Creates a client
          const storage = new Storage();

          // Lists files in the bucket
          const [files] = await storage.bucket(bucketName).getFiles();
          console.log('Files:');
          files.forEach(file => {
            // Performs label detection on the image file
            var  fileName = file.name;
            detectFulltext(bucketName + '/'  + fileName);

            // Performs Safe Search on the image file
            var  fileName2 = file.name;
            detectSafeSearch(bucketName + '/'  + fileName2);

            // Performs Landmarks on the image file
            var  fileName3 = file.name;
            detectLandmark(bucketName + '/'  + fileName3);
          });
        }

### Run the app

From the `nodejs-express-mongodb` directory, run `server.js`:

    node server.js

## Part 4: Start the batch process from a web-enabled client terminal

1.  Go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances) in the GCP Console. Your external
    IP address is listed next to your instance.

2.  Use a web-enabled client terminal to visit your new application using the external URL in the previous step, and specify
    port 8080.   You should see a webpage similar to this:

    ![image](images/image25.png)

## Part 5: Verify your new metadata in both the GCP Console and the MongoDB Atlas database

Click the **Trigger batch Vision API job** button to start the job. You should see a flurry of results in the Cloud 
Shell SSH window as the job processes your Cloud Storage bucket for images. Here is an example when done:

![image](images/image35.png)

Switch to your MongoDB Atlas cluster and verify the results. Success! Enjoy your new ML keywords!

![image](images/image40.png)
