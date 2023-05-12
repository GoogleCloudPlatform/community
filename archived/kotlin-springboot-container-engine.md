---
title: Run a Kotlin Spring Boot application on Google Kubernetes Engine
description: Learn how to deploy a Kotlin Spring Boot application in containers using Google Kubernetes Engine.
author: hhariri
tags: Kubernetes, Container Engine, Kotlin, Spring Boot, Docker
date_published: 2018-01-05
---

Hadi Hariri | JetBrains

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial helps you get started deploying your
[Kotlin](https://kotlinlang.org/) app using the
[Spring Boot](https://projects.spring.io/spring-boot/) Framework to
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/),
Google's hosting solution for containerized applications. Google Kubernetes Engine,
earlier known as *Google Container Engine*, is based on the popular open-source
[Kubernetes](https://kubernetes.io/) system, and leverages Google's deep
expertise with container-based deployments.

You will create a new Spring Boot application, and then you will learn how to:

*   Create a Docker image file that will be used to build and run your app
*   Deploy your app on Google Kubernetes Engine
*   Scale and update your app using Kubernetes

While the tutorial uses Kotlin 1.2 and Spring Boot 2 M7, other releases of Kotlin and Spring Boot should work
without any modifications (other than version numbers in Gradle files). This tutorial does assume you're familiar
with Spring Boot and creating web applications. For simplicity the tutorial responds with JSON to a specific HTTP request, but can
be built-on to connect to other Google services and/or databases.

## Before you begin

Before running this tutorial, you must set up a Google Cloud project,
and you need to have Docker and the Google Cloud SDK installed.

Create a project that will host your Spring Boot application. You can also reuse
an existing project.

1.  Use the [Cloud Console](https://console.cloud.google.com/)
    to create a new Google Cloud project. Remember the project ID; you will
    need it later. Later commands in this tutorial will use `${PROJECT_ID}` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  Enable billing for your project.

3.  Go to the [API Library](https://console.cloud.google.com/apis/library) in
    the Cloud Console. Use it to enable the following APIs:
    *   Google Cloud Container Builder API
    *   Google Container Engine API

Perform the installations:

1.  Install **Docker 17.05 or later** if you do not already have it. Find
    instructions on the [Docker website](https://www.docker.com/).

2.  Install the **[Google Cloud SDK](https://cloud.google.com/sdk/)** if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK and
    set the default project to the new project you created.

3.  Install the Kubernetes component of the Google Cloud SDK:

        gcloud components install kubectl

4.  Install [JDK 8 or higher](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) if you do not already have it.

## Creating a new app and running it locally

In this section, you will create a new Spring Boot app and make sure it runs. If
you already have an app to deploy, you can use it instead.

1.  Use [start.spring.io](https://start.spring.io) to generate a Spring Boot
    application using Kotlin as the language, Gradle as the build system.

2.  Download the generated project and save it to a local folder.

3.  Open the resulting project in your favourite IDE or editor and create a new
    source file named `MessageController.kt` with the following contents:

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

4.  Make sure you have the right dependencies in your Gradle file to import `RestController`:

        compile("org.springframework.boot:spring-boot-starter-web")

5.  Run the application from the command line using Gradle:

        gradle bootRun

    **Note:** The `gradle bootRun` is a quick way to build and run the
    application. Later on when creating the Docker image, you'll need to first
    build the app using the Gradle `build` task and then run it.

6.  Open the browser and make sure your get a valid JSON response when accessing
    http://localhost:8080/message. The result should be:

        {
            "text": "Hello from Google Cloud",
            "priority": "High"
        }

## Dockerizing your application

The next step is to produce a Docker image that builds and runs your
application in a Docker container. You will define this image using a
Dockerfile.

### Creating a Dockerfile

Various considerations go into designing a good Docker image. The Dockerfile
used by this tutorial builds a release and runs it with Alpine Linux.
If you are experienced with Docker, you can customize your image.

1.  Create a file called `Dockerfile` in your project directory and copy the
    following content into it:

        FROM openjdk:8-jdk-alpine
        VOLUME /tmp
        RUN mkdir /work
        COPY . /work
        WORKDIR /work
        RUN /work/gradlew build
        RUN mv /work/build/libs/*.jar /work/app.jar
        ENTRYPOINT ["java","-Djava.security.egd=file:/dev/./urandom","-jar","/work/app.jar"]

2.  Create a file called `.dockerignore` in your project directory and copy the
    following content into it:

        .gradle
        build
        out


The Dockerfile performs a series of steps.

1. It creates a `work` folder where sources will be copied to and built from.
2. It then copies the sources from the local file system (which should be your project folder) to the container.
3. It sets the working directory to the `work` folder created and then runs the Gradle wrapper command (`gradlew`) to build the project. This wrapper
automatically downloads Gradle and then builds the project.
4. Once built, it then copies the output of the `jar` to the `work` folder
ready for execution when invoking `docker run`.

### Test the Dockerfile

Build the image locally and test running your application from the image:

    docker build --no-cache -t demo .
    docker run -it --rm -p 8080:8080 demo

The period at the end of the `docker build` command is required. It denotes the
root directory of the application you are building.

Visit [http://localhost:8080/message](http://localhost:8080/message) to see the application
respond running locally from your Docker image.

## Deploying your application

Now you're ready to deploy your application to Google Kubernetes Engine!

### Build the production image

To deploy the app, you will use
[Google Cloud Container Build](https://cloud.google.com/container-builder/)
service to build your Docker image in the cloud and store the resulting Docker
image in your project in
[Google Cloud Container Registry](https://cloud.google.com/container-registry/).

Execute the following command to run the build:

    gcloud container builds submit --tag=gcr.io/${PROJECT_ID}/demo:v1 .

Replace `${PROJECT_ID}` with the ID of your Google Cloud project.
The period at the end is required.

After the build finishes, the image `gcr.io/${PROJECT_ID}/demo:v1` is
available. You can list the images you have built in your project using:

    gcloud container images list

You can even push and pull the image directly from your registry. See the
[Container Registry how-to guides](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
for more details.

### Create a cluster

Google Kubernetes Engine lets you create Kubernetes clusters to host your application.
These are clusters of VMs in the cloud, managed by a Kubernetes server.

1.  Choose a cluster name. For the rest of these instructions, I'll assume that
    name is "demo-cluster".

1.  Create the cluster.

        gcloud container clusters create demo-cluster --num-nodes=2

    This command creates a cluster of two machines. You can choose a different
    size, but two is a good starting point.

    It might take several minutes for the cluster to be created. You can check
    the cloud console at http://cloud.google.com/console, under the Kubernetes
    Engine section, to see that your cluster is running. You will also be able
    to see the individual running VMs under the Compute Engine section. Note
    that once the cluster is running, you will be charged for the VM usage.

1.  Configure the `gcloud` command-line tool to use your cluster by default, so
    you don't have to specify it every time for the remaining `gcloud` commands.

        gcloud config set container/cluster demo-cluster

    Replace the name if you named your cluster differently.

### Deploy to the cluster

A production deployment comprises two parts: your Docker container, and a
front-end load balancer (which also provides a public IP address.)

We'll assume that you built the image to `gcr.io/${PROJECT_ID}/demo:v1` and
you've created the Kubernetes cluster as described above.

1.  Create a deployment:

        kubectl run demo --image=gcr.io/${PROJECT_ID}/demo:v1 --port 8080

    This runs your image on a Kubernetes pod, which is the deployable unit in
    Kubernetes. The pod opens port 8080, which is the port your Spring Boot
    application is listening on.

    You can view the running pods using:

        kubectl get pods

1.  Expose the application by creating a load balancer pointing at your pod:

        kubectl expose deployment demo --type=LoadBalancer --port 80 --target-port 8080

    This creates a service resource pointing at your running pod. It listens
    on the standard HTTP port 80, and proxies back to your pod on port 8080.

1.  Obtain the IP address of the service by running:

        kubectl get service

    Initially, the external IP field will be pending while Google Kubernetes Engine
    procures an IP address for you. If you rerun the `kubectl get service`
    command repeatedly, eventually the IP address will appear. You can then
    point your browser at that URL to view the running application.

Congratulations! Your application is now up and running!

## Scaling and updating your application

You'll now explore a few of the basic features of Kubernetes for managing your
running app.

### Set the replica count

Initially your deployment runs a single instance of your application. You can
add more replicas using the `kubectl scale` command. For example, to add two
additional replicas (for a total of three), run:

    kubectl scale deployment demo --replicas=3

Once the additional replicas are running, you can see the list of three pods
by running:

    kubectl get pods

Kubernetes automatically allocates your running pods on the virtual machines
in your cluster. You can configure pods in your deployment with specific
resource requirements such as memory and CPU. See the
[Kubernetes documentation](https://kubernetes.io/docs/home/) for more details.

### Update your application

After you make a change to your app, redeploying is just a matter of
building a new image and pointing your deployment to it.

1.  Make a change to the app. (For example, modify the front page template.)

1.  Perform a new build with a new version tag `v2`:

        gcloud container builds submit --tag=gcr.io/${PROJECT_ID}/demo:v2 .

    Now you have two builds stored in your project, `demo:v1` and `demo:v2`.
    In general it's good practice to set the image tag for each build to a
    unique build number. This will let you identify and deploy any build,
    making updates and rollbacks easy.

1.  Set the deployment to use the new image:

        kubectl set image deployment/demo demo=gcr.io/${PROJECT_ID}/demo:v2

    This performs a rolling update of all the running pods.

1.  You can roll back to the earlier build by calling `kubectl set image`
    again, specifying the earlier build tag.

        kubectl set image deployment/demo demo=gcr.io/${PROJECT_ID}/demo:v1

**Note:** If a deployment gets stuck because an error in the image prevents
it from starting successfully, you can recover by undoing the rollout. See the
[Kubernetes deployment documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
for more info.

## Clean up

After you've finished this tutorial, clean up the resources you created
on Google Cloud so you won't be billed for them going forward. To
clean, either delete your Google Kubernetes Engine resources, or
delete the entire project.

### Deleting Google Kubernetes Engine resources

To delete your app from Google Kubernetes Engine, you must remove both the load
balancer and the Google Kubernetes Engine cluster.

1.  Delete the service, which deallocates the load balancer:

        kubectl delete service demo

1.  The load balancer will be deleted asynchronously. Wait for that process to
    complete by monitoring the output of:

        gcloud compute forwarding-rules list

    The forwarding rule will disappear when the load balancer is deleted.

1.  Delete the cluster, which deletes the resources used by the cluster,
    including virtual machines, disks, and network resources:

        gcloud container clusters delete demo-cluster

### Deleting the project

Alternately, you can delete the project in its entirety. To do so using the
`gcloud` tool, run:

    gcloud projects delete ${PROJECT_ID}

where `${PROJECT_ID}` is your Google Cloud project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that
use the project ID, such as an appspot.com URL, remain available.

## Next steps

If you want to procure a static IP address and connect your domain name, you
might find [this tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/configuring-domain-name-static-ip)
helpful.

See the [Google Kubernetes Engine documentation](https://cloud.google.com/kubernetes-engine/docs/)
for more information on managing Google Kubernetes Engine clusters.

See the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more
information on managing your application deployment using Kubernetes.
