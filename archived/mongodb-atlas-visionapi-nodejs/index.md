---
title: Use the Vision API with MongoDB Atlas
description: Learn how to use the Cloud Vision API and MongoDB Atlas to build a metadata database with Express server and Node.js.
author: ksmith,arajwade
tags: Vision API, Node.js, Express, MongoDB Atlas
date_published: 2019-06-24
---

Kent Smith and Abhijeet Rajwade | Customer Engineers | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how easy it is to use machine learning to gain additional insights from a batch of 
photos that have no prior metadata attached. By using this workflow, you will be able to quickly build a descriptive 
metadata MongoDB database on Atlas that can be used for a variety of business use cases.

## Objectives

* Create and configure a MongoDB Atlas free tier cluster on Google Cloud.
* Configure a Google Cloud account.
* Configure a Node.js application on a Compute Engine Debian virtual machine to use the Vision API (labels, landmarks,
  and safe search).
* Start a batch process from a web-enabled client terminal.
* Verify new metadata in the Cloud Console and in the MongoDB Atlas database.

## Part 1: Create and configure a MongoDB Atlas free tier cluster on Google Cloud

**Step 1**: Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and either sign in to your existing account or 
click **Try Free** to create a new account.
    
![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image1.png)

**Step 2**: Click **Build a Cluster**.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/imageXX.png)

**Step 3**: In the **Cloud Provider & Region** section, choose **Google Cloud Platform** and select the region for your
Atlas cluster. To minimize latency, choose a region close to your end user. For this tutorial, choose a region
with the **Free Tier Available** label.

The examples in this tutorial use Iowa (us-central1) in North America.
    
![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image15.png)

**Step 4**: In the **Cluster Tier** section, accept the default **M0** tier.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image13.png)

**Step 5**: Click **Create Cluster** at the bottom of the page.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image32.png)

The creation of the cluster may take several minutes. While the cluster is being created, you can continue with the
next setup steps.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image12.png)

**Step 6**: Click **Database Access** under the **Security** heading in the menu on the left side of the page. 

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image33.png)

**Step 7**: Click the **Add New User** button in top-right corner of the page.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image24.png)

**Step 8**: Enter a username and password. For this tutorial, use the username `mdbadmin`. Record your username and password
in a safe location for reference later.

**Step 9**: In the **User Privileges** section of the **Add New User** dialog box, select **Atlas admin**.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image9.png)

**Step 10**: Click the **Add User** button to complete this section.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image23.png)

**Step 11**: Click **Network Access** under the **Security** heading in the menu on the left side of the page. 

**Step 12**: Click the **Add IP Address** button in top-right corner of the page.

**Step 13**: Select **Allow Access from Anywhere** and click **Confirm**.

When actually putting something into production, you should narrow the scope of where your database
can be accessed by specifying an IP address or CIDR block.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image4.png)

**Step 14**: Click **Clusters** under the **Atlas** heading in the menu on the left side of the page. 

**Step 15**: Click the **Connect** button.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image6.png)

**Step 16**: In the dialog box that opens, click **Connect Your Application**.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image20.png)

**Step 17**: In the **Driver** menu, select **Node.js**.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image11.png)

**Step 18**: In the **Version** menu, select **2.2.12 or later**.

**Step 19**: Click the **Copy** button to copy the connection string, and save it in a text file. Later in this tutorial, you
will use this connection string in a Node.js application to connect to MongoDB Atlas.

**Step 20**: Click **Close**.

## Part 2: Configure your Google Cloud account

**Step 1**: If you have a Google Account, go to the [Cloud Console](https://console.cloud.google.com/) and log in.

If you don't have a Google Account, [create a free trial account](https://console.cloud.google.com/freetrial).

**Step 2**: In the [Cloud Console](https://console.cloud.google.com/), click the project selector in the top left.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image30.png)

**Step 3**: In the top right corner of the dialog box that appears, click **New Project**.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image14.png)

**Step 4**: In the **Project name** field, enter `mongodb-vision-demo`, and click **Create**.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image28.png)

**Step 5**: The active project is shown in the project selector in the top left of the Cloud Console.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image5.png)

**Step 6**: If the new project name isn't shown in the project selector in the top left of the Cloud Console, click the project
selector and select the new project in the dialog box that opens.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image22.png)

## Part 3: Configure a Node.js application on a virtual machine

**Step 1**: Follow the the instructions in
[Create a virtual machine instance](https://cloud.google.com/compute/docs/quickstart-linux#create_a_virtual_machine_instance)
to create a Debian Linux virtual machine instance on Compute Engine. When creating the instance, select
**Allow full access to all Cloud APIs** in **Identity and API access > Access scopes** on the
**Create an instance** page.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image3.png)

Creation of the instance might take more than a minute.

**Step 2**: Go to the [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) in the Cloud Console.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image18.png)  

**Step 3**: Click **Create Firewall Rule** at the top of the page, and use the following settings to create a new rule to open
the port for your new server:

