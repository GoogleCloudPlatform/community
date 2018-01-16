---
title: Run a Spring Boot application on Google Compute Engine
description: Learn how to deploy a Kotlin Spring Boot application to Compute Engine.
author: hhariri
tags: Compute Engine, Spring Boot, Kotlin
date_published: 2017-11-01
---

This tutorial helps you get started deploying your
[Kotlin](https://kotlinlang.org/) app using the
[Spring Boot](https://projects.spring.io/spring-boot/) Framework to
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/), taking
advantage of Google's deep expertise with scalable infrastructure.

You will create a new Spring Boot application, and then you will learn how to:

*   Deploy your app to Google Compute Engine instances
*   Set up load balancing and autoscaling for your app

While the tutorial uses Kotlin 1.2 and Spring Boot 2 M7, other releases of Kotlin and Spring Boot should work
without any modifications (other than version numbers in Gradle files). This tutorial does assume you're familiar 
with Spring Boot and creating web applications. For simplicity the tutorial responds with JSON to a specific HTTP request, but can
be built-on to connect to other Google services and/or databases.

## Before you begin

Before running this tutorial, you must set up a Google Cloud Platform project,
and you need to have Docker and the Google Cloud SDK installed.

Create a project that will host your Spring Boot application. You can also reuse
an existing project.

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new Cloud Platform project. Remember the project ID; you will
    need it later. Later commands in this tutorial will use `${PROJECT_ID}` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  Enable billing for your project.

3.  Go to the [API Library](https://console.cloud.google.com/apis/library) in
    the Cloud Console. Use it to enable the following APIs:

    *   Google Compute Engine API

Perform the installations:

1.  Install **Docker 17.05 or later** if you do not already have it. Find
    instructions on the [Docker website](https://www.docker.com/).

2.  Install the **[Google Cloud SDK](https://cloud.google.com/sdk/)** if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK and
    set the default project to the new project you created.

3.  Install [JDK 8 or higher](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) if you do not already have it. 

## Creating a new app and running it locally

In this section, you will create a new Spring Boot app and make sure it runs. If
you already have an app to deploy, you can use it instead.

1. Use [start.spring.io](https://start.spring.io) to generate a Spring Boot application using Kotlin as the language, Gradle as the build system. Alternatively,
you can [download](https://github.com/jetbrains/gcp-samples) the sample application. 

2. Download the generated project and save it to a local folder.

3. Open the resulting project in your favourite IDE or editor and create a new source file named `MessageController.kt` with the following contents:

```kotlin
package com.jetbrains.demo

import org.springframework.web.bind.annotation.*

data class Message(val text: String, val priority: String)

@RestController
class MessageController {
    @RequestMapping("/message")
    fun message(): Message {
        return Message("Hello from Google Cloud", "High")
    }
}
```

The package should match that of your group and artifact name. 

4. Make sure you have the right dependencies in your Gradle file to import `RestController`:

```groovy
	compile("org.springframework.boot:spring-boot-starter-web")
```

5. Run the application from the command line using Gradle:

    gradle bootRun


**Note:** The `gradle bootRun` is a quick way to build and run the application. Later on when creating the Docker image, you'll 
need to first build the app using the Gradle `build` task and then run it.

6. Open the browser and make sure your get a valid JSON response when accessing http://localhost:8080/message. The result should be:

```json
{
"text": "Hello from Google Cloud",
"priority": "High"
}
```    

## Building a release for deployment

### Prepare a Cloud Storage bucket

Create a Cloud Storage bucket for your releases:

1. Choose a bucket name (e.g. demo-01) and run the command to create the bucket

        gsutil mb gs://demo-01

### Creating a build to upload to Cloud Storage

Building a release for deployment can be done using the [Google Container Builder](https://cloud.google.com/container-builder/) or any [other number of tools](https://cloud.google.com/container-registry/docs/continuous-delivery). 
for Continuous Delivery. The release build can then be uploaded by your tool of choice to Cloud Storage Bucket so that it can be accessed via the Compute Engine instance you later create.

For the purposes of this tutorial, you can build the release locally and upload it to Cloud Storage manually:

1. Build the Spring Boot application by executing the following command from the root of your application folder

    gradle build
    
2. Upload it to Cloud Storage by executing the following command from the root of your application folder 

    gsutil cp build/libs/* gs://demo-01/demo.jar

## Deploying your application to a single instance

You can now deploy your application to Google Compute Engine.

Compute Engine instances may provide a startup script that is executed whenever
the instance is started or restarted. You will use this to install and start
your app.

### Create a startup script

Create a file called `instance-startup.sh` in your application's root directory and copy the following content into it:

```bash
#!/bin/sh

# Set the metadata server to the get projct id
PROJECTID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/BUCKET" -H "Metadata-Flavor: Google")

echo "Project ID: ${PROJECTID} Bucket: ${BUCKET}"

# Get the files we need
gsutil cp gs://${BUCKET}/demo.jar .

# Install dependencies
apt-get update
apt-get -y --force-yes install openjdk-8-jdk

# Make Java 8 default
update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java

# Start server
java -jar demo.jar
```

Alternatively, you can [download](https://github.com/JetBrains/gcp-samples/blob/master/google-compute-sample/instance-startup.sh)
a sample annotated script to study and customize.

The startup script:

1. Downloads the JAR which is the Spring Boot application, previously built and uploaded to Cloud Storage
2. Downloads and installs Java 8
3. Runs the Spring Boot Application 

The `BUCKET` attribute will be set when you create the instance. 

### Create and configure a Compute Engine instance

Now you will start a Compute Engine instance.

1.  Create an instance by running:

    gcloud compute instances create demo-instance \
        --image-family debian-9 \
        --image-project debian-cloud \
        --machine-type g1-small \
        --scopes "userinfo-email,cloud-platform" \
        --metadata-from-file startup-script=instance-startup.sh \
        --metadata BUCKET=demo-01 \
        --zone us-east1-b \
        --tags http-server

    This command creates a new instance named `demo-instance`, grants it
    access to Cloud Platform services, and provides your startup script. It
    also sets an instance attribute with the Bucket name. 

2.  Check the progress of instance creation:

        gcloud compute instances get-serial-port-output demo-instance \
            --zone us-east1-b

    If the startup script has completed, you will see the text `Finished
    running startup scripts` in the output.

3.  Create a firewall rule to allow traffic to your instance:

        gcloud compute firewall-rules create default-allow-http-8080 \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow port 8080 access to http-server"

4.  Get the external IP address of your instance:

        gcloud compute instances list

5.  To see your application running, go to `http://${IP_ADDRESS}:8080/message` where
    `${IP_ADDRESS}` is the external address you obtained above.

## Horizontal scaling with multiple instances

Compute Engine can easily scale horizontally. By using a managed instance
group and the Compute Engine Autoscaler, Compute Engine can automatically
create new instances of your application when needed, and shut down instances
when demand is low. You can set up an HTTP load balancer to distribute traffic
to the instances in a managed instance group.

### Create a managed instance group

A managed instance group is a group of homogeneous instances based on an
instance template. Here you will create a group of instances running your
Spring Boot app.

1.  Create an instance template:

        gcloud compute instance-templates create demo-template \
            --image-family debian-9 \
            --image-project debian-cloud \
            --machine-type g1-small \
            --scopes "userinfo-email,cloud-platform" \
            --metadata-from-file startup-script=instance-startup.sh \
            --metadata BUCKET=demo-01 \
            --tags http-server

    Notice that the template provides most of the information needed to create
    instances.

2.  Now create an instance group using that template:

        gcloud compute instance-groups managed create demo-group \
            --base-instance-name demo-group \
            --size 2 \
            --template demo-template \
            --zone us-east1-b

    The `size` parameter specifies the number of instances in the group. You
    can set it to a different value as needed.

3.  If you did not create the firewall rule while configuring a single instance
    above, do so now:

        gcloud compute firewall-rules create default-allow-http-8080 \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow port 8080 access to http-server"

4.  Get the names and external IP addresses of the instances that were created.

        gcloud compute instances list

    The managed instances in the group have names that start with the
    base-instance-name, i.e. `demo-group`. You can use the names to check the
    progress of instance creation as you did above with a single instance, and
    then you can use the IP addresses to see your application running on port
    8080 of each instance.

### Create a load balancer

You will now create a load balancer to direct traffic automatically to
available instances in the group. Follow these steps.

1.  Create a health check. The load balancer uses a health check to determine
    which instances are capable of serving traffic. The health check simply
    ensures that the server responds.

        gcloud compute http-health-checks create demo-health-check \
            --request-path /message \
            --port 8080

2.  Create a named port. The HTTP load balancer directs traffic to a port
    named `http`, so we map that name to port 8080 to indicate that the
    instances listen on that port.

        gcloud compute instance-groups managed set-named-ports demo-group \
            --named-ports http:8080 \
            --zone us-east1-b

3.  Create a backend service. The backend service is the "target" for
    load-balanced traffic. It defines which instance group the traffic should
    be directed to and which health check to use.

        gcloud compute backend-services create demo-service \
            --http-health-checks demo-health-check \
            --global

4.  Add your instance group to the backend service:

        gcloud compute backend-services add-backend demo-service \
            --instance-group demo-group \
            --global \
            --instance-group-zone us-east1-b

5.  Create a URL map. This defines which URLs should be directed to which
    backend services. In this sample, all traffic is served by one backend
    service. If you want to load balance requests between multiple regions or
    groups, you can create multiple backend services.

        gcloud compute url-maps create demo-service-map \
            --default-service demo-service

6.  Create a proxy that receives traffic and forwards it to backend services
    using the URL map.

        gcloud compute target-http-proxies create demo-service-proxy \
            --url-map demo-service-map

7.  Create a global forwarding rule. This ties a public IP address and port to
    a proxy.

        gcloud compute forwarding-rules create demo-http-rule \
            --target-http-proxy demo-service-proxy \
            --ports 80 \
            --global

8.  You are now done configuring the load balancer. It will take a few minutes
    for it to initialize and get ready to receive traffic. You can check on its
    progress by running:

        gcloud compute backend-services get-health demo-service \
            --global

    Continue checking until it lists at least one instance in state `HEALTHY`.

9.  Get the forwarding IP address for the load balancer:

        gcloud compute forwarding-rules list --global

    Your forwarding-rules IP address is in the `IP_ADDRESS` column.

    You can now enter the IP address into your browser and view your
    load-balanced and autoscaled app running on port 80!

### Configure an autoscaler

As traffic to your site changes, you can adjust the instance group size
manually, or you can configure an autoscaler to adjust the size automatically
in response to traffic demands.

Create an autoscaler to monitor utilization and automatically create and delete
instances up to a maximum of 10:

    gcloud compute instance-groups managed set-autoscaling demo-group \
        --max-num-replicas 10 \
        --target-load-balancing-utilization 0.6 \
        --zone us-east1-b

After a few minutes, if you send traffic to the load balancer, you might see
that additional instances have been added to the instance group.

A wide variety of autoscaling policies are available to maintain target CPU
utilization and request-per-second rates across your instance groups. For
more information, see the
[documentation](https://cloud.google.com/compute/docs/autoscaler/).

### Manage and monitor your deployment

You can use the Cloud Platform Console to monitor load balancing, autoscaling,
and your managed instance group.

In the [Compute > Compute Engine](https://console.cloud.google.com/compute/instances)
section, you can view individual running instances and connect using SSH.
You can manage your instance group and autoscaling configuration using the
[Compute > Compute Engine > Instance groups](https://console.cloud.google.com/compute/instanceGroups)
section. You can manage load balancing configuration, including URL maps and
backend services, using the
[Compute > Compute Engine > HTTP load balancing](https://console.cloud.google.com/compute/httpLoadBalancing/list)
section.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them going forward. You
can delete the resources individually, or delete the entire project.

### Delete individual resources

Delete the load balancer on the Cloud Platform Console
[network services page](https://console.cloud.google.com/net-services). Also
delete the related resources when it asks.

Delete the compute engine instance group on the Cloud Platform Console
[instance groups page](https://console.cloud.google.com/compute/instanceGroups).

Delete the remaining single instance on the Cloud Platform Console
[instances page](https://console.cloud.google.com/compute/instances).

Delete the Cloud Storage bucket hosting your OTP release from the
[Cloud Storage browser](https://console.cloud.google.com/storage/browser).

### Delete the project

Alternately, you can delete the project in its entirety. To do so using
the `gcloud` command line tool, run:

    gcloud projects delete ${PROJECT_ID}

where `${PROJECT_ID}` is your Google Cloud Platform project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead.

## Next steps

See the [Compute Engine documentation](https://cloud.google.com/compute/docs/)
for more information on managing Compute Engine deployments.
