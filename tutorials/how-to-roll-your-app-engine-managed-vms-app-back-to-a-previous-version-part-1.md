---
title: How to roll your App Engine flexible environment app back to a previous version
description: Learn how to utilize versions and rollbacks in App Engine flexible environment.
author: jmdobry
tags: App Engine
date_published: 2015-12-18
---

## Disaster scenario

You've deployed an app using App Engine flexible environment, and things
are going great. You make some change to your app and re-deploy, only to
discover that something broke. You forgot a semicolon and now your users are
upset. What do you do?

One option would be to quickly add the semicolon, commit the fix, and deploy
again. Hopefully, your app only suffered a few minutes of downtime, depending on
when you noticed the missing semicolon.

But what if it wasn't just a missing semicolon? What if you just deployed a
major feature and you don't yet know what the problem is? In this scenario, it
might be better to quickly rollback to the stable version of your app that was
running before things broke.

So how do you do that with App Engine flexible environment? A naive approach
might be to search your source control for the last point in time where your
code was stable and re-deploy that code. The pressure of downtime turns such a
search into a nightmare—you could be losing users and dollars by the second.
There must be a better way.

Enter _versions_, a feature of App Engine flexible environment. Every time you
deploy an app, the deployment is associated with a version. If you don't specify
a version, then one will be generated for you.

## Sample app

For this tutorial, you'll make a tiny Hello World Node.js app and deploy it.

Create a file named `server.js` with the following contents:

    const http = require('http');

    const hostname = '127.0.0.1';
    const port = 8080;

    http.createServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('Hello, World!\n');
    }).listen(port, hostname, () => {
      console.log(`Server running at http://${hostname}:${port}/`);
    });

Test it to make sure that it works:

    node server.js

Point your browser to [http://localhost:8080](http://localhost:8080) to see a
`Hello, World!` message. Press CTRL+C to stop the app.

## Deploy

Create a file named `app.yaml` with the following contents:

    runtime: nodejs
    env: flex

This configuration file tells App Engine how to run your app.

Create a file named `package.json` with the following contents:

    {
        "name": "sample-app"
    }

Assuming that you've created a project in the Cloud Console
and installed the Cloud SDK locally, you should be ready to deploy the app.

Run the following command to deploy the app:

    gcloud app deploy

The new deployment should start receiving all traffic, and any previously
deployed version should stop receiving traffic.

View the deployed app at `http://[YOUR_PROJECT_ID].appspot.com/`.

You didn't specify a version with the `--version` flag, so one was generated
automatically. The generated version might look something like `20151005t21174`.
To see the generated version go to this address:

`https://console.developers.google.com/appengine/versions?project=[YOUR_PROJECT_ID]`

There you'll see a list of all deployed versions of your app. The version with
the `(default)` tag next to it is the version that is currently receiving
traffic. You can view any other deployed version at the following URL:

`http://VERSION-dot-[YOUR_PROJECT_ID].appspot.com/`

## Broken deployment

Since you've only deployed once, you probably only see one version. In this section,
you deploy the app again after introducing a bug into the app. 

Find these lines of the `server.js` file:

     res.writeHead(200, { 'Content-Type': 'text/plain' });
     res.end('Hello World!\n');

Edit those two lines to be the following:

    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Error page\n');

This will cause the app to fail to start. 

Deploy the app:

    gcloud app deploy

You should now see two versions listed, the most recent one of which has the
`(default)` tag. Even though the new version is receiving all traffic, the first
version that you deployed is still running and consuming resources. If you visit
`http://[YOUR_PROJECT_ID].appspot.com/` you should see something that suggests
that the app isn't working. Time to roll back.

## Rollback

You don't want to mess around with your code; you need to fix this right now. Users
are upset. Go back to the list of versions and check the box next to the version
that was deployed first. Click the `MAKE DEFAULT` button located above the
list. Traffic immediately switches over to the stable version. Crisis averted.

That was easy.

You can now delete the buggy version by checking the box next to the version
and then clicking the `DELETE` button located above the list.

## Summary

- If you don't specify a version when you a deploy then a version will be
generated for you.
- The `--promote` flag causes a newly deployed version to start receiving all
traffic, and is set by default.
- The `--no-promote` flag causes a newly deployed version to _not_ start receiving
all traffic. Whatever is currently receiving traffic will continue to receive
traffic.
- At any given time, the version with the `(default)` tag is the version
receiving traffic.
- A previously deployed version continues running and consuming resources even
after a new version is deployed and starts receiving traffic. If you want to
avoid the expense of keeping more than one version running, then make sure to
stop previously running versions.
- Switching traffic between versions is as quick and easy as checking a box and
clicking a button. This is only possible if more than one version is running.
- Non-default versions that aren't receiving traffic will idle at the minimum
number of instances configured in your auto-scaling settings (default is 2).
- If you specify a version during deployment that has already been deployed,
then the deployed version will be deleted and the new deployment will take its
place and be assigned the same version.
