---
title: Google Vision API and MongoDB Atlas on Google Cloud
description: Learn how to use Google's Vision API and MongoDB Atlas to build a metadata database with Express server and Node.js.
author: ksmith, arajwade
tags: Vision API, Node.js, express, MongoDB Atlas
date_published: 2019-06-18
---

## Overview

In this tutorial, we will demonstrate how easy it is to use Machine Learning to gain additional insights from a batch of photos that have no prior metadata attached.  By using this workflow, we will be able to quickly build a descriptive metadata MongoDB database on Atlas that can be leveraged for a variety of business use-cases.


### Technical Complecity

Beginner

### Duration

45 Minutes

### Objectives

1.  Create and configure MongoDB Atlas Free-Tier cluster on GCP
2.  Configuring our Google Cloud Platform Account.
3.  Configure a Node JS application on a GCE Debian VM to use Vision API 
    (labels,landmarks and safe search)
4.  Kick off the batch process from any web-enabled client terminal
5.  Verify our new metadata in both the console and in our MongoDB Atlas database

## Part 1: Create and configure MongoDB Atlas Free-Tier cluster on GCP

1.  Create a free account on MongoDB Atlas on www.mongodb.com/cloud/atlas
    Click on “Try Free”at the top right if you do not have an account or “Sign In” if you already have a login. 

    ![image](images/image1.png)

2.  Once on the MongoDB Atlas Homepage, select “Build a Cluster”

    ![image](images/imageXX.png)

3.  Create New Cluster by selecting Google Cloud Platform as a “Cloud Provider”.

    Next select the region where you want to place your Atlas cluster.  Ideally, your cluster will be located close to your end user for lower latency.

    Note that we can select a free tier region in your area of choice, as noted by the “Free Tier Available” icon  This is a no-cost option to get started.

    As such, we will select our primary region to be in North America, based in Iowa (us-central1) since it is the closest Free Tier option, at time of writing.

    ![image](images/image15.png)

4.  Next, let's configure our cluster size under “Cluster Tier”.  We will take the default tier of “M0” since it is a free, no cost option.

    ![image](images/image13.png)

5.  We can skip the section “Additional settings” and “Cluster Name”. For this demo, we will keep the default of “Cluster0”. Click on “Create Cluster” button at the bottom of the page.

    ![image](images/image32.png)

6.  Our cluster is spinning up…

    ![image](images/image12.png)

7.  While this spins up, lets click on the “Database Access” submenu, under “Security” on the left menu. 

    ![image](images/image33.png)

8.  Please click the “Add New User” button on top right

    ![image](images/image24.png)

9.  Enter a user name. For our demo, let’s enter “mdbadmin” and enter a secure password.  Record your user name and password in a safe location for reference later. Under “User Privileges”, select “Atlas admin” and click on the “Add User” button to complete this section.

    ![image](images/image9.png)

10. Once done, we will see a screen similar to this…

    ![image](images/image23.png)

11. Lets click on the “Network Access” submenu, under “Security” on the left menu. Click on “Add IP Address”.

    ![image](images/image39.png)

12. Select “Allow Access from Anywhere” for the purpose of this demo and click on “Confirm”.  

Note:  When actually putting something into production, you will want to narrow the scope of where your database can be accessed and specify a specific IP address/CIDR block.

    ![image](images/image4.png)

13. Go to “Clusters” submenu, under “Atlas” on the left menu. Click on “Connect” button.

    ![image](images/image6.png)

14. A window will open. Select “Connect Your Application”

    ![image](images/image20.png)

15. For step 1, choose “Node.js” for Driver and Version “2.2.12 or later”. For step 2, copy the connection string and keep it in a text file. We will be using it in our node JS application to connect to MongoDB Atlas in a later part of this document.

    Close the pop-up dialogue

    ![image](images/image11.png)

## Part 2: Configuring our Google Cloud Platform Account

