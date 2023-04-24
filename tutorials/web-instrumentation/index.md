---
title: Instrumenting web apps end to end with Cloud Monitoring and OpenTelemetry
description: Instrument a web application end to end, from the browser to the backend application, including logging, monitoring, and tracing with OpenTelemetry and Cloud Monitoring.
author: alexamies
tags: Cloud Monitoring, OpenTelemetry
date_published: 2020-05-08
---

Alex Amies | Site Reliability Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates instrumenting a web application end to end—from the browser to the backend application—with 
OpenTelemetry and Cloud Logging, Monitoring, and Trace to understand app performance in a load test. The test app runs with
Node.js on Google Kubernetes Engine (GKE) with modern browser JavaScript packaged with webpack. The tutorial is written for
full-stack developers interested in instrumenting their apps for operational monitoring of end-user experience. The 
instrumentation discussed is intended to be applicable permanently for the app, not just temporarily for the load test. 

The tutorial specifically addresses the question of how an app will handle a load spike. The principles discussed apply to 
many other use cases, as well, such as rolling out a new version of an app. Familiarity with JavaScript development of 
browser and Node.js apps, running Kubernetes, and basic use of Google Cloud will help. Running a similar scenario with 
languages other than JavaScript is possible with some adaptation.

The architecture of the app is shown in this schematic diagram:

![Schematic diagram of the test app](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/schematic_diagram.png)

## Objectives 

* Learn to instrument a browser app with Cloud Logging, Monitoring, and Trace.
* Learn how to collect instrumentation data from the browser and the server, send to Cloud Monitoring, export to 
  BigQuery, and analyze the logs with SQL queries.
* Quickly and easily run a load test to understand how your app handles load spikes.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* Compute Engine
* Container Registry
* Cloud Monitoring
* Cloud Logging
* Cloud Trace
* BigQuery
* Cloud Build

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your 
projected usage.

## Before you begin

