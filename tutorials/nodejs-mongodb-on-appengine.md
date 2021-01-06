---
title: Connect to MongoDB from Node.js on App Engine flexible environment
description: Learn how to connect to MongoDB from a Node.js app running on App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, MongoDB
date_published: 2017-11-02
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](/sdk/).
1. [Prepare your environment for Node.js development][nodejs]

### Create a MongoDB database

There are multiple options for creating a new MongoDB database. For example:

- Create a Compute Engine virtual machine with [MongoDB pre-installed](/launcher/?q=mongodb).
- Create a MongoDB instance with [MongoDB Atlas on Google Cloud](https://www.mongodb.com/cloud/atlas/mongodb-google-cloud).
- Use [mLab](https://mlab.com/google/) to create a free MongoDB deployment on Google Cloud.

## Prepare the app

1. Initialize a `package.json` file with the following command:

        npm init

1. Install dependencies:

        npm install --save mongodb nconf

1. Create a `server.js` file with the following contents:

        'use strict';

        const mongodb = require('mongodb');
        const http = require('http');
        const nconf = require('nconf');

        // Read in keys and secrets. Using nconf use can set secrets via
        // environment variables, command-line arguments, or a keys.json file.
        nconf.argv().env().file('keys.json');

        // Connect to a MongoDB server provisioned over at
        // MongoLab.  See the README for more info.

        const user = nconf.get('mongoUser');
        const pass = nconf.get('mongoPass');
        const host = nconf.get('mongoHost');
        const port = nconf.get('mongoPort');

        let uri = `mongodb://${user}:${pass}@${host}:${port}`;
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
            // Track every IP that has visited this site
            const collection = db.collection('IPs');

            const ip = {
              address: req.connection.remoteAddress
            };

            mongodb.MongoClient.connect(uri, { useNewUrlParser: true }, (err, client) => {
              if (err) {
                throw err;
              }
        
             const db = client.db(nconf.get("mongoDatabase"))

              // push out a range
              let iplist = '';
              collection.find().toArray((err, data) => {
                if (err) {
                  throw err;
                }
                // Track every IP that has visited this site
                const collection = db.collection('IPs');

                const ip = {
                  address: req.connection.remoteAddress
                };

                collection.insertOne(ip, (err) => {
                  if (err) {
                    throw err;
                  }

                  // push out a range
                  let iplist = '';
                  collection.find().toArray((err, data) => {
                    if (err) {
                      throw err;
                    }
                    data.forEach((ip) => {
                      iplist += `${ip.address}; `;
                    });

                    res.writeHead(200, {
                      'Content-Type': 'text/plain'
                    });
                    res.write('IPs:\n');
                    res.end(iplist);
                  });
                });

                res.writeHead(200, {
                  'Content-Type': 'text/plain'
                });
                res.write('IPs:\n');
                res.end(iplist);
              });
            });
          }).listen(process.env.PORT || 8080, () => {
            console.log('started web process');
          });
        });

1.  Create a `keys.json` file with the following content, replacing the
    variables with your own values:

        {
          "mongoHost": "YOUR_MONGO_HOST",
          "mongoPort": "YOUR_MONGO_PORT",
          "mongoDatabase": "YOUR_MONGO_DB",
          "mongoUser": "YOUR_MONGO_USERNAME",
          "mongoPass": "YOUR_MONGO_PASSWORD"
        }

    Do not check your credentials into source control. Create a `.gitignore`
    file if you don't have one, and add `keys.json` to it.

## Run the app

1.  Run the app locally:

        npm start

1.  Visit [http://localhost:8080](http://localhost:8080) to see the app.

## Deploy the app

1.  Create an `app.yaml` file with the following content:

        runtime: nodejs
        env: flex

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  View the deployed app:

        gcloud app browse

[mongo]: https://www.mongodb.com/
[nodejs-gcp]: running-nodejs-on-google-cloud
[nodejs]: /nodejs/docs/setup