1.  Go to cloud.google.com and login with your Google account. If you don't have
    a Google account, please create a free trial account by following
    instructions at this [link](https://console.cloud.google.com/freetrial).

2.  If not already there, go to https://console.cloud.google.com/

3.  Create a new project, by selecting the following dropdown in the top left:

    ![image](images/image30.png)

4.  A new window will pop up.  In it, select "New Project" in the top right:

    ![image](images/image14.png)

5.  Give your Vision API demo a new project name.  Let's go with “mongodb-vision-demo” and click the “Create” button:

    ![image](images/image28.png)

    ![image](images/image31.png)

6.  After your new project is done being created. Go back to the dropdown in
    Step 3, select your new project name:

    ![image](images/image22.png)

7.  When the right project is selected, the name will change to reflect this in the dropdown in the top left of your console:

    ![image](images/image5.png)

## Part 3: Configure a Node JS application on a GCE Debian VM on GCP

1. Create a Debian Linux GCE VM instance using the instructions given here [link](https://www.google.com/url?q=https://cloud.google.com/compute/docs/quickstart-linux&sa=D&ust=1560383195254000)

    NOTE:  When creating your instance, please be sure to enable “Allow full access to all Cloud APIs” under “Access scopes”

    ![image](images/image3.png)

2. In the search box at the top, enter “Firewall” and select the matching suggestion”Firewall rules”under “VPC network”

    ![image](images/image19.png)

3.  Click “Create Firewall Rule” at the top to create a new rule to open up the needed port for our new server

    ![image](images/image18.png)

4.  Enter the following details and click “Create”:

        Name: port8080
        Targets: All instances in the network
        Source IP ranges:   [your specific source IP / range]  For testing, you can enter your IP using the Google search “what is my ip”.
        Protocols and ports:  
            tcp: 8080
        
    ![image](images/image38.png)

5.  In the search field up top, enter “compute engine” and select the suggestion:

    ![image](images/image27.png)

6.  After your instance is created, SSH to your instance by clicking on the SSH button of your instance.

    ![image](images/image16.png)

7.  You should see a CloudShell window similar to this open...

    ![image](images/image7.png)

8.  Install Node JS and Express by executing following commands:

        sudo apt-get update
        sudo apt-get install -y nodejs
        sudo apt-get install npm
        curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
        sudo apt-get install -y build-essential
        npm install nconf
        npm install express --save
        npm install mongodb@2.2.33 --save

9.  Install vision library:

        npm install --save @google-cloud/vision
   
10. Install storage library:

        npm install --save @google-cloud/storage

11. Enable cloud vision API:

        gcloud services enable vision.googleapis.com

12. Create bucket with a name for your project.  Replace [bucketname] with your unique name.  Note buckets have to have a globally unique name to be accepted:

        gsutil mb gs://[bucketname]

        ![image](images/image26.png)        

13. Make bucket public:

        gsutil defacl set public-read gs://[bucketname]

        ![image](images/image29.png)   

14. Let's switch back to the console and navigate to our new Google Cloud Storage bucket, by entering “Storage” in the search query and selecting the recommendation.  
    Please verify your new bucket exists and select it
    
    ![image](images/image36.png)

15. Once selected, you can drag and drop a few sample images for our demo server to process:   

    ![image](images/image8.png)

    ![image](images/image10.png)    

16. Switch back to your SSH window and lets create a folder named: “nodejs-express-mongodb”:

        mkdir nodejs-express-mongodb

17. Change directory to this folder:

        cd nodejs-express-mongodb

18. Preparing the app

        1.  Initialize a package.json file with the following command:

                npm init

                ![image](images/image21.png)

            Setup a new node project. You can press enter to accept the default settings, but when you get to entry point, type in “server.js” 

                ![image](images/image17.png)

            Enter “yes” when prompted and press enter

        2.  We need to create a public folder for our server and select it, by entering the following commands:

                mkdir public
                cd public

                ![image](images/image2.png)

        3.  Let’s create the client side file using the following command and copying the following script content into the editor. Save the file using Ctrl + X:

                nano client.js

                        ****************************************

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
                        ****************************************

        4.  Let’s create the web server home page using the following command and entering the following script content into the editor. Save the file using Ctrl + X:

                nano index.html

                         ****************************************
                        <!DOCTYPE HTML>

                        <html>

                        <head>

                            <title>Gaining ML insight with Google Vision API and MongoDB Atlas</title>

                        </head>

                        <body>

                        <div style="text-align:center;">

                         <meta charset='utf-8'><meta charset="utf-8"><b style="font-weight:normal;"><p><p><p><p><p><p><p><p><p><p><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#3C4043;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">DEMO: Gaining </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#FBBC05;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">ML insight</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#3C4043;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> with </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#4285F4;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">Google Vision API</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#3C4043;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> and </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#34A853;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">MongoDB</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#4285F4;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#000000;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">on</span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#4285F4;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;"> </span><span style="font-size:36pt;font-family:'Google Sans',sans-serif;color:#EA4335;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">Google Cloud</span></b><p><p>    <p><p><p>

                           

                            <button id="myButton">Trigger batch Vision API job!</button>

                          </div>

                          </body>

                          <script src="client.js"></script>    

                        </html>
                         ****************************************

        5.  Navigate back to your “nodejs-express-mongodb” folder and let’s create the server side file with the following commands and script contents. Save the file using Ctrl + X :

        NOTE:  See the sections where you need to enter your GCS bucket name previously created and your Atlas Connection string. Do not forget to edit your connection string with your DB password.  

                cd ..
                nano server.js                      

                        ****************************************
                        console.log('Server-side code running');

                        const express = require('express');

                        const MongoClient = require('mongodb').MongoClient;

                        const app = express();

                        const gcpbucket = 'gs://[INSERT YOUR GCS BUCKET NAME]';

                        var strOutput;

                        var strOutput2;

                        var strOutput3;

                        // serve files from the public directory

                        app.use(express.static('public'));

                        // connect to the db and start the express server

                        let db;

                        // Replace the URL below with the URL for your database

                        const url =  '[INSERT YOUR MONGODB ATLAS CONNECTION STRING]';

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
                        ****************************************

19. Running our app. From nodejs-express-mongodb directory run server.js

    node server.js

    ![image](images/image34.png)

## Part 4: Kick off the batch process from any web-enabled client terminal

1.  Switch back to the console view to look at  “VM Instances” under “Compute Engine”.  Our external IP address is listed next to our instance.

    ![image](images/image37.png)

2.  Use a web-enabled client terminal to visit your new application using the external  URL in the previous step and specify port 8080.   You should see a webpage similar to this:

    ![image](images/image25.png)

## Part 5: Verify our new metadata in both the conole and in our MongoDB Atlas database

1.  While monitoring your SSH console window, click on the “Trigger batch Vision API job” button to kick off our job.  If correct, you should see a flurry of results as it combs through your GCS bucket for images within seconds.  Here is an example when done:

    ![image](images/image35.png)

2.  Let’s switch over to our MongoDB Atlas cluster and verify our results.  Success!  Enjoy your new ML keywords!

    ![image](images/image40.png)