For this tutorial, you need a Google Cloud
[project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a new 
one, or select a project that you already created.

1.  Select or create a Google Cloud project.

    [Go to the project selector page.](https://console.cloud.google.com/projectselector2/home/dashboard)
    
1.  Enable billing for your project.

    [Enable billing.](https://support.google.com/cloud/answer/6293499#enable-billing)
    
1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/professional-services.git
        
1.  Install Node.js.
1.  Install Go.
1.  Install Docker.
1.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/install).

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created. For details,
see [Cleaning up](#Cleaning-up).

## Background

This tutorial is motivated by customer inquiries about preparing for seasonal peaks that can be reduced to the seemingly 
simple question "How well will my app handle a load spike?" As simple as the question seems, it has many layers. From a
client perspective, will end users experience degraded performance during the peak? From a backend perspective, how fast
will the cluster serving the app scale up? Also, how long will it take the app to recover if it fails?

First, you need a plan for collecting data to be able to observe how the app is performing. Monitoring data, although 
useful, is not sufficient. Monitoring data is typically aggregated over time intervals of one minute and focuses on a single 
point of measurement. You need richer, second-by-second measurements because a lot can happen in a minute. For that, this 
tutorial shows how to collect distributed traces and metrics using the OpenTelemetry JavaScript library, which sends this 
data to Cloud Monitoring through the OpenTelemetry Collector. Logs are captured with Cloud Logging. You export the logs to
BigQuery, where sophisticated queries can be done.

Second, you need to know of any end-user impact. This tutorial shows how to instrument both the backend and the client for 
this purpose. Of special interest are errors that affect end users and timeouts for requests that do not make it to the 
backend.

## Code walkthrough

This section explains the code used in the tutorial app. Read this walkthrough section if you want to know how to instrument
the app; skip this walkthrough section if you just want to run the tutorial.

### Client

The file `browser/src/index.js` is the entry point for the web app. It imports and initializes the OpenTelemetry code as 
shown below for document loading.

    import { CollectorExporter } from '@opentelemetry/exporter-collector';
    import { SimpleSpanProcessor } from '@opentelemetry/tracing';
    import { DocumentLoad } from '@opentelemetry/plugin-document-load';
    import { WebTracerProvider } from '@opentelemetry/web';
    import { TestApp } from './TestApp';

    console.log(`App version: ${__VERSION__}`);

    // Edit this to point to the app to the OpenTelemetry Collector address:
    // If running locally use http://localhost:55678/v1/trace
    const collectorURL = 'http://localhost:55678/v1/trace';
    // const collectorURL = 'http://35.188.162.236/v1/trace';

    const webTracer = new WebTracerProvider({
      plugins: [
        new DocumentLoad(),
      ],
    });
    const collectorOptions = {
      url: collectorURL,
    };
    const exporter = new CollectorExporter(collectorOptions);
    webTracer.addSpanProcessor(new SimpleSpanProcessor(exporter));

    const testApp = new TestApp(collectorURL);
    testApp.setup();

The ES2015-style import statements used here are resolved by webpack in a client code build process. This build process is 
configured by the webpack configuration file `browser/webpack.config.js`. 

The file `browser/src/LoadTest.js` drives the test. It imports the `XMLHttpRequestPlugin` module to trace XML HTTP requests 
to the server and the `CollectorExporter` module to export the trace data to the OpenTelemetry Collector.

    import { CollectorExporter } from '@opentelemetry/exporter-collector';
    import { BatchSpanProcessor } from '@opentelemetry/tracing';
    import { XMLHttpRequestPlugin } from '@opentelemetry/plugin-xml-http-request';
    import { ZoneScopeManager } from '@opentelemetry/scope-zone';
    import { WebTracerProvider } from '@opentelemetry/web';

The tracing initialization code is shown below:

    const webTracerWithZone = new WebTracerProvider({
      scopeManager: new ZoneScopeManager(),
      plugins: [
        new XMLHttpRequestPlugin({
          ignoreUrls: ['/log', '/trace'],
        }),
      ],
    });
    const collectorOptions = {
      url: collectorURL,
    };
    const exporter = new CollectorExporter(collectorOptions);
    webTracerWithZone.addSpanProcessor(new BatchSpanProcessor(exporter));

The app uses an HTML page to accept user input for test parameters and drive load to the server. `LoadTest.js` implements
this and also tallies the total number of requests sent and received:


      sendData(payload) {
        const data = {
          name: payload.name,
          reqId: payload.reqId,
          tSent: payload.tSent,
        };
        this.numSent += 1;
        const urlStr = `/data/${payload.reqId}`;
        const obs = ajax({
          body: JSON.stringify({ data }),
          headers: {
            'Content-Type': 'application/json',
          },
          method: 'POST',
          url: urlStr,
        });
        obs.subscribe(
          (val) => {
            const resp = val.response;
            this.numSuccess += 1;
            if (this.numSuccess % 100 === 0) {
              this.logCollector.log(`Num success: ${this.numSuccess}`);
            }
            if (resp instanceof Object && 'tSent' in resp && 'name' in resp
                && 'reqId' in resp) {
              const latency = performance.now() - resp.tSent;
              this.logCollector.log(`LoadTest: latency: ${latency}, `
                                      + `${resp.name}, reqId: ${resp.reqId}`);
            } else {
              this.logCollector.log('LoadTest: Payload does not include '
                                       + 'expected fields');
            }
          },
          (err) => {
            this.numFail += 1;
            this.logCollector.error(`Error sending data ${err}`);
            this.logCollector.log(`Num failures: ${this.numFail}`);
          },
        );
      }

The client inserts a unique ID (a timestamp of when the request was sent) and logs it. When the response is received, the 
latency is computed and logged. The client latency is calculated using the W3C User Timing API's `performance.now()` method.
For details on measuring browser performance, see
[A Primer for Web Performance Timing APIs](https://w3c.github.io/perf-timing-primer/). 

The browser logs are collected and sent to the server using the `LogCollector` class, located in the file 
`browser/src/lib/LogCollector.js`. That code stores and forwards the logs to the application running in Node.js, where the 
class `ConsoleLogger` (located in the file `src/ConsoleLogger.js`) sends the logs to the server console. In Google 
Kubernetes Engine, the server console logs are sent to Cloud Logging. 

**Note**: In the future, you may be able to reduce the code needed for this with the 
[Reporting API](https://developer.mozilla.org/en-US/docs/Web/API/Reporting_API), an experimental initiative in the process 
of being standardized, currently only available for Firefox and Chrome with a special flag.

### Server

The server runs in Node.js using Express. The server accepts the HTTP requests, uses some CPU resources to simulate a real
app, and returns the same data to the client. The entry point is the `src/app.js` file:

    const appTracing = require('./tracing');
    const tracer = appTracing.initTracing();
    const express = require('express');

    // Initialize Express
    const app = express();
    app.use(express.static('dist'));
    app.use(express.json());

Importing and initializing the OpenTelemetry code is done in the `src/tracing.js` file:

    const opentelemetry = require('@opentelemetry/api');
    const { StackdriverTraceExporter } = require('@opentelemetry/exporter-stackdriver-trace');
    const { LogLevel } = require('@opentelemetry/core');
    const { NodeTracerProvider } = require("@opentelemetry/node");
    const { BatchSpanProcessor } = require("@opentelemetry/tracing");

    /**
     * Initialize tracing
     * @return {Tracer} tracer object
     */
    module.exports.initTracing = () => {
      const provider = new NodeTracerProvider({
        logLevel: LogLevel.ERROR
      });
      opentelemetry.trace.initGlobalTracerProvider(provider);
      const tracer = opentelemetry.trace.getTracer('default');
      provider.addSpanProcessor(new BatchSpanProcessor(getExporter()));
      console.log("initTracing: done");
      return tracer;
    };

    function getExporter() {
      const keyFileName = process.env.GOOGLE_APPLICATION_CREDENTIALS;
      if (!keyFileName) {
        console.log('Proceed without a keyFileName (will only work on GCP)');
        return new StackdriverTraceExporter({});
      }
      console.log("Using GOOGLE_APPLICATION_CREDENTIALS");
      return new StackdriverTraceExporter({
        keyFileName: keyFileName});
    }

The server app also adds child spans to trace the backend processing of data:

    app.post('/data*', (req, res) => {
      if ('data' in req.body) {
        const data = req.body['data'];
        if (data) {
          // Trace the request
          const currentSpan = tracer.getCurrentSpan();
          const span = tracer.startSpan('process-data', {
            parent: currentSpan
          });
          tracer.withSpan(span, () => {
            // Use some CPU resources
            for (let i = 0; i < 1000000; i += 1) {
              // Do nothing useful
              if (i % 1000000 === 0) {
                console.log(`app.post ${i}`);
              }
            }
            if ('name' in data && 'reqId' in data && 'tSent' in data) {
              console.log(`tSent: ${data.tSent}, name: ${data.name}, `
                          + `reqId: ${data.reqId}`);
              res.status(200).send(data).end();
            } else {
              const msg = 'Payload does not include expected fields';
              console.log(msg);
              sendError(msg, res);
            }
            span.end();
          });
        } else {
          const msg = 'Data is empty';
          console.log(msg);
          sendError(msg, res);
        }
      } else {
        const msg = 'Data is empty';
        sendError(msg, res);
      }
    });

## Building and deploying the test app

The application can be run in a local development environment, on any of a number of environments in Google Cloud, or 
elsewhere. Here’s an example of how to run it in Google Kubernetes Engine, using Cloud Shell for the command-line interface.

### Project setup

1.  After cloning the repository, change to its directory:

        cd professional-services/examples/web-instrumentation

1.  Install the JavaScript packages required by both the server and the browser:

        npm install

1.  Set the Cloud SDK to the current project:

        GOOGLE_CLOUD_PROJECT=[YOUR_PROJECT_ID]
        gcloud config set project $GOOGLE_CLOUD_PROJECT

1.  Enable the APIs for the required services:

        gcloud services enable bigquery.googleapis.com \
          cloudbuild.googleapis.com \
          cloudtrace.googleapis.com \
          compute.googleapis.com \
          container.googleapis.com \
          containerregistry.googleapis.com \
          logging.googleapis.com \
          monitoring.googleapis.com

### OpenTelemetry Collector

This section shows how to build and push the OpenTelemetry Collector to Container Registry.

**Note**: At the time of this writing, the OpenTelemetry Collector is in beta.

1.  Open a new command shell. In a new directory, clone the OpenTelemetry Collector Contrib project, which contains the 
    Cloud Monitoring (Stackdriver) exporter

        git clone https://github.com/open-telemetry/opentelemetry-collector-contrib
        cd opentelemetry-collector-contrib

1.  Build a Docker container with the binary executable:

        make docker-otelcontribcol

1.  Set the Cloud SDK to the current project in the new command shell:

        GOOGLE_CLOUD_PROJECT=[YOUR_PROJECT_ID]

1.  Tag the image for Container Registry:

        docker tag otelcontribcol gcr.io/$GOOGLE_CLOUD_PROJECT/otelcontribcol

1.  Configure `gcloud` as a Docker credential helper:

        gcloud auth configure-docker

1.  Push the container with the binary executable to Container Registry:

        docker push gcr.io/$GOOGLE_CLOUD_PROJECT/otelcontribcol

### Deploying the app to Google Kubernetes Engine

The application can be deployed locally or to Google Kubernetes Engine without any changes, except that the URL of the
OpenCensus agent must be included in the web client. 

#### Create a cluster

The steps in this section create the Kubernetes cluster and deploy the OpenTelemetry Collector.

1.  Back in the first command shell, create a GKE cluster with 1 node and with autoscaling enabled:

        ZONE=us-central1-a
        NAME=web-instrumentation
        CHANNEL=stable
        gcloud beta container clusters create $NAME \
           --num-nodes 1 \
           --enable-autoscaling --min-nodes 1 --max-nodes 4 \
           --enable-basic-auth \
           --issue-client-certificate \
           --release-channel $CHANNEL \
           --zone $ZONE \
           --enable-stackdriver-kubernetes

1.  Change the project ID in the file `k8s/ot-service.yaml` with the `sed` command:

        sed -i.bak "s/[YOUR_PROJECT_ID]/$GOOGLE_CLOUD_PROJECT/" k8s/ot-service.yaml

1.  Deploy the OpenTelemetry Collector to the Kubernetes cluster:

        kubectl apply -f k8s/ot-service.yaml

1.  Get the IP address of the service:

        EXTERNAL_IP=$(kubectl get svc ot-service-service \
            -o jsonpath="{.status.loadBalancer.ingress[*].ip}")

1.  Edit the file `browser/src/index.js`, changing the variable `agentURL` to the external IP address and port of the agent 
    with the following sed command:

        sed -i.bak "s/localhost:55678/${EXTERNAL_IP}:80/" browser/src/index.js

#### Build the client

The browser code refers to ES2015 modules that need to be transpiled and bundled with the help of webpack. 

1.  In the first command shell, change to the browser code directory:

        cd browser

1.  Install the dependencies:

        npm install

1.  Compile and package the code:

        npm run build

The output is written to the file `dist/main.js`.

#### Build and deploy the app image

This section uses Cloud Build to build the test app, and then the app is deployed to the Kubernetes cluster.

1.  Go up one directory:

        cd  ..

1.  Build the app's Docker image and push it to Container Registry:

        gcloud builds submit

1.  Change the project ID in the file `k8s/deployment.yaml` with the `sed` command:

        sed -i.bak "s/[YOUR_PROJECT_ID]/$GOOGLE_CLOUD_PROJECT/" k8s/deployment.yaml

1.  Add a deployment for the app to the cluster:

        kubectl apply -f k8s/deployment.yaml

1.  Create a Kubernetes service:

        kubectl apply -f k8s/service.yaml

1.  Expose the service with an Ingress:

        kubectl apply -f k8s/ingress.yaml

1.  Check the status of the Ingress and get the external IP address:

        kubectl get ingress

    It may take a few minutes for the service to be exposed through an external IP address.
    
    The URL to navigate to is shown in the command shell output and also in the Cloud Console.
    
1.  Use the URL to navigate to the web interface.

1.  To try the app, enter a test name, a small number of requests, and 1000 ms between requests, and then click
    **Start test**.
    
    ![Screenshot: Web form for test app](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/webform_steady_state.png)

1.  Navigate to the web instrumentation container deployment in the Cloud Console.

1.  Click **Container logs** to navigate to the Log Viewer and check that your test generated some logs.

    ![Screenshot: Kubernetes deployment detail](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/k8s_deployment.png)

#### Enable export of logs to BigQuery

To analyze the details of the load test, you use logs and trace data, which enables analysis of data at per-request and 
second intervals. Follow the steps in this section to create log exports for the Kubernetes container and load balancer 
logs.

1.  Create a BigQuery dataset for the container logs:

        bq --location=US mk -d \
          --description "Web instrumentation container log exports" \
          --project_id $GOOGLE_CLOUD_PROJECT \
          web_instr_container

1.  Create a log export for the container logs:

        LOG_SA=$(gcloud logging sinks create web-instr-container-logs \
          bigquery.googleapis.com/projects/$GOOGLE_CLOUD_PROJECT/datasets/web_instr_container \
          --log-filter='resource.type="k8s_container" AND labels.k8s-pod/app="web-instrumentation"' \
          --format='value("writerIdentity")')

1.  Grant write access to BigQuery for the logs service account:

        gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
            --member $LOG_SA \
            --role roles/bigquery.dataEditor

    The identity of the logs writer service account is captured in the shell variable `LOG_SA`. 

Repeat these steps for the load balancer logs:

1.  Create a BigQuery dataset:

        bq --location=US mk -d \
          --description "Web instrumentation load balancer log exports" \
          --project_id $GOOGLE_CLOUD_PROJECT \
          web_instr_load_balancer

1.  Create a log export for the load balancer logs: 

        LOG_SA=$(gcloud logging sinks create web-instr-load-balancer-logs \
          bigquery.googleapis.com/projects/$GOOGLE_CLOUD_PROJECT/datasets/web_instr_load_balancer \
          --log-filter='resource.type="http_load_balancer"' \
          --format='value("writerIdentity")')

1.  Grant write access to BigQuery for the new service account ID: 

        gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
          --member $LOG_SA \
          --role roles/bigquery.dataEditor

## Running the load test

The browser application generates the load sent to the server and tallies the results. As the browser generates load against
the server, the latency increases. With the instrumentation that you put in place, you can compare server and client side 
latency data.

### Generate some load

In this section, you enter a steady-state load followed by a load spike. The steady state load gives a reference level for
latency that you can use to compare against the result of the load spike. 
    
1.  Navigate to the IP address shown in the output of the `kubectl get ingress` command.

1.  Enter values for the steady state, such as 1,800 requests at an interval of 1000 ms, which gives 30 minutes of
    steady-state load of 1 request per second.

1.  Check the load in the 
    [Monitoring tab](https://console.cloud.google.com/net-services/loadbalancing/loadBalancers/list) for the L7 load 
    balancer for the Kubernetes Ingress, as shown below.

    ![Screenshot: Cloud Load Balancer request count](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_request_count.png)
    
     It may take a few minutes for monitoring data to be generated and replicated so that it's visible in the chart.

1.  Check the latency in [Cloud Monitoring](https://console.cloud.google.com/monitoring) under
    **Dashboards** > **Load Balancing**.

    ![Screenshot: Cloud Monitoring load balancing total latency](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_latency.png)

1.  When the latency stabilizes, open another tab in your browser at the Ingress IP address.

1.  Enter values for the load spike, such as 10,000 requests at intervals of 20ms, which gives a load spike of 50 requests
    per second for 3 minute and 20 seconds.
    
    You should see the traffic volume and latency increase very quickly in the
    [Trace](https://console.cloud.google.com/traces/traces) view, as shown below.

    ![Trace scatter plot for the error spike](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/trace_scatter_plot_load_spike.png)

### Viewing the test results

1.  Click the points to see details. The web client spans should be shown as parents of the server side spans, as shown
    in the screenshot below.

    ![Example Trace Timeline](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/web_trace_child_spans.png)

    The spans generated by the web client can be differentiated from the server spans from the agent. For the web client,
    the component field is `xml-http-request`.
    
1.  Click **Show events** in the timeline to see events for opening the XML-HTTP request and sending data from the web 
    client. The server span should show an event for bytes received.

1.  Navigate to the load balancing monitoring page in the Cloud Console.

1.  Click **Show all Legends** to see the charts for responses by code class and expand the legend.

    You should see a spike with a few responses in 300 or 500 response class:

    ![Cloud Monitoring - load balancing response count by class](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_latency_spike.png)

1.  To see the effect on the browser client latency during the spike, click one of the points in the Trace chart:

    ![Example Trace during spike showing latency experienced by the client](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/trace_timeline_spike.png)

    Notice how long the client latency is compared to the server latency. This indicates a lot of time spent before the 
    request arrives at the Node.js server. You can also view the frontend round-trip time (RTT) in Cloud Monitoring, as 
    shown below:

    ![Cloud Monitoring view of frontend RTT as measured by the load balancer](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_rtt_spike.png)
    
    The main suspect for the increase in latency is load on the CPU. You can see the CPU load from the Compute Engine
    monitoring view.

1.  Click the [Monitoring tab](https://console.cloud.google.com/monitoring).

    ![Screenshot: Virtual machine CPU](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gce_cpu_spike.png)

    You can also view CPU load on the Kubernetes pod serving your app.

    ![Screenshot: CPU for the Kubernetes Pod](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/pod_cpu_spike.png)

The request chart and browser summary showed errors. One convenient place to look for error summaries is the Error Reporting user interface:

![Screenshot: Error Reporting](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/error_reporting_spike.png)

These errors are interesting. There are only four occurrences, but they might indicate that your home-made browser log 
shipper may have overloaded the server by sending a huge request. An alternative approach to collecting browser error logs
is the 
[Client-side JavaScript library for Stackdriver Error Reporting](https://github.com/GoogleCloudPlatform/stackdriver-errors-js).

## Detailed analysis of the test data

You ran the load test and saw that the app seemed to do alright with some increase in latency and errors, but it's a good
idea to check in more detail. 

Let’s review the questions raised at the start of the tutorial.

### How did the app scale?

You can answer the question of how the app scaled in terms of impact on end users by querying log data in BigQuery to find
second-by-second client latency.

To explore the client logs, enter a query like the one below in the
[BigQuery console](https://console.cloud.google.com/bigquery). Use the current date (UTC time zone) in the table name.

    SELECT
      timestamp, textPayload
    FROM `web_instr_container.stdout_20200129`
    ORDER BY timestamp DESC
    LIMIT 10

To explore the load balancer log data in BigQuery, enter a query like the following:

    SELECT 
      httpRequest.requestUrl,
      httpRequest.status,
      trace,
      timestamp 
    FROM 
      `web_instr_load_balancer.requests_20200129` 
    LIMIT 10

#### Visualizing the log data

From BigQuery, read the data into Colab, where it can be plotted in charts. Colab is an iPython notebook service hosted by
Google with many Google Cloud services pre-configured for ease of use. Follow these steps to query the log tables in BigQuery and process the results in Python.

1.  Open the
    [Colab](https://colab.research.google.com/github/GoogleCloudPlatform/professional-services/blob/master/examples/web-instrumentation/load_test_analysis.ipynb)
    sheet in Chrome. 

1.  Open the **Initialization** block if it's not open already.

1.  Change the `project_id` variable to your own project.

1.  To execute the code in the **Initialization** block, click the **Run** button. If prompted, approve access with your 
    Google account.

1.  Open the **Logs Overview** block.

1. Execute the code in the **Logs Overview** block.

1. Open the **Client Latency** block.

1.  Change the hour in the `WHERE` clause to be the hour in which you ran the test.

1.  Execute the code in the **Client Latency** block.

    The result is a chart of median client latency:

    ![Median client latency from Colab sheet](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/client_latency_median.png)

The Colab sheet uses the Pandas library to hold and plot the BigQuery query results. Pandas uses the MatPlotLib library for
plotting the chart. 

To see the details of the client latency, do the following:

1.  In the Colab sheet, open the **Scatter Plot** code block.
1.  Edit the table name for the date and hour and minute range for the time of your test.
1.  Execute the code block.

    The result is a chart that shows points for the client latency values:

    ![Scatter plot for client latency](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/client_latency_scatterr.png)

In this test, you will probably not trigger autoscaling. To see autoscaling, you can repeat the test with a greater 
number of requests sent and a greater test duration. You may not be able to generate sufficient load from one browser to 
trigger autoscaling. If you increase the number of requests sent to an excessive value, you may see the Chrome error  
`net::ERR_INSUFFICIENT_RESOURCES`.

To drive a more substantial load, you can use
[headless Chrome](https://developers.google.com/web/updates/2017/04/headless-chrome) or
[Webdriver](https://selenium.dev/documentation/en/webdriver/) with multiple clients. Another approach is to use a simple 
load generator like [Locust](https://locust.io/), [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html), or 
[JMeter](http://jmeter.apache.org/) and simultaneously observe the noisy neighbor impact on an instrumented browser app, as
described in this tutorial.

## Other languages and environments

You can run the backend or frontend in other languages and use the same instrumentation with more scalable tools, such 
as Apache Bench or Locust. To see the format of the XML HTTP requests that you will need to use, do the following:

1. Start a test from Chrome (for example, with 5 requests at 1,000 ms intervals).
1. Open Chrome Developer tools.
1. Go to the **Network** tab.
1. Right-click a request and click **Copy > Copy as cURL**.

This procedure gives the JSON format needed, as well as the headers that can be used directly in cURL, which are similar to
those required for other tools. 

See the [OpenCensus](https://opencensus.io/) website to get started with other backend languages. For other frontend 
languages, such as Java on Android or Objective-C on iOS, you need to use the OpenTelemetry service, as described above.

If you prefer not to use client libraries to generate traces, you can generate them from your own code by sending HTTP 
headers following the [W3C Trace Context](https://www.w3.org/TR/trace-context-1/) format. This may be preferable on mobile
clients, where it's important to minimize the size of the application binary. The trace ID generated is very useful for
correlating logs between frontend and backend, even if you do not use tracing.

If running in a serverless environment like Cloud Run or App Engine flexible environment, you need to package the 
OpenTelemetry service in the Docker container with a web server like Nginx to forward the trace collection requests to the 
collector.

## Troubleshooting

For troubleshooting tips, see the 
[README document for this tutorial's code](https://github.com/GoogleCloudPlatform/professional-services/tree/master/examples/web-instrumentation#troubleshooting).

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

### Delete the project

To delete the project, do the following:

1. In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).

1. In the project list, select the project that you want to delete and click **Delete**.

1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What’s next

Explore the following related resources:

* Explore the [Opentelemetry-js](https://github.com/open-telemetry/opentelemetry-js) GitHub project.
* Try
  [distributed load testing using Google Kubernetes Engine](https://cloud.google.com/solutions/distributed-load-testing-using-gke).
* Read about [patterns for scalable and resilient apps](https://cloud.google.com/solutions/scalable-and-resilient-apps).
* Read about [handling overload](https://landing.google.com/sre/sre-book/chapters/handling-overload/) in the SRE Book.
* Read about [load balancing in data centers](https://landing.google.com/sre/sre-book/chapters/load-balancing-datacenter/)
  in the SRE Book.
* Read about [managing load](https://landing.google.com/sre/workbook/chapters/managing-load/) in the SRE Workbook.
* Adapt the app in this tutorial to a Go backend with [Troubleshooting app latency with Cloud Spanner and OpenCensus](https://cloud.google.com/solutions/troubleshooting-app-latency-with-cloud-spanner-and-opencensus).
* Try out other Google Cloud features. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
