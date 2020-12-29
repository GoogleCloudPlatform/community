---
title: Connect to Redis from Node.js on App Engine flexible environment
description: Learn how to connect to Redis from a Node.js app running in the App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Redis
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

## Start a Redis server

There are multiple options for creating a new Redis server:

* [Host](https://cloud.google.com/launcher/?q=redis) a Redis instance on
  Compute Engine.
* Use [Redis Labs](https://app.redislabs.com/#/sign-up/tabs/redis-cloud) to
  create a free Redis-as-a-Service account.

### Using Compute Engine

To use a hosted Redis instance on Compute Engine:

1.  Launch a Compute Engine virtual machine with
    [Redis pre-installed](https://console.cloud.google.com/launcher/details/bitnami-launchpad/redis)
    by Bitnami.
1.  After the virtual machine launches,
    [reserve a regional static IP address](https://console.cloud.google.com/networking/addresses/add).
    Set the IP address region to the location of your Redis virtual machine
    instance. Then, select the instance in the **Attached To** dropdown, and
    click **Reserve**. This IP address is your Redis hostname.
1.  Under your Redis virtual machine instance in
    [Compute Engine](https://console.cloud.google.com/compute/instances), find
    your **Bitnami Base Password** under **Custom Metadata**. Use this as your
    Redis key.
1.  By default, your Redis port number is `6379`. You can verify this by using
    SSH to connect to your Redis virtual machine instance and then typing
    `redis-cli`.
1.  After you have completed these steps, create a configuration file and
    [connect to your hosted Redis instance](#connecting_to_a_redis_server). For
    example:

        {
          "redisHost": "1.2.3.4",
          "redisPort": 6379,
          "redisKey": "bitnami_base_password"
        }

### Using Redis Labs

To create a new Redis instance using Redis Labs:

1.  Create a new Redis subscription.
1.  Choose the cloud `GCE/us-central1`.
1.  Choose the free tier.
1.  Click **select**.
1.  Enter a resource name and password.
1.  Go to **My Resources** &rarr; **Manage** and click on your Redis instance.
    You should see a URL that looks similar to the one below.

        pub-redis-12345.us-central1-2-3.gce.garantiadata.com:12345

    Your Redis hostname consists of everything before the colon, and your Redis
    port number is the number after the colon. Use your Redis table password as
    the `key` value. For example, if your Redis table had a password of
    `password`, the URL above would be configured as follows:

        {
          "redisHost": "pub-redis-12345.us-central1-2-3.gce.garantiadata.com",
          "redisPort": 12345,
          "redisKey": "password"
        }

1.  Using this information, create a configuration file and
    [connect to your Redis Labs instance](#connecting_to_a_redis_server).

## Connecting to a Redis server

### Create a configuration file

Create a JSON file named `keys.json` that contains your Redis host name, port,
and password. Do not check your credentials into source control. Create a
`.gitignore` file if you don't have one, and add `keys.json` to it.

        {
          "redisHost": [YOUR_REDIS_HOSTNAME],
          "redisPort": [YOUR_REDIS_PORT_NUMBER],
          "redisKey": [YOUR_REDIS_PASSWORD]
        }

Replace `[YOUR_REDIS_HOSTNAME]`, `[YOUR_REDIS_PORT_NUMBER]`, and
`[YOUR_REDIS_PASSWORD]` with your Redis hostname, port number, and password
respectively.

### Prepare the application

1.  Initialize a `package.json` file with the following command:

        npm init

1.  Install dependencies:

        npm install --save redis nconf

1.  Create a `server.js` file with the following contents:

        'use strict';

        const redis = require('redis');
        const http = require('http');
        const nconf = require('nconf');

        // Read in keys and secrets. Using nconf use can set secrets via
        // environment variables, command-line arguments, or a keys.json file.
        nconf.argv().env().file('keys.json');

        // Connect to a redis server provisioned over at
        // Redis Labs. See the README for more info.
        const client = redis.createClient(
          nconf.get('redisPort') || '6379',
          nconf.get('redisHost') || '127.0.0.1',
          {
            'auth_pass': nconf.get('redisKey'),
            'return_buffers': true
          }
        ).on('error', (err) => console.error('ERR:REDIS:', err));

        // Create a simple little server.
        http.createServer((req, res) => {
          client.on('error', (err) => console.log('Error', err));

          // Track every IP that has visited this site
          const listName = 'IPs';
          client.lpush(listName, req.connection.remoteAddress);
          client.ltrim(listName, 0, 25);

          // push out a range
          let iplist = '';
          client.lrange(listName, 0, -1, (err, data) => {
            if (err) {
              console.log(err);
              res.status(500).send(err.message);
              return;
            }

            data.forEach((ip) => {
              iplist += `${ip}; `;
            });

            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end(iplist);
          });
        }).listen(process.env.PORT || 8080);

        console.log('started web process');

### Run the app on your local computer

1.  Run the app with the following command:

        npm start

1.  Visit [http://localhost:8080](http://localhost:8080) to see the app.

When you're ready to move forward, press Ctrl+C to stop the local web server.

## Deploy

1.  Create an `app.yaml` file with the following content:

        runtime: nodejs
        env: flex

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  View the deployed app:

        gcloud app browse

[redis]: https://redis.io/
[nodejs-gcp]: running-nodejs-on-google-cloud
[nodejs]: /nodejs/docs/setup
