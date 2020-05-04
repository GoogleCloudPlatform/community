---
title: Instrumenting web apps end to end with Cloud Monitoring and OpenTelemetry
description: Instrument a web application end to end, from the browser to the backend application, including logging, monitoring, and tracing with OpenTelemetry and Cloud Monitoring.
author: alexamies
tags: Cloud Monitoring, OpenTelemetry
date_published: 2020-05-01
---

This tutorial demonstrates instrumenting a web application end to end, from the browser to the backend application, 
including logging, monitoring, and tracing with OpenTelemetry and Cloud Monitoring to understand app performance in a load
test. The test app runs with Node.js on Google Kubernetes Engine (GKE) with modern browser JavaScript packaged with Webpack.
The tutorial is written for full-stack developers interested in instrumenting their apps for operational monitoring of 
end-user experience. The instrumentation discussed is intended to be applicable permanently for the app, not just 
temporarily for the load test. 

The tutorial specifically addresses the question of how and app will handle a load spike. The principles discussed apply to 
many other use cases, as well, such as rolling out a new version of an app. Familiarity with JavaScript development of 
browser and Node.js apps, running Kubernetes, and basic use of Google Cloud will help. Running a similar scenario with 
languages other than JavaScript is possible with some adaptation.

The architecture of the app is shown in this schematic diagram:

![Schematic Diagram of the Test App](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/schematic_diagram.png)

## Objectives 

* Learn to instrument a browser app with Cloud Logging, Monitoring, and Trace.
* Learn how to collect instrumentation data from the browser and the server, send to Cloud Monitoring, export to 
  BigQuery, and analyze the logs with SQL queries.
* Quickly and easily run a load test to understand how your app handles load spikes.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* Compute Engine
* Container Registry
* Cloud Monitoring, Logging, and Trace
* BigQuery
* Cloud Build

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your 
projected usage.

## Before you begin

