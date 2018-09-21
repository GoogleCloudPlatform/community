---
title: Run a Kotlin Ktor app on Google App Engine Standard
description: Learn how to deploy a Kotlin Ktor app to Google App Engine Standard.
author: bshaffer
tags: App Engine, Kotlin, Ktor, Java, App Engine Standard
date_published: 2018-01-17
---

[Google App Engine Standard](https://cloud.google.com/appengine/docs/standard/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. In this tutorial you'll see how to deploy your
[Kotlin](https://kotlinlang.org/) and [Ktor](https://ktori.io) application to
App Engine Standard.

You will create a new Ktor application, and then you will learn how to:

*   Deploy your application
*   Update your application

While the tutorial uses Kotlin 1.2 and Ktor 2 M7, other releases of Kotlin and Ktor should work
without any modifications (other than version numbers in Maven files). This tutorial does assume you're familiar
with Ktor and creating web applications. For simplicity the tutorial responds with JSON to a specific HTTP request, but can
be built-on to connect to other Google services and/or databases.

## Before you begin

Before running this tutorial, you must set up a Google Cloud Platform project,
and you need to have the Google Cloud SDK installed.

Create a project that will host your Ktor application. You can also reuse
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

## Create your Ktor Application

In this section, you will create a new Ktor app and make sure it runs. If
you already have an app to deploy, you can use it instead.

> You can skip all these steps and just [download][ktor-sample-code] the sample
  application.

[ktor-sample-code]: https://github.com/GoogleCloudPlatform/kotlin-samples/tree/master/appengine/ktor/

1. In an empty project, create the following files:

    * `build.gradle` - The Gradle build file for dependencies and plugins.
    * `src/main/kotlin/HelloApplication.kt` - An example application controller
    * `src/main/resources/application.conf` - Ktor application configuration file
    * `src/main/webapp/WEB-INF/web.xml` - Web configuration file

1. In `build.gradle`, copy the following contents:

    ```gradle
    buildscript {
        // Consider moving these values to `gradle.properties`
        ext.kotlin_version = '1.2.61'
        ext.ktor_version = '0.9.4'
        ext.appengine_version = '1.9.60'
        ext.appengine_plugin_version = '1.3.4'

        repositories {
            jcenter()
        }
        dependencies {
            classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
            classpath "com.google.cloud.tools:appengine-gradle-plugin:$appengine_plugin_version"
        }
    }

    apply plugin: 'kotlin'
    apply plugin: 'war'
    apply plugin: 'com.google.cloud.tools.appengine'

    sourceSets {
        main.kotlin.srcDirs = [ 'src/main/kotlin' ]
    }

    repositories {
        jcenter()
        maven { url "https://kotlin.bintray.com/ktor" }
    }

    dependencies {
        compile "org.jetbrains.kotlin:kotlin-stdlib-jdk8:$kotlin_version"
        compile "io.ktor:ktor-server-servlet:$ktor_version"
        compile "io.ktor:ktor-html-builder:$ktor_version"

        providedCompile "com.google.appengine:appengine:$appengine_version"
    }

    kotlin.experimental.coroutines = 'enable'

    task run(dependsOn: appengineRun)
    ```

1. In `src/main/kotlin/HelloApplication.kt`, copy the following contents:

    ```kt
    package com.example.demo

    import io.ktor.application.*
    import io.ktor.features.*
    import io.ktor.html.*
    import io.ktor.routing.*
    import kotlinx.html.*

    // Entry Point of the application as defined in resources/application.conf.
    // @see https://ktor.io/servers/configuration.html#hocon-file
    fun Application.main() {
        // This adds Date and Server headers to each response, and allows custom additional headers
        install(DefaultHeaders)
        // This uses use the logger to log every call (request/response)
        install(CallLogging)

        // Registers routes
        routing {
            // Here we use a DSL for building HTML on the route "/"
            // @see https://github.com/Kotlin/kotlinx.html
            get("/") {
                call.respondHtml {
                    head {
                        title { +"Ktor on Google App Engine Standard" }
                    }
                    body {
                        p {
                            +"Hello there! This is Ktor running on Google Appengine Standard"
                        }
                    }
                }
            }
        }
    }
    ```

1. In `src/main/resources/application.conf`, copy the following contents:

    ```conf
    ktor {
        application {
            modules = [ com.example.demo.HelloApplicationKt.main ]
        }
    }
    ```
1. In `src/main/webapp/WEB-INF/web.xml`, copy the following contents:

    ```xml
    <?xml version="1.0" encoding="ISO-8859-1" ?>
    <web-app xmlns="http://java.sun.com/xml/ns/javaee" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://java.sun.com/xml/ns/javaee http://java.sun.com/xml/ns/javaee/web-app_3_0.xsd" version="3.0">
        <servlet>
            <display-name>KtorServlet</display-name>
            <servlet-name>KtorServlet</servlet-name>
            <servlet-class>io.ktor.server.servlet.ServletApplicationEngine</servlet-class>
            <!-- path to application.conf file, required -->
            <init-param>
                <param-name>io.ktor.config</param-name>
                <param-value>application.conf</param-value>
            </init-param>
        </servlet>
        <servlet-mapping>
            <servlet-name>KtorServlet</servlet-name>
            <url-pattern>/</url-pattern>
        </servlet-mapping>
    </web-app>
    ```

Now you have a basic Ktor app set up. You can go ahead and run this locally,
but  but let's add App Engine configuration and

## Running your application locally with the App Engine plugin

For running your application and deploying it to production, you will use
the [App Engine plugin for Gradle](https://cloud.google.com/appengine/docs/standard/java/tools/gradle).

1. Add the following file to your project

    * `src/main/webapp/WEB-INF/appengine-web.xml` - App Engine configuration file

1. In `src/main/webapp/WEB-INF/appengine-web.xml`, copy the following contents:

    ```xml
    <?xml version="1.0" encoding="utf-8"?>
    <appengine-web-app xmlns="http://appengine.google.com/ns/1.0">
        <threadsafe>true</threadsafe>
        <runtime>java8</runtime>
    </appengine-web-app>
    ```

1. Now you can run the application from the command line using the following command:

    ```sh
    ./gradlew appengineRun
    ```

1. Open the browser and you should see the "Hello World" message when accessing
http://localhost:8080/.

## Deploy your application

1.  Run the following command to deploy your app:

    ```sh
    ./gradlew appengineDeploy
    ```

    If this is the first time you have deployed to App Engine in this project,
    `gcloud` will prompt you for a region. You may choose the default of
    "us-central", or select a region close to your location.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

    **Note**: If the command fails with `Google Cloud SDK could not be found`, make sure the environment
    variable `GOOGLE_CLOUD_SDK_HOME` is set to the root directory of where you installed the Google Cloud SDK.

1.  Once the deploy command has completed, you can run the following to see your
app running in production on App Engine in the browser:

    ```sh
    gcloud app browse
    ```

## Update your application

Make a simple change and redeploy.

1.  Add the following after the `get("/") { ... }` function call in `HelloApplication.kt`:

    ```kt
    get("/demo") {
        call.respondHtml {
            head {
                title { +"Ktor on Google App Engine Standard" }
            }
            body {
                p {
                    +"It's another route!"
                }
            }
        }
    }
    ```

1.  Run the deployment command again:

    ```sh
    ./gradlew appengineDeploy
    ```

1.  View your changes live by running:

    ```sh
    gcloud app browse
    ```

    Now you can browse to `/demo` to see the new route you added!

## Integrate your application with Stackdriver Logging

The following will walk you through adding [Stackdriver Logging][stackdriver]
to your application.

1. Add the following file to your project

    * `src/main/resources/logback.xml` - Application logging configuration file
    * `src/main/webapp/WEB-INF/logging.properties` - File which specifies the appropriate log level


1. In `src/main/resources/logback.xml`, copy the following contents:

    ```xml
    <configuration>
        <!-- Stack Driver Appender -->
        <!-- See Config here: https://cloud.google.com/logging/docs/setup/java#wzxhzdk57wzxhzdk58logback_appender_for_product_name -->
        <appender name="CLOUD" class="com.google.cloud.logging.logback.LoggingAppender">
            <!-- Optional : filter logs at or above a level -->
            <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
                <level>INFO</level>
            </filter>
            <log>application.log</log> <!-- Optional : default java.log -->
            <flushLevel>WARN</flushLevel> <!-- Optional : default ERROR -->
        </appender>
        <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
            <encoder>
                <pattern>%d{YYYY-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
            </encoder>
        </appender>
        <root level="trace">
            <!-- Add Console output for local dev -->
            <appender-ref ref="STDOUT"/>
            <!-- Add Cloud Appender to root output-->
            <appender-ref ref="CLOUD" />
        </root>
    </configuration>
    ```

1. In `src/main/webapp/WEB-INF/logging.properties`, copy the following contents:

    ```properties
    .level = INFO
    ```

1. Modify `build.gradle` and add the following line under `buildscript`:

    ```gradle
    ext.gce_logback_version = '0.60.0-alpha'
    ```

1. Again modify `build.gradle` and add the following line under `dependencies`:

    ```gradle
    compile "com.google.cloud:google-cloud-logging-logback:$gce_logback_version"
    ```

1. Modify `src/main/webapp/WEB-INF/appengine-web.xml` and add the following
under `appengine-web-app`:

    ```xml
    <system-properties>
        <property name="java.util.logging.config.file" value="WEB-INF/logging.properties"/>
    </system-properties>
    ```

1.  Run the deployment command again:

    ```sh
    ./gradlew appengineDeploy
    ```

1.  View your changes live by running:

    ```sh
    gcloud app browse
    ```

Now you can visit the [Logging Console][logging-console] and see request logs
when your application is requested.

[stackdriver]: https://cloud.google.com/logging/
[logging-console]: https://console.cloud.google.com/logs

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
