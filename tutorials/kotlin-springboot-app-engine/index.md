---
title: Run a Kotlin Spring Boot app on the App Engine flexible environment
description: Learn how to deploy a Kotlin Spring Boot app to the App Engine flexible environment.
author: hhariri
tags: App Engine, Kotlin, Spring Boot
date_published: 2018-01-17
---

Hadi Hariri | JetBrains

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

The [App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. Using [Kotlin](https://kotlinlang.org/) and [Spring Boot](https://projects.spring.io/spring-boot/), in this tutorial you'll
see how to deploy your application to App Engine.

You will create a new Spring Boot application, and then you will learn how to:

*   Deploy your application
*   Update your application

While the tutorial uses Kotlin 1.2 and Spring Boot 2 M7, other releases of Kotlin and Spring Boot should work
without any modifications (other than version numbers in Maven files). This tutorial does assume you're familiar
with Spring Boot and creating web applications. For simplicity the tutorial responds with JSON to a specific HTTP request, but can
be built-on to connect to other Google services and/or databases.

## Before you begin

Before running this tutorial, you must set up a Google Cloud project,
and you need to have Docker and the Cloud SDK installed.

Create a project that will host your Spring Boot application. You can also reuse
an existing project.

1.  Use the [Cloud Console](https://console.cloud.google.com/)
    to create a new Google Cloud project. Remember the project ID; you will
    need it later. Later commands in this tutorial will use `[PROJECT_ID]` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  Enable billing for your project.


3.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). Make sure
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

    Version 175.0.0 or later of the SDK is required.

3.  Install [JDK 8 or higher](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) if you do not already have it.

4.  Install [Maven](https://maven.apache.org/install.html).

## Creating a new app and running it locally

In this section, you will create a new Spring Boot app and make sure it runs. If
you already have an app to deploy, you can use it instead.

1.  Use [start.spring.io](https://start.spring.io) to generate a Spring Boot application using Kotlin as the language, 
    Maven as the build system. Alternatively,
    you can [download](https://github.com/jetbrains/gcp-samples) the sample application.

2.  Download the generated project and save it to a local folder.

3.  Open the resulting project in your favourite IDE or editor and create a new source file
    named `MessageController.kt` with the following contents:

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

4.  Make sure you have the right dependencies in your Maven file to import
    `RestController` as seen
    [here](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/kotlin-springboot-app-engine/pom-dependency-example.xml).

5. Run the application from the command line using Maven:

        mvn spring-boot:run

6. Open the browser and make sure you get a valid JSON response when accessing http://localhost:8080/message. The result should be:

        {
            "text": "Hello from Google Cloud",
            "priority": "High"
        }

## Deploy your application

To deploy your application, you will use an App Engine plugin for Maven which simplifies some of the process. The plugin
is also [available for Gradle](https://cloud.google.com/appengine/docs/standard/java/tools/gradle).


1.  Specify the runtime.

    -   If you are using JDK 8, create a file called `app.yaml` in a new folder `src/main/appengine` with the following contents:
    
            runtime: java
            env: flex
            runtime_config:
              jdk: openjdk8
      
        By specifying `runtime: java`, the runtime image `gcr.io/google-appengine/openjdk:8` is automatically selected when you deploy a JAR file. The JDK 
        version is also selected using the `jdk` field.
        
    -   If you are using JDK 11, create a file called `app.yaml` in the root directory (or any other directory configured in the `appengine-maven-plugin`)
        with the following contents:
   
            runtime: java11
       
        **Note**: The `flex` environment is not currently available for Java 11.
   
1.  Add [the following](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/kotlin-springboot-app-engine/pom-plugin-example.xml) plugin entry 
    to the `pom.xml` file to configure the Maven plugin.

1.  Run the following command to deploy your app:

        mvn appengine:deploy

    If this is the first time you have deployed to App Engine in this project,
    `gcloud` will prompt you for a region. You may choose the default of
    "us-central", or select a region close to your location.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

    **Note**: If the command fails with `Google Cloud SDK could not be found`, make sure the environment
    variable `GOOGLE_CLOUD_SDK_HOME` is set to the root directory of where you installed the Google Cloud SDK.

1.  After the `deploy` command has completed, you can run the following command to see your app running in production on App Engine in the browser:

        gcloud app browse

    Note, however, that this application does not respond to the root endpoint. When the browser is open with the correct URL, you need to append
    `/message` to it.

## Update your application

Make a simple change and redeploy.

1.  Change the text returned from the `message()` function to

    "Hello from App Engine"

2.  Run the deployment command again:

        mvn appengine:deploy

3.  View your changes live by running:

        gcloud app browse

    Remember to add `/message` to the URL.

## Clean up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud so you won't be billed for them in the future. To clean
up the resources, you can delete the project or stop the App Engine service.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. To do so using `gcloud`, run:

    gcloud projects delete [PROJECT_ID]

where `[PROJECT_ID]` is your Google Cloud project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that
use the project ID, such as an appspot.com URL, remain available.

### Stopping App Engine services

To disable an App Engine service:

1.  In the Cloud Console, go to the
    [App Engine Versions page](https://console.cloud.google.com/appengine/versions).
2.  Make sure your project is selected. If necessary, pull down the project
    selection dropdown at the top, and choose the project you created for this
    tutorial.
3.  If you deployed to a service other than "default", make sure it is selected
    in the Service dropdown.
4.  Select all the versions you wish to disable and click **Stop** at the top
    of the page. This will free all of the Google Compute Engine resources used
    for this App Engine service.

## Next steps

See the [App Engine documentation](https://cloud.google.com/appengine/docs/flexible/)
for more information on App Engine features including scaling, health checks,
and infrastructure customization.
