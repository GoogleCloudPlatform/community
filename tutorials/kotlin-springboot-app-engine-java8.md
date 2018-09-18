---
title: Run a Kotlin Spring Boot app on Google App Engine Standard
description: Learn how to deploy a Kotlin Spring Boot app to Google App Engine Standard.
author: bshaffer
tags: App Engine, Kotlin, Spring Boot, Java, App Engine Standard
date_published: 2018-01-17
---

[Google App Engine Standard](https://cloud.google.com/appengine/docs/standard/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. In this tutorial you'll see how to deploy your
[Kotlin](https://kotlinlang.org/) and
[Spring Boot](https://projects.spring.io/spring-boot/) application to App Engine
Standard.

You will create a new Spring Boot application, and then you will learn how to:

*   Deploy your application
*   Update your application

While the tutorial uses Kotlin 1.2 and Spring Boot 2 M7, other releases of Kotlin and Spring Boot should work
without any modifications (other than version numbers in Maven files). This tutorial does assume you're familiar
with Spring Boot and creating web applications. For simplicity the tutorial responds with JSON to a specific HTTP request, but can
be built-on to connect to other Google services and/or databases.

## Before you begin

Before running this tutorial, you must set up a Google Cloud Platform project,
and you need to have the Google Cloud SDK installed.

Create a project that will host your Spring Boot application. You can also reuse
an existing project.

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new Cloud Platform project. Remember the project ID; you will
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

1. Use [start.spring.io](https://start.spring.io) to generate a Spring Boot
application.

    * Select **Kotlin** as the language and **Maven** as the build system.
    * Using the Dependency selector, type **GCP Support** and select it.
    * In the same Dependency selector, type **Web** and select first result.
    * Click "Switch to the full version" at the bottom to expand the advanced
      options. Under **Packaging** select **War** in the dropdown.

    > Alternatively, you can [download](https://github.com/GoogleCloudPlatform/kotlin-samples/tree/master/appengine/springboot/) the sample application.

1. Download the generated project and save it to a local folder.

1. Open the resulting project in your favourite IDE or editor and create a new
source file `MessageController.kt` in the directory
`src/main/kotlin/com/example/demo` with the following contents:
    ```kt
    package com.example.demo

    import org.springframework.web.bind.annotation.RequestMapping
    import org.springframework.web.bind.annotation.RestController

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

1.  Edit the file named `DemoApplication.kt` in
    `src/main/kotlin/com/example/demo` and replace its contents with the
    following:
    ```kt
    package com.example.demo

    import org.springframework.boot.autoconfigure.SpringBootApplication
    import org.springframework.boot.runApplication
    import org.springframework.boot.web.servlet.support.SpringBootServletInitializer

    @SpringBootApplication
    class DemoApplication : SpringBootServletInitializer()

    fun main(args: Array<String>) {
        runApplication<DemoApplication>(*args)
    }
    ```

1. Run the application from the command line using Maven:

        mvn spring-boot:run

1. Open the browser and make sure you get a valid JSON response when accessing http://localhost:8080/message. The result should be:
    ```json
    {
      "text": "Hello from Google Cloud",
      "priority": "High"
    }
    ```

## Deploy your application

To deploy your application, you will use an App Engine plugin for Maven which simplifies some of the process. The plugin
is also [available for Gradle](https://cloud.google.com/appengine/docs/standard/java/tools/gradle).

1.  Create a file called `appengine-web.xml` in a new folder `src/main/webapp/WEB-INF` with the following contents:
    ```xml
    <?xml version="1.0" encoding="utf-8"?>
    <appengine-web-app xmlns="http://appengine.google.com/ns/1.0">
        <threadsafe>true</threadsafe>
        <runtime>java8</runtime>
    </appengine-web-app>
    ```

1.  Add the following entry to the `plugins` section of your `pom.xml` file to
    configure the [Google Cloud plugin](https://cloud.google.com/appengine/docs/standard/java/tools/maven):
    ```xml
    <plugin>
        <groupId>com.google.cloud.tools</groupId>
        <artifactId>appengine-maven-plugin</artifactId>
        <version>1.3.1</version>
    </plugin>
    ```

1.  Run the following command to deploy your app:

        mvn appengine:deploy

    If this is the first time you have deployed to App Engine in this project,
    `gcloud` will prompt you for a region. You may choose the default of
    "us-central", or select a region close to your location.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

    **Note**: If the command fails with `Google Cloud SDK could not be found`, make sure the environment
    variable `GOOGLE_CLOUD_SDK_HOME` is set to the root directory of where you installed the Google Cloud SDK.

1.  Once the deploy command has completed, you can run

        gcloud app browse

    to see your app running in production on App Engine in the browser. Not however that this application does not
    respond to the root endpoint. Once the browser is open with the correct URL, you need to append `/message` to it.

## Update your application

Make a simple change and redeploy.

1.  Change the text returned from the `message()` function to

    "Hello from Google App Engine"

1.  Run the deployment command again:

        mvn appengine:deploy

1.  View your changes live by running:

        gcloud app browse

    Remember to add `/message` to the URL.

## Clean up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. To clean
up the resources, you can delete the project or stop the App Engine service.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. To do so using `gcloud`, run:

    gcloud projects delete [PROJECT_ID]

where `[PROJECT_ID]` is your Google Cloud Platform project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that
use the project ID, such as an appspot.com URL, remain available.

### Stopping App Engine services

To disable an App Engine service:

1.  In the Cloud Platform Console, go to the
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

See the [App Engine documentation](https://cloud.google.com/appengine/docs/standard/java/)
for more information on App Engine features including scaling, health checks,
and infrastructure customization.
