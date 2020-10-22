---
title: Monitoring Ghost on App Engine flexible environment - part 2
description: Learn how to monitor a Ghost blog running on App Engine flexible environment.
author: jmdobry
tags: App Engine, Ghost, Node.js, Stackdriver
date_published: 2016-05-26
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how to monitor a [Ghost blog][ghost] deployed on
[App Engine flexible environment][flex].

## Objectives

* Understand Cloud Monitoring with Ghost.
* Understand Cloud Logging with Ghost.
* Activate Cloud Trace.

## Before you begin

Complete the tutorial [Ghost on App Engine Part 1 - Deploying][deploying].

## Understanding Cloud Monitoring

Monitoring is powered by [Cloud Monitoring][monitoring].

You don't have to install the monitoring agent on App Engine flexible
environment because Cloud Monitoring support is built-in.

You can [view the monitoring dashboard][mon_dash] for your Ghost blog in the
Cloud Console.

[monitoring]: https://cloud.google.com/monitoring/
[mon_dash]: https://app.google.stackdriver.com/services/app-engine/

## Understanding Cloud Logging

Logging is powered by [Cloud Logging][logging].

You don't have to install the logging agent on Google App Engine Flexible
Environment because Cloud Logging support is built-in. See
[Cloud Logging in App Engine Apps for more information][logging].

You can [view the logs][logs] for your Ghost blog in the Cloud Console.

[logging]: https://cloud.google.com/logging/
[gae_logging]: https://cloud.google.com/appengine/articles/logging
[logs]: https://console.cloud.google.com/logs?service=appengine.googleapis.com

## Using Cloud Trace

Tracing of HTTP requests and RPC calls in your Ghost blog is powered by
[Cloud Trace][trace].

To begin tracing what goes on in your Ghost blog you must import the
[Node.js trace agent][trace_agent] into the application.

[trace]: https://cloud.google.com/trace/
[trace_agent]: https://github.com/GoogleCloudPlatform/cloud-trace-nodejs

### Enable Trace

1.  To install the `@google-cloud/trace-agent` module during deployment, edit the `package.json` file and add a `postinstall` script:

        "scripts": {
          "preinstall": "...",
          "postinstall": "npm install @google-cloud/trace-agent",
          "start": "...",
          "test": "..."
        }
  
    We use a `postinstall` script because it allows us to avoid messing with
    Ghost's `npm-shrinkwrap.json` file.

1.  Create a `trace.js` file with the following contents:

        if (process.env.NODE_ENV === 'production') {
          require('@google-cloud/trace-agent').start({
            enhancedDatabaseReporting: true
          });
        }
 
1.  To start Cloud Trace when the deployed application starts, the `@google-cloud/trace-agent` module
    must be imported as the very first thing the application does. Add the following to
    the _very first line_ of `index.js`:

        require('./trace');

    The application will now use Cloud Trace when it is deployed to App
    Engine.

1.  Re-deploy the application:

        gcloud app deploy

1.  After a few minutes, activity in your application causes traces to appear in
    the [Trace Dashboard][trace_dashboard].

[trace_dashboard]: https://console.cloud.google.com/traces/traces

## Error Reporting

Error reporting in your Ghost blog is powered by [Cloud Error Reporting][errorreporting].

Error reporting works by capturing logs written to a certain location. We will
use the [winston][winston] library to write the logs to the right location.

[winston]: https://github.com/winstonjs/winston

### Enable Error Reporting

1.  To install the `winston` module during deployment, edit the `package.json` file
    and add `winston` to the `postinstall` script you added earlier:

        "scripts": {
          "preinstall": "...",
          "postinstall": "npm install @google-cloud/trace-agent winston",
          "start": "...",
          "test": "..."
        }

1.  Create an `errorreporting.js` file with the following contents:

        var logFile = '/var/log/app_engine/custom_logs/ghost.errors.log.json';
        var winston = require('winston');

        winston.add(winston.transports.File, {
          filename: logFile
        });

        function report (err, req) {
          var payload = {
            serviceContext: {
              service: 'ghost'
            },
            message: err ? err.stack : '',
            context: {
              httpRequest: {
                url: req.originalUrl,
                method: req.method,
                referrer: req.header('Referer'),
                userAgent: req.header('User-Agent'),
                remoteIp: req.ip,
                responseStatusCode: 500
              }
            }
          };
          winston.error(payload);
        }

        function skip (req, res) {
          if (res.statusCode >= 400) {
            report(null, req);
          }
          return false
        }

        exports.logging = {
          skip: skip
        };

1.  To start collecting errors when the deployed application starts, the error
    reporting code needs to be added to the Express application. Add the following
    `logging` setting to `config.json`:

        production: {
          // Other settings hidden

          logging: require('./errorreporting').logging
        }
  
1.  Re-deploy the application:

        gcloud app deploy

1.  Any request errors will now be reported in the [Error Reporting Dashboard][error_dashboard].

[errorreporting]: https://cloud.google.com/error-reporting/
[error_dashboard]: https://console.cloud.google.com/errors

## Debugging

Debugging your Ghost blog is powered by [Cloud Debugger][debugger].

To make Cloud Debugger available to your Ghost blog you must import the
[Node.js debugger agent][debugger_agent] into the application.

### Enable Cloud Debugger

1.  To install the `@google-cloud/debug-agent` module during deployment, edit the
    `package.json` file and add `@google-cloud/debug-agent` to the `postinstall` script
    you added earlier:

        "scripts": {
          "preinstall": "...",
          "postinstall": "npm install @google/cloud-trace winston @google-cloud/debug-agent",
          "start": "...",
          "test": "..."
        }
 
1.  Create a `debug.js` file with the following contents:

        if (process.env.NODE_ENV === 'production') {
          require('@google-cloud/debug-agent').start();
        }

1.  To make Cloud Debugger available to the deployed application, the
    `@google-cloud/debug-agent` module must be imported as the second thing the
    application does (right after where Trace is imported). Add the following to the
    top of `index.js` after `require('./trace');`:

        require('./debug');
 
    The application will now be able to use Cloud Debugger when it is
    deployed to App Engine.

1.  Re-deploy the application:

        gcloud app deploy

1.  You can debug the application using the [Cloud Debugger dashboard][debugger_dashboard].

[debugger]: https://cloud.google.com/debugger/
[debugger_agent]: https://github.com/GoogleCloudPlatform/cloud-debug-nodejs
[debugger_dashboard]: https://console.cloud.google.com/debug

## Cleanup

See the [cleanup guide][cleanup] for the Bookshelf Node.js tutorial.

[cleanup]: https://cloud.google.com/nodejs/getting-started/delete-tutorial-resources
[deploying]: https://cloud.google.com/community/tutorials/ghost-on-app-engine-part-1-deploying
[ghost]: https://ghost.org/
[flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/
