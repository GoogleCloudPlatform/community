---
title: Deploying Dropwizard applications on Google App Engine
description: Learn how to deploy Dropwizard applications on Google App Engine flexible environment using a custom runtime.
author: agentmilindu
tags: App Engine, Dropwizard
date_published: 2017-10-29
---

Milindu Sanoj Kumarage

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows how to deploy an [Dropwizard][dropwizard] application
on Google App Engine flexible environment.

[Dropwizard][dropwizard] is a Java framework for developing RESTful
web services with support for configuration management, application metrics,
logging, operational tools, and more out of the box.

Deploying Dropwizard applications on Google App Engine flexible environment can
be tricky because it requires you to pass arguments to the JAR, like
`java -jar app.jar server config.yaml` in order to  get the Dropwizard
application running.

This tutorial shows how to make use of Google App Engine flexible environment's
[custom runtime][flexible-custom-runtimes] to deploy a Dropwizard
application using Docker. This tutorial assumes that you are familiar with Dropwizard and that you have installed Docker.

If you don't have a Dropwizard application already, you can check out
[getting started guide][getting-started] to create a sample Dropwizard
application.

[dropwizard]: http://www.dropwizard.io
[getting-started]: http://www.dropwizard.io/1.2.0/docs/getting-started.html
[flexible-custom-runtimes]: https://cloud.google.com/appengine/docs/flexible/custom-runtimes/

## Objectives

1.  Create a Dockerfile that bundles your JAR file and config.yml
1.  Run the Dropwizard app locally with Docker.
1.  Deploy the Dropwizard app to Google App Engine flexible environment.

## Costs

This tutorial uses billable components of Google Cloud, including:

- Google App Engine flexible environment

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  Enable billing for your project.
1.  Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Preparing the app

1.  Build your application and generate your JAR artifacts.
1.  If you don't have a fat JAR (a JAR file with all the dependencies bundled
    together), generate one using a fat JAR plugin.

    1.  You can use [Apache Maven Shade Plugin][shade].

        See [example.pom.xml][pom] for example plugin configuration.

    1.  Then you can build your app using:

            mvn package

        This will create a JAR file with all the dependencies of your
        application bundled together as one fat file.

        **Note**: Apache Shade renames your original package JAR
        `sample-app-1.0-SNAPSHOT.jar` into
        `original-sample-app-1.0-SNAPSHOT.jar` and creates the fat JAR
        with the name `sample-app-1.0-SNAPSHOT.jar`.

    1.  (Optionally) you can rename the fat JAR using:

        See [example.pom.xml][pom] for an example.

        The config in the example will create a fat JAR file named `uber.jar`
        instead of `sample-app-1.0-SNAPSHOT.jar`.

[pom]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-dropwizard/example.pom.xml
[pom2]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-dropwizard/example.pom.xml#L13

## Create a Dockerfile

Create a file named `Dockerfile` in your project root and add the following:

     FROM gcr.io/google-appengine/openjdk:8

     COPY target/uber.jar uber.jar
     COPY config.yml config.yml
     CMD [ "java", "-jar","uber.jar", "server", "config.yml"]

Let's examine the lines in the `Dockerfile`:

The following defines what should be the base image for your Docker image:

    FROM gcr.io/google-appengine/openjdk:8

The following copies your `uber.jar` into the Docker image:

    COPY target/uber.jar uber.jar

The following copies your `config.yml` into the Docker image:

    COPY config.yml config.yml

The following defines the command to be executed when running the Docker
container, which runs your Dropwizard application on the Docker container:

    CMD [ "java", "-jar","uber.jar", "server", "config.yml"]`:

**Note**: If you did not rename your fat JAR to `uber.jar`, replace `uber.jar`
in the `Dockerfile` with your fat JAR name, which is like
`sample-app-1.0-SNAPSHOT.jar`.

[shade]: https://maven.apache.org/plugins/maven-shade-plugin/

## Run the app locally with Docker

1.  First, you should build your Docker image from the `Dockerfile`:

        docker build -t sample-app .

    or

        docker build -t YOUR_DOCKERHUB_USERNAME/sample-app .

    `-t`  options tell Docker what should be the tag for your Docker image.
    You can give a meaningful name to the tag.

    **Notes**

    * You have to do this only once unless you update your `Dockerfile`,
      `config.yml`, or the fat JAR.
    * If you have a Docker Hub or any other Docker registry account or
      organization and you wish to push your Docker images there, you can prefix
      the username/organization name with the tag like
      `-t YOUR_DOCKERHUB_USERNAME/YOUR_APP_NAME`.

1.  Then, you can run the Docker image you just built:

        docker run -p 8080:8080 -t sample-app

    or

        docker run -p 8080:8080 -t YOUR_DOCKERHUB_USERNAME/sample-app

1.  Visit [http://localhost:8080](http://localhost:8080) to see the running app.

1.  Press Ctrl+C to stop the app.

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

        runtime: custom
        env: flex

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://[YOUR_PROJECT_ID].appspot.com` to see the deployed app.

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

## Improvements

You might want to access Dropwizard's Admin context which usually runs on port
`8081`. However, since AppEngine does not allow port `8081`, you can do a slight
change in config and get both application and admin contexts to port `8080`.

For that, you can add the following into your config.yml:

```yaml
server:
  type: simple
  applicationContextPath: /api
  adminContextPath: /admin
  connector:
    type: http
    port: 8080
```

Now you can access the application API endpoint as
`http://[YOUR_PROJECT_ID].appspot.com/api` and admin API endpoint as
`http://[YOUR_PROJECT_ID].appspot.com/admin`.