For this tutorial, you need a Google Cloud
[project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a new one, or select a project you already created.

1.  Select or create a Google Cloud project.

    [Go to the project selector page.](https://console.cloud.google.com/projectselector2/home/dashboard)
    
1.  Enable billing for your project.

    [Enable billing.](https://support.google.com/cloud/answer/6293499#enable-billing)
    
1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/professional-services.git
        
1.  Install Node.js.
1.  Install Go.
1.  Install Docker
1.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/install).

When you finish this tutorial, you can avoid continued billing by deleting the resources you created. For details,
see [Cleaning up](#Cleaning-up).

## Background

This tutorial is motivated by customer inquiries about preparing for season peaks that can be reduced to the seemingly simple question, How well will my app handle a load spike? As innocent as the question seems, it has many layers. From a client perspective, will end users experience degraded performance during the peak? From a backend perspective, how fast will the cluster serving the app scale up? Also, how long will it take the app to recover, if it fails?

Firstly, we need a plan for collecting data to be able to observe how the app is performing. We will see that monitoring data, although useful, is not sufficient. Monitoring data is typically aggregated over time intervals of one minute and focuses on a single point of measurement. We will need richer second-by-second measurements because a lot can happen in a minute. For that we are going to collect distributed traces and metrics using the OpenTelemetry JavaScript library, which will send this data to Cloud Monitoring via the OpenTelemetry Collector. Logs will be captured with Cloud Logging. We will export the logs to BigQuery where sophisticated queries can be done.

Secondly, we want to know of any end-user impact. We will instrument both backend and client, for that purpose. We are especially interested in end-user observed errors and timeouts for requests that do not make it to the backend.

## Code Walkthrough

This section explains the code used in the tutorial app. Read this if you want to know how to instrument the app and skip it if you just want to run the tutorial.

### Client

The file `browser/src/index.js` is the entry point for the web app. It imports and initializes the OpenTelemetry code as shown below for document loading.

```JavaScript
import {CollectorExporter} from '@opentelemetry/exporter-collector';
import { CollectorExporter } from '@opentelemetry/exporter-collector';
import { SimpleSpanProcessor } from '@opentelemetry/tracing';
import { DocumentLoad } from '@opentelemetry/plugin-document-load';
import { WebTracerProvider } from '@opentelemetry/web';
import { TestApp } from './TestApp';

console.log(`App version: ${__VERSION__}`);

// Edit this to point to the app to the OpenTelemetry collector address:
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
```

The ES2015 style import statements used here will be resolved by webpack in a client code build process. This build process is configured by the webpack configuration file `browser/webpack.config.js`. 

The file `browser/src/LoadTest.js` actually drives the test. It imports the XMLHttpRequestPlugin to trace XML HTTP requests to the server and the CollectorExporter to export the trace data to the OpenTelemetry collector.

```JavaScript
import { CollectorExporter } from '@opentelemetry/exporter-collector';
import { BatchSpanProcessor } from '@opentelemetry/tracing';
import { XMLHttpRequestPlugin } from '@opentelemetry/plugin-xml-http-request';
import { ZoneScopeManager } from '@opentelemetry/scope-zone';
import { WebTracerProvider } from '@opentelemetry/web';
```

The tracing initialization code is shown below

```JavaScript
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
```

The app uses a HTML page to accept user input for test parameters and drives load to the server. `LoadTest.js` implements this and also tallies the total number of requests sent and received:

```JavaScript
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
```

The client inserts a unique id, a timestamp of when the request was sent and logs it. When the response is received the latency is computed and logged. The client latency is calculated using the W3C User Timing performance.now() API. See 
[A Primer for Web Performance Timing APIs](https://w3c.github.io/perf-timing-primer/)
for details on measuring browser performance. 

The browser logs are collected and sent to the server using the `LogCollector` class, located in file `browser/src/lib/LogCollector.js`. That code stores and forwards the logs to the application running in Node.js, where the class `ConsoleLogger`, located in file `src/ConsoleLogger.js`, sends the logs to the server console. If Google Kubernetes Engine the server console logs are shipped to Cloud Logging. In future you may be able to reduce the code needed for this with the 
[Reporting API](https://developer.mozilla.org/en-US/docs/Web/API/Reporting_API),
an experimental initiative in the process of being standardized, currently only supported by Firefox and Chrome with a special flag  at present.

### Server

The server runs in Node.js using Express. It accepts the HTTP requests, consumes some CPU to simulate a real app, and returns the same data to the client. The entry point is the `src/app.js` file:

```JavaScript
const appTracing = require('./tracing');
const tracer = appTracing.initTracing();
const express = require('express');

// Initialize Express
const app = express();
app.use(express.static('dist'));
app.use(express.json());
```

Importing and initialize the OpenTelemetry code is done in `src/tracing.js`:

```JavaScript
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
```

The server app also adds child spans to trace backend processing of data:

```JavaScript
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
        // Use some CPU
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
```

## Building and Deploying the Test App

The application can be run in a local development environment, on any of a number of environments in Google Cloud or elsewhere. Here’s an example of how to run it in Google Kubernetes Engine and using Cloud Shell for the command line.

### Project Setup

1. After cloning the repo, change to its directory and set an environment variable to remember the
location
```shell
cd professional-services/examples/web-instrumentation
```

1. Install the JavaScript packages required by both the server and the browser
```shell
npm install
```

1. Set Google Cloud SDK to the current project 
```shell
GOOGLE_CLOUD_PROJECT=[Your project]
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

1. Enable the required services
```shell
gcloud services enable bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  cloudtrace.googleapis.com \
  compute.googleapis.com \
  container.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

### OpenTelemetry collector

The steps below show how to build and push the OpenTelemetry collector to Google Container Registry (GCR).

Note: At the time of this writing, the OpenTelemetry collector is in beta.

1. Open up a new shell command line. In a new directory, clone the OpenTelemetry collector
contrib project, which contains the Cloud Monitoring (Stackdriver) exporter

```shell
git clone https://github.com/open-telemetry/opentelemetry-collector-contrib
cd opentelemetry-collector-contrib
```

1. Build a Docker container with the binary executable

```shell
make docker-otelcontribcol
```

1. Set Google Cloud SDK to the current project in the new terminal

```shell
GOOGLE_CLOUD_PROJECT=[Your project]
```

1. Tag the image for GCR

```shell
docker tag otelcontribcol gcr.io/$GOOGLE_CLOUD_PROJECT/otelcontribcol
```

1. Configure gcloud as a Docker credential helper

```shell
gcloud auth configure-docker
```

1. Push to GCR

```shell
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/otelcontribcol
```

### Deploying the app to Google Kubernetes Engine

The application can be deployed locally or to Google Kubernetes Engine without any changes, except the URL address of the OpenCensus agent must be included in the web client. 

#### Create a cluster

The steps below create the Kubernetes cluster and deploy the OpenTelemetry collector.

1. Back in the first terminal, create a GKE cluster with 1 node and autoscaling enabled

```shell
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
```

1. Change the project id in file `k8s/ot-service.yaml` with the sed command

```shell
sed -i.bak "s/{{PROJECT-ID}}/$GOOGLE_CLOUD_PROJECT/" k8s/ot-service.yaml
```

1. Deploy the OpenTelemetry collector to the Kubernetes cluster

```shell
kubectl apply -f k8s/ot-service.yaml
```

1. Get the IP of the service with the command

```shell
EXTERNAL_IP=$(kubectl get svc ot-service-service \
    -o jsonpath="{.status.loadBalancer.ingress[*].ip}")
```

1. Edit the file `browser/src/index.js` changing the variable agentURL to the external IP and port of the agent with the following sed command

```shell
sed -i.bak "s/localhost:55678/${EXTERNAL_IP}:80/" browser/src/index.js
```

#### Build the Client

The browser code refers to ES2015 modules that need to be transpiled and bundled with the help of webpack. 

1. In the first terminal, change to the browser code directory

```shell
cd browser
```

1. Install the dependencies with the command

```shell
npm install
```

1. Compile and package the code

```shell
npm run build
```

The output will be written to `dist/main.js`.


#### Build and deploy the app image

The steps below use Cloud Build to build the test app and then the app is
deployed to the Kubernetes cluster.

1. Change up one directory

```shell
cd  ..
```

1. Build the app Docker image and push it to GCR:

```shell
gcloud builds submit
```

1. Change the project id in file `k8s/deployment.yaml` with the sed command

```shell
sed -i.bak "s/{{PROJECT-ID}}/$GOOGLE_CLOUD_PROJECT/" k8s/deployment.yaml
```

1. Add a deployment for the app to the cluster

```shell
kubectl apply -f k8s/deployment.yaml
```

1. Create a Kubernetes service

```shell
kubectl apply -f k8s/service.yaml
```

1. Expose the service through an ingress:

```shell
kubectl apply -f k8s/ingress.yaml
```

1. It may take a few minutes for the service to be exposed through an external IP. Check for the status of the ingress and get external IP:

```shell
kubectl get ingress
```

1. The URL to navigate to is shown console output and also in the Google Cloud Console. At this point you should be able to navigate to the web interface and try it out.

![Screenshot: Web form for test app](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/webform_steady_state.png)

1. Try it by entering a test name a small number of requests and, say 1000 ms between requests, and clicking **Start test**. You should see a test summary like shown above. Navigate to web instrumentation container deployment in the Google Cloud Console, as shown below

![Screenshot: Kubernetes deployment detail](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/k8s_deployment.png)

Notice the link Container logs. Click this to navigate to the Log Viewer and check that your test generated some logs.

#### Enable log export to BigQuery

To analyze the details of the load test, we will use a log and trace data This will enable analysis of data at per-request and second intervals. Create log exports for the Kubernetes container and load balancer logs with the commands below.

1. Create a BQ dataset for the container logs

```shell
bq --location=US mk -d \
  --description "Web instrumentation container log exports" \
  --project_id $GOOGLE_CLOUD_PROJECT \
  web_instr_container
```

1. Create a log export for the container logs

```shell
LOG_SA=$(gcloud logging sinks create web-instr-container-logs \
  bigquery.googleapis.com/projects/$GOOGLE_CLOUD_PROJECT/datasets/web_instr_container \
  --log-filter='resource.type="k8s_container" AND labels.k8s-pod/app="web-instrumentation"' \
  --format='value("writerIdentity")')
```

1. The identity of the logs writer service account is captured in the shell variable LOG_SA. Grant the logs service account write access to BigQuery

```shell
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $LOG_SA \
    --role roles/bigquery.dataEditor
```

1. Repeat for load balancer logs. Create a BQ dataset

```shell
bq --location=US mk -d \
  --description "Web instrumentation load balancer log exports" \
  --project_id $GOOGLE_CLOUD_PROJECT \
  web_instr_load_balancer
```

1. Create a log export for the load balancer logs 

```shell
LOG_SA=$(gcloud logging sinks create web-instr-load-balancer-logs \
  bigquery.googleapis.com/projects/$GOOGLE_CLOUD_PROJECT/datasets/web_instr_load_balancer \
  --log-filter='resource.type="http_load_balancer"' \
  --format='value("writerIdentity")')
```

1. Note that a new service account id is created so that you need to repeat the step for granting write access BigQuery

```shell
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member $LOG_SA \
  --role roles/bigquery.dataEditor
```

## Running the load test

The browser application will generate the load sent to the server and tally the results. As the browser generates load against the server, we expect to see the latency increase. With the instrumentation that we have put we can compare server and client side latency data.

### Generate some load

Navigate to the IP shown in the output of the `kubectl get ingress` command again. We will enter a steady state load followed by a load spike. The steady state load will give a reference level for latency that we can use to compare against the result of the load spike. Enter values for the steady state like 1,800 requests at an interval of 1000 ms. This will give 30 minutes of steady state load of 1 request per second.

Check the load in the 
[GCLB monitoring tab](https://console.cloud.google.com/net-services/loadbalancing/loadBalancers/list) for the L7 load balancer for the Kubernetes ingress, as shown below. It may take a few minutes for monitoring data to be generated and replicated so that it is visible in the chart.

![Screenshot: Google Cloud Load Balancer Request Count](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_request_count.png)

Check the latency in 
[Cloud Monitoring](https://console.cloud.google.com/monitoring)
 under Dashboards | Google Cloud  Load Balancers as shown below.

![Screenshot: Cloud Monitoring GCLB Total Latency](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_latency.png)

When the latency stabilizes, open another tab in your browser at the ingress IP. Enter values for the load spike, say 10,000 requests at intervals of 20ms. This will give a load spike of 50 requests per second for about 3 minute and 20 seconds.

### Viewing the test results

You should see the traffic volume and latency increase very quickly in the 
[Trace](https://console.cloud.google.com/traces/traces)
view, as shown below.

![Trace scatter plot for the error spike](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/trace_scatter_plot_load_spike.png)

Click on the points to see details. The web client spans should be shown as parents of the the server side spans, as shown in the screenshot below.

![Example Trace Timeline](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/web_trace_child_spans.png)

The spans generated by the web client can be differentiated from the server spans from the agent. For the web client, the component field will be ‘xml-http-request.’ After clicking on ‘Show events’ in the timeline you should be able to see events for opening the XML-HTTP request and sending data from the web client. The server span should show an event for bytes received.

Navigate the GCLB monitoring page in the Cloud Console. See the charts for responses by code class and expand the legend by clicking Show all Legends. You should see a spike with a few responses in 300 or 500 response class:

![Cloud Monitoring - GCLB response count by class](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_latency_spike.png)

To see the effect on the browser client latency during the spike, click on one of the points in the Trace chart:

![Example Trace during spike showing latency experienced by the client](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/trace_timeline_spike.png)

Notice how long the client latency is compared to the server latency. This indicates a lot of time spent before the request arrives at the Node.js server. You can also view the frontend RTT in Stackdriver Monitoring, as shown below.

![Cloud Monitoring view of Frontend RTT as measured by the load balancer](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gclb_rtt_spike.png)

1. Click on the [Monitoring tab](https://console.cloud.google.com/monitoring).

Our main suspect for the increase in latency is load on the CPU. We can see the CPU load from the GCE monitoring view

![Screenshot: Virtual machine CPU](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/gce_cpu_spike.png)

We can also view CPU load on the Kubernetes pod serving our app.

![Screenshot: CPU for the Kubernetes Pod](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/pod_cpu_spike.png)

The request chart and browser summary showed errors. One convenient place to look for error summaries in the Error Reporting user interface:

![Screenshot: Error Reporting](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/error_reporting_spike.png)

These errors are interesting. There are only four occurrences but they might indicate that our home made browser log shipper may have overloaded the server by sending a huge request. An alternative approach to collecting browser error logs is the 
[Client-side JavaScript library for Stackdriver Error Reporting](https://github.com/GoogleCloudPlatform/stackdriver-errors-js).

## Detailed analysis of the test data

We ran the load test, saw that the app seemed to do alright with some increase in latency and errors, but let’s check in more detail. Let’s review the questions raised at the start of the tutorial.

### How did the app scale?

We will answer the question of how the app scaled in terms of impact on end users by querying log data in BigQuery to find second-by-second client latency.

To explore the client logs, enter a query like below in the [BigQuery console](https://console.cloud.google.com/bigquery). Use the current date (UTC time zone) in the table name.

```sql
SELECT
  timestamp, textPayload
FROM `web_instr_container.stdout_20200129`
ORDER BY timestamp DESC
LIMIT 10
```

To explore the load balancer log data in BigQuery, enter a query like

```sql
SELECT 
  httpRequest.requestUrl,
  httpRequest.status,
  trace,
  timestamp 
FROM 
  `web_instr_load_balancer.requests_20200129` 
LIMIT 10
```

#### Visualizing the log data

From BigQuery, we read data into Colab, where it can be plotted in charts. Colab is an iPython notebook service hosted by Google with many Google Cloud services pre-configured for ease of use. Follow these steps to query the log tables in BigQuery and process the results in Python

1. Open the [Colab](https://colab.research.google.com/github/GoogleCloudPlatform/professional-services/blob/master/examples/web-instrumentation/load_test_analysis.ipynb) sheet in Chrome. 

1. Open the Initialization block if it is not open already. Change the project_id variable to your own project.

1. Execute the code in the Initialization block by clicking the Run icon. You will need to approve access with your Google account

1. Open the Logs Overview block.

1. Execute the code in the Logs Overview block

1. Open the Client Latency block. Change the hour in the WHERE clause to be the hour that you ran the test

1. Execute the code in the Client Latency block

You should see a chart of median client latency similar to the chart below.

![Median Client Latency from Colab Sheet](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/client_latency_median.png)

The Colab sheet uses the Pandas library to hold and plot the BigQuery query results. Pandas wraps MatPlotLib library for plotting the chart. 

To see the details of the client latency, still in the Colab sheet

1. Open the Scatter Plot code block
1. Edit table name for the current date and the hour and minute range for the time of your text
1. Execute the code block

You should see a scatter plot similar to the chart below showing points for the client latency values.

![Scatter Plot for Client latency](https://storage.googleapis.com/gcp-community/tutorials/web-instrumentation/client_latency_scatterr.png)

In this test you will probably not trigger autoscaling. To see autoscaling triggered you can repeat the test with an increased the number of requests sent and  test duration. 

You may not be able to generate sufficient load from one browser to trigger autoscaling. If you increase the number of requests sent sufficiently you may see the Chrome error  net::ERR_INSUFFICIENT_RESOURCES. To drive a more substantial load, you can use 
[Headless Chrome](https://developers.google.com/web/updates/2017/04/headless-chrome)
or [Webdriver](https://selenium.dev/documentation/en/webdriver/)
with multiple clients. Another approach is to use a simple load generator like 
[Locust](https://locust.io/), 
[Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html), or 
[JMeter](http://jmeter.apache.org/)
and simultaneously observe the noisy neighbor impact on an instrumented browser app, as described in this tutorial.

## Other languages and environments

You can run the backend or frontend in other languages and and use the same instrumentation with more scalable tools, such as Apache Bench or Locust. To see the format of the XML HTTP requests that you will need to use:

1. Start a test from Chrome. Say with 5 requests at 1,000 ms intervals.
1. Open up Chrome Developer tools
1. Go to the Network tab
1. Right click a request and click Copy | Copy as cURL

This will give the JSON format needed as well as the headers that can be used directly in cURL, which will be similar to other tools. 

See the [OpenCensus](https://opencensus.io/)
website to get started with other backend languages. For other front end languages, such as Java on Android or Objective C on iOS, you will need to use the OpenTelemetry service, as described above.

If you prefer not to use client libraries to generate traces, you can generate them from your own code by sending HTTP headers following the
[W3C Trace Context](https://www.w3.org/TR/trace-context-1/)
format. This may be preferable on mobile clients where it is important to minimize the size of the application binary. The trace id generated is very useful for correlating logs between front and back end even if you do not use tracing.

If running in a serverless environment like Cloud Run or App Engine flexible environment, you will need to package the 
OpenTelemetry service in the Docker container with a web server like NGINX to forward the trace collection requests to the 
collector.

## Troubleshooting

See the 
[README.md](https://github.com/GoogleCloudPlatform/professional-services/tree/master/examples/web-instrumentation#troubleshooting) file in GitHub for troubleshooting tips.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial:

### Delete the project

The easiest way to eliminate billing is to delete the project that you created for the tutorial.

To delete the project, do the following:

1. In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).

1. In the project list, select the project you want to delete and click **Delete**.

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
* Adapt the app in this tutorial to a Java backend with [Identifying causes of app latency with Stackdriver and OpenCensus](https://cloud.google.com/solutions/identifying-causes-of-app-latency-with-stackdriver-and-opencensus).
* Adapt the app in this tutorial to a Go backend with [Troubleshooting app latency with Cloud Spanner and OpenCensus](https://cloud.google.com/solutions/troubleshooting-app-latency-with-cloud-spanner-and-opencensus).
* Try out other Google Cloud features. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
