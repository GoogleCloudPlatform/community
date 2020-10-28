---
title: Monitoring data from IoT devices with Go and Grafana
description: Learn how to set up a serveless monitoring environment on Google Cloud for IoT devices.
author: leozz37
tags: Cloud Run, Golang, Prometheus, Grafana, IoT, data, metrics
date_published: 2020-10-03
---

In this tutorial, you set up a monitoring environment for IoT devices with an Arduino-based board (ESP32), Grafana, and Google Cloud.

## Objectives

*   Send temperature data from an ESP32 built-in sensor to a temperature topic.
*   Create a Pub/Sub queue to receive that data.
*   Host a service written in Go, Prometheus, and and a Grafana container on Cloud Run.
*   Collect that temperature data, send it to Prometheus, and show it on Grafana.
*   Create a Grafana dashboard.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Run](https://cloud.google.com/run)
*   [Pub/Sub](https://cloud.google.com/pubsub)
*   [IoT Core](https://cloud.google.com/solutions/iot)

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the
[pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Before you begin

This tutorial assumes that you're using an Unix operating system.

This tutorial also requires an [ESP32 board](https://www.espressif.com/en/products/socs/esp32).

The instructions in this tutorial use the [Google Cloud SDK command-line interface](https://cloud.google.com/sdk/install) to set up the environment, but you
can use [Cloud Console](https://console.cloud.google.com/).

## Getting started

First, take a look at the infrastructure used in this tutorial:

![architecture](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/architecture.png)

This tutorial uses the built-in temperature sensor from the ESP32 to send data every 5 seconds to a Pub/Sub service in Google Cloud. This data is processed
by a Go service and sent to Prometheus, and you use Grafana to visualize the data.

Grafana is a visualization tool. Prometheus is a data source for Grafana that collects the data in time series and displays it in a way that Grafana understands.

Because Prometheus can’t collect data directly from Pub/sub, a service is used to send the data to Prometheus.

The author of this tutorial made a [GitHub repository](https://github.com/leozz37/iot-monitoring-gcp-grafana) with all of the code used in this article.

So, it’s time to get your hands dirty!

## Set up Google Cloud

On Google Cloud, you’ll be using IoT Core to manage your devices, Pub/Sub as a messaging system, and Cloud Run to host your containers.

First, let’s set up our project. You’ll need a Google account and a credit card, but don’t worry you won’t be charged for anything (if you don’t do some heavy work), your free trial lasts for 3 months and you have US$300 to spend in any Google Cloud service. But you can always keep an eye on your billing board to not have any surprises on your credit card.

To make things easier, you can export this environment variables and just paste the commands from this tutorial (choose your own names):

```bash
export PROJECT_ID=
export REGION=
export TOPIC_ID=
export SUBSCRIPTION=
export REGISTRY=
export DEVICE_ID=
export USER_NAME=
export IMAGE_NAME=
export SERVICE_NAME=
```

> The export command should look like this:
>
> `export PROJECT_ID=temperature-grafana`

To start, log in with your Google account on CLI, create a project, and select the project created. Open a terminal and type the following commands:

```bash
$ gcloud auth login

$ gcloud projects create $PROJECT_ID

$ gcloud config set project $PROJECT_ID
```

You can check your project dashboard, and if everything goes well, you should see your project there.

![Select Project](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img1.png)

Now let's enable pub/sub and IoT Core services in our project. But before that, you'll need to enable the billing into your project. To do that, run the following command and continue to the browser and link a profile:

```bash
$ open "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"

$ gcloud services enable cloudiot.googleapis.com pubsub.googleapis.com
```

We also need to permit IoT Core to publish into pub/sub service. Since IoT Core is responsible for our devices, and they don’t need to subscribe to any topic, we’re giving them just the publishing role.

```bash
$ gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=serviceAccount:cloud-iot@system.gserviceaccount.com \
    --role=roles/pubsub.publisher
```

Choose a region [here](https://cloud.google.com/compute/docs/regions-zones/). I’m using us-central1, but pick the one that better suits you. We also need a pub/sub topic, a subscription, and a registry.

On MQTT, pub/sub works like an Instagram/Twitter hashtag, where you can publish a post using a hashtag and who is following (or subscribed) to that hashtag, we'll see your post. The same works for MQTT, but the hashtag is the topic, the photo is the message and the people following that topic is the subscription.

A registry is like a bucket for our IoT devices. It allows us to group devices and set properties that they all share, such as connection protocol, data storage location, and Cloud pub/sub topics.

Follow these commands:

```bash
$ gcloud pubsub topics create $TOPIC_ID

$ gcloud pubsub subscriptions create --topic $TOPIC_ID $SUBSCRIPTION

$ gcloud iot registries create $REGISTRY \
    --region=$REGION \
    --event-notification-config=topic=temperature-topic \
    --enable-mqtt-config --enable-http-config
```

You can check your [registries](https://console.cloud.google.com/iot/registries), and if everything goes well, you should see your registry with your topic and subscription there.

![registries](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img2.png)

## Set up the ESP32 device

We’ll be using the Espressif micro-controller ESP32 for its WiFi and a built-in temperature sensor. Also, I’m using the Arduino IDE, so make sure you have it installed and set up for ESP32 usage, if you need some help you can follow this [tutorial](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/).

We need to generate an Elliptic Curve (EC) ES256 private/public key pair for our device authentication. Make sure to generate them into a “safe place”:

```bash
$ openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem

$ openssl ec -in ec_private.pem -pubout -out ec_public.pem
```

Now we have to register our device into Core IoT, so run the following commands:

```bash
$ gcloud iot devices create $DEVICE_ID \
    --region=$REGION \
    --registry=$REGISTRY \
    --public-key="path=./ec_public.pem,type=es256"
```

Install “Google Cloud IoT Core JWT” and lwmMQTT from Joel Garhwller libraries on your Arduino IDE. They’re responsible for connecting, authenticating, and sending messages to GCP.

![arduino libs](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img3.png)

Now let's use the library code example for ESP32-lwmqtt:

![arduino example](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img4.png)

On ciotc_config.h, set your WiFi network and credentials:

```cpp
// Wifi network details
const char *ssid = "SSID";
const char *password = "PASSWORD";// Cloud iot details
const char *project_id = "project-id";
const char *location = "us-central1";
const char *registry_id = "my-registry";
const char *device_id = "my-esp32-device";
```

To get your private_key_str, run the following command at the same directory where you saved your public/private keys and paste the "priv" it into the code:

```bash
$ openssl ec -in ec_private.pem -noout -text
````

PS: The key length should be 32 pairs of hex digits. If your private key is bigger, remove the “00:” and if its smaller add “00:”. It should look like this:

![private-key](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img5.png)

You’ll need to set up your root_cert as well. Do the same steps as previously:

```bash
$ openssl s_client -showcerts -connect mqtt.googleapis.com:8883
```

It should look something like this:

![root-cert](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img6.png)

On Esp32-lwmqtt.ino file, let's do some changes to get the ESP32 temperature. This is how our code looks like:

```cpp
#include "esp32-mqtt.h"

#ifdef __cplusplus
extern "C" {
#endif
  uint8_t temprature_sens_read();
#ifdef __cplusplus
}
#endif

uint8_t temprature_sens_read();

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  setupCloudIoT();
}

unsigned long lastMillis = 0;
void loop() {
  mqtt->loop();
  delay(10);

  if (!mqttClient->connected()) {
    connect();
  }

  
  if (millis() - lastMillis > 5000) {
    lastMillis = millis();

    const float temperature = (temprature_sens_read() - 32) / 1.8;

    String payload =
      String("{\"temperature\":") + String(temperature) + String("}");
    publishTelemetry(payload);
  }
}
```

And a Dockerfile for it:

```docker
FROM golang

COPY . /app
WORKDIR /app

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/resources/service-account-key.json

RUN go mod download

CMD ["go", "run", "pubsub.go"]
```

## Build and deploy with Cloud Build, Cloud Run, and Container Registry

First, we need to enable Cloud Build, Cloud Run, and Container Registry in our project:

```bash
$ gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
```

Now let’s build and push our Golang service Docker image to the Cloud Build:

```bash
$ gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

$ gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/ $IMAGE_NAME \
    --region us-central1 \
    --platform managed \
    --allow-authenticated \
    --port 2112
```

GCP will generate an URL for your container, copy it. You can get it on your terminal or accessing your project on your project [Cloud Run page](https://console.cloud.google.com/run)

![console-link](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img9.png)

Now paste it on your prometheus.yml file, on your targets (remove the https://):

```yml
global:
  scrape_interval:     10s
  evaluation_interval: 10s
  external_labels:
    monitor: 'codelab-monitor'

scrape_configs:
  - job_name: 'temperature'
    scrape_interval: 5s
    static_configs:
    - targets:
      - 'temperature-grafana-utsma6q3sq-uc.a.run.app' # Your project URL
```

Since we can't deploy existing images from Docker Hub to Cloud Run, we need to make a custom Docker image for Prometheus and Grafana, then deploy them. Let's deploy a Prometheus container:

```docker
FROM prom/prometheus
ADD ./prometheus.yml /etc/prometheus/prometheus.yml
EXPOSE 9090
```

Building and submitting to production:

```bash
$ gcloud builds submit --tag gcr.io/$PROJECT_ID/prometheus .

$ gcloud run deploy prometheus --image gcr.io/$PROJECT_ID/prometheus \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 9090
```

Make sure to save the URL generated. Do the same thing for Grafana:

```bash
FROM grafana/grafana
EXPOSE 3000
ENTRYPOINT [ "/run.sh" ]
````

Building and submitting to production:

```bash
$ gcloud builds submit --tag gcr.io/$PROJECT_ID/grafana .

$ gcloud run deploy grafana --image gcr.io/$PROJECT_ID/grafana \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 3000
```

## Use the dashboard to view data

Now you can access your Grafana dashboard through the generated URL. You can log in with the admin login (default user: admin, pass: admin, make sure to change that).

Now we have to set up Grafana to listen to our Prometheus. After logging in, go to "Data Source" on the right menu bar, click on "Add data source" and select Prometheus.

![grafana-data-source](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img10.png)

On the Prometheus data source page, paste the URL to your Prometheus instance on the HTTP > URL and hit "save & test".

![grafana-data-source](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img11.png)

On my [Github repository](https://github.com/leozz37/iot-monitoring-gcp-grafana/blob/master/grafana/grafana.json), there’s a JSON file that will import a Grafana Dashboard. Feel free to use it or create your own. If you looking into creating your dashboards, Grafana uses PromQL for querying metrics data, take a look into its [documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/) for more information.

To import my dashboard, go to the right menu bar, then to Create and Import. Paste the JSON content into the text box and hit load.

Select Prometheus as your data source and boom, you should a dashboard like this one:

![grafana-dashboard](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/img12.png)

Now plug your ESP32 on the USB and you should see the graph going up and down!

![final-gif](https://storage.googleapis.com/gcp-community/tutorials/monitoring-iot-data-grafana/gif1.gif)

And that’s it. You can monitor data from IoT devices anywhere in the world.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete project**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

    ![deleting the project](https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png)

## What's next

- Learn [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/).
- Create your own [Grafana](https://grafana.com/) dashboards.
- Learn more about [Google Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