* **Name**: `port8080`
* **Targets**: **All instances in the network**
* **Source IP ranges**: For testing, you can enter your public IP address. To determine your public IP address,
you can use [this search](https://www.google.com/search?q=what+is+my+ip).
* **Protocols and ports**: Select **Specified protocols and ports**, select **tcp**, and enter `8080` in the **tcp**
field.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image38.png)

**Step 4**: Click **Create**.

**Step 5**: Go to the [**VM instances** page](https://console.cloud.google.com/compute/instances).

**Step 6**: Click the **SSH** button for your instance to connect to it with SSH.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image16.png)

This opens a Cloud Shell window for the connection.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image7.png)

**Step 7**: Install Node.js and Express with the following commands:

    sudo apt-get update
    sudo apt-get install -y nodejs
    sudo apt-get install npm
    curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
    sudo apt-get install -y build-essential
    npm install nconf
    npm install express --save
    npm install mongodb@2.2.33 --save

**Step 8**: Install the `vision` library:

    npm install --save @google-cloud/vision
   
**Step 9**: Install the `storage` library:

    npm install --save @google-cloud/storage

**Step 10**: Enable the Vision API:

    gcloud services enable vision.googleapis.com

**Step 11**: Create a bucket for your project, replacing `[BUCKET_NAME]` with a unique name for your project:

    gsutil mb gs://[BUCKET_NAME]
 
A bucket must have a globally unique name to be accepted.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image26.png)

**Step 12**: Make the bucket public:

    gsutil defacl set public-read gs://[BUCKET_NAME]

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image29.png)

**Step 13**: Go to the [**Storage** page](https://console.cloud.google.com/storage) and select your bucket.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image36.png)

**Step 14**: Add a few sample images to the bucket for the demonstration server to process. To add images to a bucket, you
can use the **Upload** buttons or drag and drop images to the bottom of the **Storage** page.  

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image8.png)

**Step 15**: Switch back to the Cloud Shell window and create a new folder:

    mkdir nodejs-express-mongodb

**Step 16**: Change directory to this folder:

    cd nodejs-express-mongodb

### Prepare the app

**Step 1**: Initialize a `package.json` file with the following command:

    npm init

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image21.png)

Set up a new project. You can press enter to accept the default settings, but when you get to the entry point,
type in `server.js`. 

Enter `yes` when prompted, and press Enter.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image17.png)

**Step 2**: Create a public folder for your server and enter the new folder with following commands:

    mkdir public
    cd public

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image2.png)

**Step 3**: Open a text editor to create the client-side file:

    nano client.js

**Step 4**: Copy and paste the following script content into the text editor:

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

**Step 5**: Press Ctrl+X to save the file.

**Step 6**: Go to the
[source repository](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/mongodb-atlas-visionapi-nodejs/src) for
this tutorial, open the `index.html` file, and copy the contents of that file to the clipboard.

**Step 7**: Open a text editor to create the web server home page:

    nano index.html

**Step 8**: Paste the contents of the source file into the new file, and press Ctrl+X to save the new file.

**Step 9**: Navigate back to your `nodejs-express-mongodb` folder:

    cd ..

**Step 10**: Open a text editor to create the server-side file:

    nano server.js

**Step 11**: Copy and paste the following script content into the text editor, replacing `[BUCKET_NAME]` with the name that you
gave to your bucket previously and replacing `[MONGODB_ATLAS_CONNECTION_STRING]` with the connection string that you
saved previously. Be sure to edit your connection string with your database password.  
    
    console.log('Server-side code running');
    
    const express = require('express');
    const MongoClient = require('mongodb').MongoClient;
    const app = express();
    const gcpbucket = 'gs://demo-visionapi-atlas';
    var strOutput;
    var strOutput2;
    var strOutput3;
    
    // serve files from the public directory
    app.use(express.static('public'));

    // connect to the db and start the express server
    let db;

    // Replace the URL below with the URL for your database
    const url =  'mongodb://mdbadmin:Mdbdemo2019@cluster0-shard-00-00-2oe94.gcp.mongodb.net:27017,cluster0-shard-00-01-2oe94.gcp.mongodb.net:27017,cluster0-shard-00-02-2oe94.gcp.mongodb.net:27017/ML_Keywords?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority';

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

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image34.png)

## Part 4: Start the batch process from a web-enabled client terminal

**Step 1**: Go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances) in the Cloud Console. Your external
IP address is listed next to your instance.

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image37.png)

**Step 2**: Use a web-enabled client terminal to visit your new application using the external URL in the previous step, and specify
port 8080. You should see a webpage similar to this:

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image25.png)

## Part 5: Verify your new metadata in both the Cloud Console and the MongoDB Atlas database

Click the **Trigger batch Vision API job** button to start the job. You should see a flurry of results in the Cloud 
Shell SSH window as the job processes your Cloud Storage bucket for images. Here is an example when done:

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image35.png)

Switch to your MongoDB Atlas cluster and verify the results. Success! Enjoy your new ML keywords!

![image](https://storage.googleapis.com/gcp-community/tutorials/mongodb-atlas-visionapi-nodejs/image40.png)
