---
title: Deduplicate Pub/Sub Messages Using Dataflow in A Spring Boot Application
description: Use Dataflow's PubsubIO to deduplicate Pub/Sub messages in a Spring Boot application.
author: anguillanneuf
tags: Cloud Pub/Sub, Spring, Spring Cloud GCP, Cloud Dataflow, Java
date_published: 2020-02-29
---


Tianzi Cai | Developer Programs Engineer | Google Cloud


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
   If you have not done it, set your `PROJECT_NAME` environment variable to your GCP project.
   ```shell script
    export PROJECT_NAME=$(gcloud config get-value project)
   ```

1. Clone this repository and navigate to the sample code:

   ```shell script
   git clone https://github.com.GoogleCloudPlatform/pubsub-spring-dedup-messages.git
   cd community/tutorials/pubsub-spring-dedup-messages
   ```

## Bind Cloud Pub/Sub to Your Spring Boot Application

Spring makes use of Spring Cloud Stream binders to send data to a Cloud Pub/Sub topic and receive data from a Cloud Pub/Sub subscription.

Your application will know how to send data from an internal queue to a Cloud Pub/Sub topic if you specify 1). a Spring Cloud Stream source and 2). a Cloud Pub/Sub topic.

### Specify a Spring Cloud Stream source
Spring can recognize a Spring Cloud Stream source as a Supplier bean.

In [App.java](pubsub-spring/src/main/java/com/google/example/App.java):

[embedmd]:# (pubsub-spring/src/main/java/com/google/example/App.java java /  \/\/ The Supplier Bean/ /}/)
```java
  // The Supplier Bean makes the function a valid Spring Cloud Stream source. It
  // sends messages to a Cloud Pub/Sub topic configured with the binding name
  // `sendMessagesForDeduplication-out-0` in application.properties.
  @Bean
  Supplier<Flux<Message<String>>> sendMessagesForDeduplication(
    final EmitterProcessor<Message<String>> frontEndListener) {
    return () -> frontEndListener;
  }
```

### Specify a Cloud Pub/Sub topic for the source
Spring can find the Cloud Pub/Sub topic that your code should publish data to when you provide a topic name in `application.properties` and assign it to a source using an output binder. Here, the output binding name is `sendMessagesForDeduplication-out-0`. For more information, see [Binding and Binding Names].

In [application.properties](pubsub-spring/src/main/resources/application.properties):

[embedmd]:# (pubsub-spring/src/main/resources/application.properties /.*Data going/ /=topicToDataflow/)
```properties
# Data going to Cloud Pub/Sub from a Spring Cloud Stream source defined in the
# functional bean `sendMessagesForDeduplication`. The application will
# create the Cloud Pub/Sub topic `topicToDataflow` if it does not exist.
spring.cloud.stream.bindings.sendMessagesForDeduplication-out-0.destination=topicToDataflow
```

Similarly, your application will know how to receive data from a Cloud Pub/Sub subscription if you specify 1). a Spring Cloud Stream sink and 2). a pair of Cloud Pub/Sub topic and subscription.

### Specify a Spring Cloud Stream sink
Spring can recognize a Spring Cloud Stream sink as a Consumer bean.

In [App.java](pubsub-spring/src/main/java/com/google/example/App.java):

[embedmd]:# (pubsub-spring/src/main/java/com/google/example/App.java java /  \/\/ The Consumer Bean/ /}/)
```java
  // The Consumer Bean makes the function a valid Spring Cloud Stream sink. It
  // receives messages from a Cloud Pub/Sub subscription configured with the binding
  // name `receiveDedupedMessagesFromDataflow-in-0` in application.properties.
  @Bean
  Consumer<Message<String>> receiveDedupedMessagesFromDataflow() {
    return msg -> {
      System.out.println("\tDE-DUPED message: \"" + msg.getPayload() + "\".");
    }
```

### Specify a Cloud Pub/Sub topic and subscription for the sink
Spring can find the Cloud Pub/Sub subscription that your code should receive data from when you provide a subscription name in `application.properties` and assign it to a consumer group of the sink using an input binder. Here, the input binding name is `receiveDedupedMessagesFromDataflow-in-0`. Because a subscription cannot exist without a topic, a topic must also be specified for the sink. Note that only input bindings have consumer groups. For more information, see [Common Binding Properties].

In [application.properties](pubsub-spring/src/main/resources/application.properties):

