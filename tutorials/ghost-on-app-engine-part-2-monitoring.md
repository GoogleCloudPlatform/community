---
title: Ghost on App Engine Part 2 - Monitoring
author: jmdobry
tags: App Engine, Ghost
date_published: 05/26/2016
---
See [Ghost on App Engine Part 1 - Deploying][deploying].

This tutorial explains how to monitor a [Ghost blog][ghost] deployed on [Google App Engine Flexible Environment][flex].

## Monitoring

Monitoring is powered by [Stackdriver Monitoring][monitoring].

You do not have to install the monitoring agent on Google App Engine Flexible Environment, as Stackdriver monitoring support is built-in.

You can [view the monitoring dashboard][mon_dash] for your Ghost blog in the Google Stackdriver Console.

[monitoring]: https://cloud.google.com/monitoring/
[mon_dash]: https://app.google.stackdriver.com/services/app-engine/

## Logging

Logging is powered by [Stackdriver Logging][logging].

You do not have to install the logging agent on Google App Engine Flexible Environment, as Stackdriver Logging support is built-in. See [Stackdriver Logging in App Engine Apps for more information][logging].

You can [view the logs][logs] for your Ghost blog in the Google Cloud Platform Console.

[logging]: https://cloud.google.com/logging/
[gae_logging]: https://cloud.google.com/appengine/articles/logging
[logs]: https://console.cloud.google.com/logs?service=appengine.googleapis.com

## Trace

Tracing of HTTP requests and RPC calls in your Ghost blog is powered by [Stackdriver Trace][trace].

To begin tracing what goes on in your Ghost blog you must import the [Node.js trace agent][trace_agent] into the application.

[trace]: https://cloud.google.com/trace/
[trace_agent]: https://github.com/GoogleCloudPlatform/cloud-trace-nodejs

### Activate Trace

1. To install the `@google/cloud-trace` module during deployment, edit the `package.json` file and add a `postinstall` script:

        "scripts": {
          "preinstall": "...",
          "postinstall": "npm install @google/cloud-trace",
          "start": "...",
          "test": "..."
        }

    We use a `postinstall` script because it allows us to avoid messing with Ghost's `npm-shrinkwrap.json` file.

1. Create a `trace.js` file with the following contents:

        if (process.env.NODE_ENV === 'production') {
          require('@google/cloud-trace').start({
            enhancedDatabaseReporting: true
          });
        }

1. To start Stackdriver Trace when the deployed application starts, the `@google/cloud-trace` module must be imported as the very first thing the application does. Add the following to the _very first line_ of `index.js`:

        require('./trace');

    The application will now use Stackdriver Trace when it is deployed to App Engine.

1. Re-deploy the application:

        gcloud preview app deploy

1. After a few minutes, activity in your application will cause traces to begin appearing in the [Trace Dashboard][trace_dashboard].

[trace_dashboard]: https://console.cloud.google.com/traces/traces

## Error Reporting

Error reporting in your Ghost blog is powered by [Stackdriver Error Reporting][errorreporting].

[errorreporting]: https://cloud.google.com/error-reporting/

## Debugging

Debugging your Ghost blog is powered by [Stackdriver Debugger][debugger].

[debugger]: https://cloud.google.com/debugger/

[deploying]: https://cloud.google.com/community/tutorials/ghost-on-app-engine-part-1-deploying
[ghost]: https://ghost.org/
[flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/