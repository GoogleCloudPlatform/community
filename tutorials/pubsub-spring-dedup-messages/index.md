---
title: Deduplicate Pub/Sub Messages Using Dataflow in A Spring Boot Application
description: Use Dataflow's PubsubIO to deduplicate Pub/Sub messages in a Spring Boot application
author: anguillanneuf
tags: Cloud Pub/Sub, Spring, Spring Cloud GCP, Cloud Dataflow, Java
date_published: 2020-02-29
---


Tianzi Cai | Developer Programs Engineer | Google Cloud


## Architecture

## Objectives
- Configure a Spring Boot application to use [Cloud Pub/Sub] as a message broker.
- Use [Cloud Dataflow] to deduplicate messages.

## Before You Begin

1. Install the [Cloud SDK].

1. Create a new Google Cloud project via the
   [*New Project* page],
   or via the `gcloud` command line tool.

   ```shell script
   export PROJECT_NAME=your-google-cloud-project-id
   gcloud projects create $PROJECT_NAME
   ```

1. [Enable billing].

1. Setup the Cloud SDK to your GCP project.

   ```shell script
   gcloud init
   ```

1. [Enable the APIs](https://console.cloud.google.com/flows/enableapi?apiid=dataflow,compute_component,pubsub): Dataflow, Compute Engine, Pub/Sub.

1. Create a service account JSON key via the
   [*Create service account key* page],
   or via the `gcloud` command line tool.
   Here is how to do it through the *Create service account key* page.

   * From the **Service account** list, select **New service account**.
   * In the **Service account name** field, enter a name.
   * From the **Role** list, select **Project > Owner**.
   * Click **Create**. A JSON file that contains your key downloads to your computer.

   Alternatively, you can use `gcloud` through the command line.

   ```shell script
   export PROJECT_NAME=$(gcloud config get-value project)
   export SA_NAME=spring_app
   export IAM_ACCOUNT=$SA_NAME@$PROJECT_NAME.iam.gserviceaccount.com

   # Create the service account.
   gcloud iam service-accounts create $SA_NAME --display-name $SA_NAME

   # Set the role to Project Owner (*).
   gcloud projects add-iam-policy-binding $PROJECT_NAME \
     --member serviceAccount:$IAM_ACCOUNT \
     --role roles/owner

   # Create a JSON file with the service account credentials.
   gcloud iam service-accounts keys create path/to/your/credentials.json \
     --iam-account=$IAM_ACCOUNT
   ```

   > *Note:* The **Role** field authorizes your service account to access resources.
   > You can view and change this field later by using the
   > [GCP Console IAM page].
   > If you are developing a production app, specify more granular permissions than **Project > Owner**.
   > For more information, see
   > [Granting roles to service accounts].

   For more information, see
   [Creating and managing service accounts].

1. Set your `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account key file.

   ```shell script
   export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   ```

1. Clone this repository and navigate to the sample code:

   ```shell script
   git clone https://github.com.GoogleCloudPlatform/pubsub-spring-dedup-messages.git
   cd community/tutorials/pubsub-spring-dedup-messages
   ```

## Bind Cloud Pub/Sub to Your Spring Boot Application

For your Spring Boot application to send data to a Cloud Pub/Sub topic and receive data from a Cloud Pub/Sub subscription, it can make use of Google Cloud Platform-maintained Spring Cloud Stream binders for Cloud Pub/Sub.

Your application will know how to send data from an internal queue to a Cloud Pub/Sub topic if you specify 1). a Spring Cloud Stream source and 2). a Cloud Pub/Sub topic.

#### Specify a Spring Cloud Stream source
Spring can recognize a Spring Cloud Stream source when it is defined as a Supplier bean.

[embedmd]:# (pubsub-spring/src/main/java/com/google/example/App.java /.*@Bean Supplier.*/ /}/)

#### Specify a Cloud Pub/Sub topic for the source
Spring can find (if not find, create) the Cloud Pub/Sub topic that your code should publish data to when you provide a topic name in `application.properties` and associate it with the source by referring to its function name.

[embedmd]:# (pubsub-spring/src/main/java/resources/application.properties /# Data going to Cloud Pub/Sub/ /topicToDataflow/)

Similarly, your application will know how to receive data from a Cloud Pub/Sub subscription if you specify 1). a Spring Cloud Stream sink and 2). a pair of Cloud Pub/Sub topic and subscription.

#### Specify a Spring Cloud Stream sink
Spring can recognize a Spring Cloud Stream sink when it is defined as a Consumer bean.

[embedmd]:# (pubsub-spring/src/main/java/com/google/example/App.java /.*@Bean Consumer.*/ /}/)

#### Specify a Cloud Pub/Sub topic and subscription for the sink
Spring can find (if not find, create) the Cloud Pub/Sub subscription that your code should receive data from when you provide a subscription name in `application.properties` and associate it with the sink by referring to its function name. Because a subscription cannot exist without a topic, and processed messages get published to a topic first, a topic is also specified for the sink.

[embedmd]:# (pubsub-spring/src/main/java/resources/application.properties /# Data coming from Cloud Pub/Sub/ /subscriptionFromDataflow/)

To start your application on a local port, run: 

```shell script
cd pubsub-spring/
mvn spring-boot:run
```

## Start a Dataflow Job to Deduplicate Pub/Sub Messages

```shell script
 mvn compile exec:java \
   -Dexec.mainClass=com.example.DedupPubSub \
   -Dexec.cleanupDaemonThreads=false \
   -Dexec.args="\
     --project=$PROJECT_NAME \
     --inputTopic=projects/$PROJECT_NAME/topics/topicFirst \
     --outputTopic=projects/$PROJECT_NAME/topics/topicSecond \
     --idAttribute=key \
     --runner=DataflowRunner"
```

## Cleanup

## Next Steps

[Cloud Pub/Sub]: https://cloud.google.com/pubsub/docs/
[Cloud Dataflow]: https://cloud.google.com/dataflow/docs/
[Cloud SDK]: https://cloud.google.com/sdk/docs/
[Cloud Shell]: https://console.cloud.google.com/cloudshell/editor/
[*New Project* page]: https://console.cloud.google.com/projectcreate
[Enable billing]: https://cloud.google.com/billing/docs/how-to/modify-project/
[*Create service account key* page]: https://console.cloud.google.com/apis/credentials/serviceaccountkey/
[GCP Console IAM page]: https://console.cloud.google.com/iam-admin/iam/
[Granting roles to service accounts]: https://cloud.google.com/iam/docs/granting-roles-to-service-accounts/
[Creating and managing service accounts]: https://cloud.google.com/iam/docs/creating-managing-service-accounts/