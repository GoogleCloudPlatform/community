---
title: Run a Kotlin Ktor app on App Engine standard environment
description: Learn how to deploy a Kotlin Ktor app to App Engine standard environment.
author: bshaffer
tags: App Engine, Kotlin, Ktor, Java, App Engine Standard
date_published: 2018-01-17
---

[App Engine standard environment](https://cloud.google.com/appengine/docs/standard/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. In this tutorial you'll see how to deploy your
[Kotlin](https://kotlinlang.org/) and [Ktor](https://ktor.io) application to
App Engine standard environment.

You will create a new Ktor application, and then you will learn how to:

*   Deploy your application
*   Update your application

While the tutorial uses Kotlin 1.2 and Ktor 2 M7, other releases of Kotlin and
Ktor should work without any modifications (other than version numbers in Maven
files). This tutorial does assume you're familiar with Ktor and creating web
applications. For simplicity the tutorial responds with JSON to a specific HTTP
request, but can be built-on to connect to other Google services and/or
databases.

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

1.  In an empty project, create the following files:

    * `build.gradle` - The Gradle build file for dependencies and plugins.
    * `src/main/kotlin/HelloApplication.kt` - An example application controller
    * `src/main/resources/application.conf` - Ktor application configuration file
    * `src/main/webapp/WEB-INF/web.xml` - Web configuration file

1.  In `build.gradle`, copy the following contents:

        buildscript {
            // Consider moving these values to `gradle.properties`
            ext.kotlin_version = '1.2.61'
            ext.ktor_version = '0.9.4'
            ext.appengine_version = '1.9.60'
            ext.appengine_plugin_version = '2.1.0'

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

        appengine.deploy.projectId = 'GCLOUD_CONFIG'
        appengine.deploy.version = 'GCLOUD_CONFIG'

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

1.  In `src/main/kotlin/HelloApplication.kt`, copy the following contents:

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
                            title { +"Ktor on Google App Engine standard environment" }
                        }
                        body {
                            p {
                                +"Hello there! This is Ktor running on App Engine standard environment"
                            }
                        }
                    }
                }
            }
        }

1.  In `src/main/resources/application.conf`, copy the following contents:

        ktor {
            application {
                modules = [ com.example.demo.HelloApplicationKt.main ]
            }
        }

1.  Copy [this XML](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/kotlin-ktor-app-engine-java8/web-example.xml) into `src/main/webapp/WEB-INF/web.xml`.

Now you have a basic Ktor app set up. You can go ahead and run this locally,
but let's add App Engine configuration and run it with the App Engine plugin.

## Running your application locally with the App Engine plugin

For running your application and deploying it to production, you will use
the [App Engine plugin for Gradle](https://cloud.google.com/appengine/docs/standard/java/tools/gradle).

1.  Add the following file to your project

    * `src/main/webapp/WEB-INF/appengine-web.xml` - App Engine configuration file

1.  Copy [this XML](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/kotlin-ktor-app-engine-java8/appengine-web-example.xml) into `src/main/webapp/WEB-INF/appengine-web.xml`.

1.  Now you can run the application from the command line using the following
    command:

        ./gradlew appengineRun

1.  Open the browser and you should see the "Hello World" message when accessing
    http://localhost:8080/.

## Deploy your application

1.  Run the following command to deploy your app:

        ./gradlew appengineDeploy

    If this is the first time you have deployed to App Engine in this project,
    `gcloud` will prompt you for a region. You may choose the default of
    "us-central", or select a region close to your location.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

    **Note**: If the command fails with `Google Cloud SDK could not be found`,
    make sure the environment variable `GOOGLE_CLOUD_SDK_HOME` is set to the
    root directory of where you installed the Google Cloud SDK.

1.  Once the deploy command has completed, you can run the following to see
    your app running in production on App Engine in the browser:

        gcloud app browse

## Update your application

Make a simple change and redeploy.

1.  Add the following after the `get("/") { ... }` function call in
    `HelloApplication.kt`:

        get("/demo") {
            call.respondHtml {
                head {
                    title { +"Ktor on App Engine standard environment" }
                }
                body {
                    p {
                        +"It's another route!"
                    }
                }
            }
        }

1.  Run the deployment command again:

        ./gradlew appengineDeploy

1.  View your changes live by running:

        gcloud app browse

    Now you can browse to `/demo` to see the new route you added!

## Integrate your application with Stackdriver Logging

The following will walk you through adding [Stackdriver Logging][stackdriver]
to your application.

1.  Add the following file to your project

    * `src/main/resources/logback.xml` - Application logging configuration file
    * `src/main/webapp/WEB-INF/logging.properties` - File which specifies the appropriate log level


1.  Copy [this XML](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/kotlin-ktor-app-engine-java8/logback-example.xml) into `src/main/resources/logback.xml`.

1.  In `src/main/webapp/WEB-INF/logging.properties`, add the following:

        .level = INFO

1.  Modify `build.gradle` and add the following line under `buildscript`:

        ext.gce_logback_version = '0.60.0-alpha'

1.  Again modify `build.gradle` and add the following line under `dependencies`:

        compile "com.google.cloud:google-cloud-logging-logback:$gce_logback_version"

1.  Add [this XML](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/kotlin-ktor-app-engine-java8/appengine-web-system-example.xml) to `src/main/webapp/WEB-INF/appengine-web.xml` under
    `appengine-web-app`:

1.  Run the deployment command again:

        ./gradlew appengineDeploy

1.  View your changes live by running:

        gcloud app browse

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
3.  If you deployed to a service other than "default", you can navigate to the
    **Services** page, select the service you want to remove, and click
    **Delete**.
4.  If you have multiple versions running, you can navigate to the **Versions**
    page, select your version and click **Split Traffic** to migrate all traffic
    away from the version you want to stop. Once your version is serving zero
    traffic, select it and click **Stop** or **Delete**.
5.  If you want to stop App Engine entirely, you can navigate to the
    **Settings** page and click **Disable Application**.

## Next steps

See the [App Engine documentation](https://cloud.google.com/appengine/docs/standard/java/)
for more information on App Engine features including scaling, health checks,
and infrastructure customization.