[embedmd]:# (pubsub-spring/src/main/resources/application.properties /.*Data coming/ /=subscriptionFromDataflow/)
```properties
# Data coming from Cloud Pub/Sub to a Spring Cloud Stream sink defined in the
# functional bean `receiveDedupedMessagesFromDataflow`. The application
# will create the Cloud Pub/Sub topic `topicFromDataflow` and subscription
# `topicFromDataflow.subscriptionFromDataflow` if they do not exist.
spring.cloud.stream.bindings.receiveDedupedMessagesFromDataflow-in-0.destination=topicFromDataflow
spring.cloud.stream.bindings.receiveDedupedMessagesFromDataflow-in-0.group=subscriptionFromDataflow
```
### Run the application
To start your application, navigate to `pubsub-spring/` and run: 

```shell script
mvn spring-boot:run
```

Observe that your app has started successfully by pointing your browser to `localhost:8080`. You should be able to send messages using the form there. At this point, Spring will have automatically created the Cloud Pub/Sub topic that you have specified in `application.properties` to publish your message to. You can view Publish Message Request Count and Publish Message Operation Count in the topic details in [Cloud Console for Pub/Sub Topic] to verify that publishing to Cloud Pub/Sub is successful.  

## Start a Cloud Dataflow Job to Deduplicate Pub/Sub Messages

As a middle process that takes data from a Cloud Pub/Sub topic and publishes processed data to another Cloud Pub/Sub topic, Cloud Dataflow achieves exactly once stream processing by asking the input stream for an `idAttribute`. Using the user-defined key name as this unique record identifier name, Cloud Dataflow can avoid processing messages of the same key multiple times.

In [DedupPubSub.java](pubsubio-dedup/src/main/java/com/google/example/DedupPubSub.java):

[embedmd]:# (pubsubio-dedup/src/main/java/com/google/example/DedupPubSub.java java /  pipeline\n.*1\)./ /;/)
```java
  pipeline
        // 1) Read string messages from a Pub/Sub topic.
        .apply(
            "Read from PubSub",
            PubsubIO.readStrings()
                .fromTopic(options.getInputTopic())
                .withIdAttribute(options.getIdAttribute()))
        // 2) Write string messages to a Pub/Sub topic.
        .apply("Write to PubSub", PubsubIO.writeStrings().to(options.getOutputTopic()));
```

### Run the Dataflow job

To start the Dataflow job,  navigate to `pubsubio-dedup/` and run: 
```shell script
  mvn compile exec:java \
   -Dexec.mainClass=com.google.example.DedupPubSub \
   -Dexec.cleanupDaemonThreads=false \
   -Dexec.args="\
     --project=$PROJECT_NAME \
     --inputTopic=projects/$PROJECT_NAME/topics/topicToDataflow \
     --outputTopic=projects/$PROJECT_NAME/topics/topicFromDataflow \
     --idAttribute=key \
     --runner=DataflowRunner"
```
You can observe the job's progress in the [Cloud Console for Dataflow]. Wait a few minutes for the job status to be "running". Then issue `Ctrl+C` to stop the program locally.

## Observe the Results
Publish a few messages of different keys via the web host and observe deduplicated messages in your terminal.

## Cleanup
1. Use `Ctrl+C` to stop the Spring Boot application and the Dataflow.
1. In the [Cloud Console for Dataflow], select the Dataflow job and stop it. Cancel the pipeline instead of draining it. 
1. Delete the subscriptions followed by the topics in the [Cloud Console for Pub/Sub] or via the command line.
```shell script
gcloud pubsub subscriptions delete topicFromDataflow.subscriptionFromDataflow
gcloud pubsub topics delete topicFromDataflow topicToDataflow
```
## Next Steps
1. Learn more about [Cloud Pub/Sub].
1. A list of [Google Cloud Platform services that integrate with Spring].
1. Using [Cloud Dataflow templates] for stream processing.

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
[Cloud Console for Pub/Sub Topic]: https://console.cloud.google.com/cloudpubsub/topic/
[Cloud Console for Dataflow]: http://console.cloud.google.com/dataflow/
[Cloud Console for Pub/Sub]: https://console.cloud.google.com/cloudpubsub/

[Binding and Binding Names]: https://github.com/spring-cloud/spring-cloud-stream/blob/master/docs/src/main/asciidoc/spring-cloud-stream.adoc#binding-and-binding-names
[Common Binding Properties]: https://github.com/spring-cloud/spring-cloud-stream/blob/master/docs/src/main/asciidoc/spring-cloud-stream.adoc#common-binding-properties
 [Google Cloud Platform services that integrate with Spring]: https://spring.io/projects/spring-cloud-gcp
 [Cloud Dataflow templates]: https://cloud.google.com/dataflow/docs/guides/templates/overview
 
