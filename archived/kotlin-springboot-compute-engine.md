---
title: Run a Spring Boot application on Compute Engine
description: Learn how to deploy a Kotlin Spring Boot application to Compute Engine.
author: hhariri
tags: Compute Engine, Spring Boot, Kotlin
date_published: 2017-11-01
---

Hadi Hariri | VP of Developer Advocacy | JetBrains

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial demonstrates how to deploy a
[Kotlin](https://kotlinlang.org/) app using the
[Spring Boot](https://projects.spring.io/spring-boot/) framework to
[Compute Engine](https://cloud.google.com/compute/docs/), taking
advantage of Google's deep expertise with scalable infrastructure.

In this tutorial, you create a new Spring Boot application, and then learn how to do the following:

*   Deploy your app to Compute Engine instances.
*   Set up load balancing and autoscaling for your app.

While the tutorial uses Kotlin 1.2 and Spring Boot 2 M7, other releases of
Kotlin and Spring Boot should work without any modifications (other than version
numbers in Gradle files).

This tutorial assumes that you are familiar with Spring Boot and with creating
web applications. For simplicity, the tutorial responds with JSON to a specific
HTTP request, but can be expanded to connect to other Google services or
databases.

## Before you begin

Before running this tutorial, you must set up a Google Cloud
project, install Docker, and install the Cloud SDK.

You can create a project for your Spring Boot application. You can also use
an existing project.

1.  Use the [Cloud Console](https://console.cloud.google.com/) to create or choose
    a project. Remember the project ID; you use it in this
    tutorial. Later commands in this tutorial use `${PROJECT_ID}` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

3.  Visit the [API Library](https://console.cloud.google.com/apis/library) menu
    and enable the Compute Engine API.

Next, complete the following installations:

1.  Install Docker 17.05 or later if you do not already have it. Find
    instructions on the [Docker website](https://www.docker.com/).

2.  Install the [Cloud SDK](https://cloud.google.com/sdk/) if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK. Use
    your project's ID to set the default project for the `gcloud` command-line tool.

3.  Install [JDK 8 or higher](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) if you do not already have it.

## Creating a new Spring Boot app and running it locally

In this section, you create a new Spring Boot app and make sure it runs. If
you already have an app to deploy, you can use it instead.

1.  Use [start.spring.io](https://start.spring.io) to generate a Spring Boot application using the Kotlin language and the 
    Gradle build system.

2.  Download the generated project and save it to a local folder.

3.  Open the project in your an IDE or editor. Create a new source file named
    `MessageController.kt` with the following content:

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

    The package should match that of your group and artifact name.

4.  Make sure you have the correct dependencies in your Gradle file to import
    `RestController`:

        compile("org.springframework.boot:spring-boot-starter-web")

5.  Run the application from the command line using Gradle:

        gradle bootRun

    **Note:** The `gradle bootRun` command is a quick way to build and run the
    application. Later, when you create the Docker image, you need to first
    build the app using the Gradle `build` task and then run it.

6.  Visit `http://localhost:8080/message` in your web browser. Ensure that the
    page returns a valid JSON response. The response should be as follows:

        {
            "text": "Hello from Google Cloud",
            "priority": "High"
        }

## Building a release for deployment

The following sections explain how to use Google Cloud Storage and Container Builder to build a release for deployment.

### Create a Cloud Storage bucket

You use Cloud Storage to store your application's dependencies.

Choose a bucket name (such as `demo-01`), then create the bucket by running
the following command:

    gsutil mb gs://demo-01

### Creating a build to upload to Cloud Storage

You can create a build for deployment using [Container Builder](https://cloud.google.com/container-builder/)
or any [other number of continuous delivery tools](https://cloud.google.com/container-registry/docs/continuous-delivery). The release build can then be uploaded
to Cloud Storage bucket, where a Compute Engine instance can access it.

For the purposes of this tutorial, you can build the release locally and upload
it to Cloud Storage:

1.  Build the Spring Boot application by running the following command from the
    root of your application folder:

        gradle build

2.  Upload the app to Cloud Storage:

        gsutil cp build/libs/* gs://demo-01/demo.jar

## Deploying your application to a single instance

You can now deploy your application to Compute Engine.

Compute Engine instances might provide a startup script that is executed whenever
the instance is started or restarted. You use this to install and start your app.

### Create a startup script

Create a file called `instance-startup.sh` in your application's root directory
and copy the following content to it:

    #!/bin/sh

    # Set the metadata server to the get project id
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

The startup script does the following:

1.  Downloads the JAR which is the Spring Boot application, previously built and
    uploaded to Cloud Storage.
2.  Downloads and installs Java 8.
3.  Runs the Spring Boot application.

The `BUCKET` attribute is set when you create the instance.

### Create and configure a Compute Engine instance

To create a Compute Engine instance, perform the following steps:

1.  Create an instance by running the following command:

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
    access to Google Cloud services, and provides your startup script. It
    also sets an instance attribute with the bucket name.

2.  Check the progress of instance creation:

        gcloud compute instances get-serial-port-output demo-instance \
            --zone us-east1-b

    If the startup script has completed, this command returns `Finished running startup scripts`.

3.  Create a firewall rule to allow traffic to your instance:

        gcloud compute firewall-rules create default-allow-http-8080 \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow port 8080 access to http-server"

4.  Get the external IP address of your instance:

        gcloud compute instances list

5.  To see your application running, visit `http://${IP_ADDRESS}:8080/message`, where
    `${IP_ADDRESS}` is the external address you obtained above.

## Horizontal scaling with multiple instances

Compute Engine can easily scale horizontally. By using a managed instance
group and the Compute Engine autoscaler, Compute Engine can automatically
create new instances of your application when needed, and shut down instances
when demand is low. You can set up an HTTP load balancer to distribute traffic
to the instances in a managed instance group.

### Create a managed instance group

A managed instance group is a group of homogeneous instances based on an
instance template. In this section, you create a group of instances running
your Spring Boot app.

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

2.  Next, create an instance group using the template:

        gcloud compute instance-groups managed create demo-group \
            --base-instance-name demo-group \
            --size 2 \
            --template demo-template \
            --zone us-east1-b

    The `size` parameter specifies the number of instances in the group. You
    can set it to a different value as needed.

3.  If you did not create the firewall rule while configuring a single instance
    above, run the following command to do so:

        gcloud compute firewall-rules create default-allow-http-8080 \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow port 8080 access to http-server"

4.  Get the names and external IP addresses of the created instances:

        gcloud compute instances list

    The managed instances in the group have names that start with the
    base-instance-name, such as `demo-group`. You can use the names to check the
    progress of instance creation as you did above with a single instance, and
    then you can use the IP addresses to see your application running on port
    8080 of each instance.

### Create a load balancer

In this section, you create a load balancer to direct traffic automatically
to available instances in the group:

1.  Create a health check. The load balancer uses a health check to determine
    which instances are capable of serving traffic. The health check simply
    ensures that the server responds:

        gcloud compute http-health-checks create demo-health-check \
            --request-path /message \
            --port 8080

2.  Create a named port. The HTTP load balancer directs traffic to a port
    named `http`, so we map that name to port 8080 to indicate that the
    instances listen on that port:

        gcloud compute instance-groups managed set-named-ports demo-group \
            --named-ports http:8080 \
            --zone us-east1-b

3.  Create a backend service. The backend service is the target for
    load-balanced traffic. It defines the instance group to which traffic
    should be directed, and which health check to use:

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
    service. If you want to load-balance requests between multiple regions or
    groups, you can create multiple backend services:

        gcloud compute url-maps create demo-service-map \
            --default-service demo-service

6.  Create a proxy that receives traffic and forwards it to backend services
    using the URL map:

        gcloud compute target-http-proxies create demo-service-proxy \
            --url-map demo-service-map

7.  Create a global forwarding rule. This ties a public IP address and port to
    a proxy:

        gcloud compute forwarding-rules create demo-http-rule \
            --target-http-proxy demo-service-proxy \
            --ports 80 \
            --global

8.  You are now done configuring the load balancer. It might take a few minutes
    for it to initialize and get ready to receive traffic. You can check on its
    progress by running the following command:

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
more information, refer to the Compute Engine
[autoscaler documentation](https://cloud.google.com/compute/docs/autoscaler/).

### Manage and monitor your deployment

You can use the Cloud Console to monitor load balancing, autoscaling,
and your managed instance group.

In the [Compute Engine](https://console.cloud.google.com/compute/instances)
menu, you can view individual running instances and connect using SSH.
You can manage your instance group and autoscaling configuration using the
[Instance groups](https://console.cloud.google.com/compute/instanceGroups)
menu. You can manage the load-balancing configuration, including URL maps and
backend services, using the
[HTTP load balancing](https://console.cloud.google.com/compute/httpLoadBalancing/list)
menu.

## Cleaning up

After you have finished this tutorial, you can clean up the resources you created
on Google Cloud so you aren't be billed for them going forward. You can delete the resources
individually, or delete the entire project.

### Delete individual resources

1. Delete the load balancer from the Cloud Console
[network services](https://console.cloud.google.com/net-services) menu. Also
delete the related resources when prompted.

1. Delete the Compute Engine instance group from the Cloud Console
[instance groups](https://console.cloud.google.com/compute/instanceGroups) menu.

1. Delete the remaining single instance from the Cloud Console
[instances page](https://console.cloud.google.com/compute/instances).

1. Delete the Cloud Storage bucket hosting your OTP release from the
[Cloud Storage browser](https://console.cloud.google.com/storage/browser).

### Delete the project

To delete your project using the `gcloud` command line-tool, run
the following command:

    gcloud projects delete ${PROJECT_ID}

where `${PROJECT_ID}` is your Google Cloud project ID.

**Warning**: If you used an existing project, deleting the project also deletes
any other work you have in the project. You can't reuse the project ID of a deleted
project. If you created a custom project ID that you plan to use in the future, you
should delete the resources inside the project instead.

## Next steps

[Learn more about managing Compute Engine deployments](https://cloud.google.com/compute/docs/).
