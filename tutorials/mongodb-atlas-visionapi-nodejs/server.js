
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
