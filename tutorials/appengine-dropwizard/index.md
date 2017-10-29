---
title: Deploying Apache Dropwizard applications on Google App Engine
description: Learn how to deploy Apache Dropwizard applications on Google App Engine Flexible environment using custom runtime.
author: agentmilindu
tags: App Engine, Aapche, Dropwizard
date_published: 2017-10-29
---
This tutorial shows how to deploy an [Apache Dropwizard][dropwizard] application
on Google App Engine flexible environment.


##Overview

[Apache Dropwizard][dropwizard] is a Java framework for developing RESTful 
web services which support for configuration management, application metrics,
 logging, operational tools, etc out of the box. 

Deploying Dropwizard applications on Google App Engine
 Flexible Environment is not straightforward as it needs passing arguments 
 to the JAR, like `java -jar app.jar server config.yaml`.
 
This tutorial shows how to make use of Custom runtime to deploy 
Apache Dropwizard application using Docker. This
tutorial assumes that you are familiar with Apache Dropwizard and that you
have installed Docker.

If you don't have a Dropwizard application already, you can check out
 [Getting Started Guide][getting-started] to create a sample 
 Dropwizard application.

[dropwizard]: http://www.dropwizard.io
[getting-started]: http://www.dropwizard.io/1.2.0/docs/getting-started.html
[flexible-custom-runtimes]: https://cloud.google.com/appengine/docs/flexible/custom-runtimes/

## Objectives

1. Create a Dockerfile that bundles JAR file and config.yml
1. Run the Dropwizard app locally with Docker.
1. Deploy the Dropwizard app to Google App Engine flexible environment.

## Costs

This tutorial uses billable components of Google Cloud Platform, including:

- Google App Engine flexible environment

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Preparing the app

1.  Build your application and generate your JAR artefacts.
1.  If you don't have a Fat JAR( a JAR file with all the dependencies bundled together ), 
generate one using a Fat JAR plugin.

    1.  You can use [Apache Maven Shade Plugin][shade]:

        ```
        <project>
          ...
          <build>
            <plugins>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.1.0</version>
                <configuration>
                  <!-- put your configurations here -->
                </configuration>
                <executions>
                  <execution>
                    <phase>package</phase>
                    <goals>
                      <goal>shade</goal>
                    </goals>
                  </execution>
                </executions>
              </plugin>
            </plugins>
          </build>
          ...
        </project>
        ```

    1. Then you can build your app using: 
    
        ```
        mvn package
        ```
        
       This will create a JAR file with all the dependencies of your 
       application bundled together as one fat file.
       
       **Note**: Apache Shader renames your original package JAR 
       `sample-app-1.0-SNAPSHOT.jar` into 
       `original-sample-app-1.0-SNAPSHOT.jar` and create the fat jar
       with the name `sample-app-1.0-SNAPSHOT.jar`

    1.  (Optionally) you can rename the fat jar using: 

            <plugin>
                <artifactId>maven-shade-plugin</artifactId>
                <version>2.4.1</version>
                <configuration>
                    <finalName>uber</finalName>
                </configuration>
            </plugin>
            
        This will create a fat JAR file named `uber.jar` 
        instead `sample-app-1.0-SNAPSHOT.jar`.


## Create a Dockerfile

  Create a file named `Dockerfile` in your project root and add the following:

     FROM gcr.io/google-appengine/openjdk:8
     
     COPY target/uber.jar uber.jar
     COPY config.yml config.yml
     CMD [ "java", "-jar","uber.jar", "server", "config.yml"]
     
  1.  `FROM gcr.io/google-appengine/openjdk:8`:

       This defines what should be the base image for your Docker image.

  1.  `COPY target/uber.jar uber.jar`:
  
        This copies your `uber.jar` into the Docker image.
     
  1.  `COPY config.yml config.yml`:
  
        This copies your `config.yml` into the Docker image.
 
  1.  `CMD [ "java", "-jar","uber.jar", "server", "config.yml"]`:
  
        This defines the command to be executed when running the Docker container, 
        which runs your Dropwizard application on the Docker container.

  **Note**: If you did not rename your fat JAR into `uber.jar`,
     replace `uber.jar` in the Dockerfile definition with you fat JAR name,
     which is like `sample-app-1.0-SNAPSHOT.jar`.


[shade]: https://maven.apache.org/plugins/maven-shade-plugin/

## Run the app locally with Docker

1.  First, you should build your Docker image from the `Dockerfile`:

        docker build -t sample-app .

    or

        docker build -t <your-dockerhub-username>/sample-app .
        
    `-t`  options tell Docker what should be the tag for your Docker image.
    You can give a meaningful name to the tag. 

    **Notes**
    
    * You have to do this only once unless you update your
     `Dockerfile`, `config.yml` or the fat JAR.
    * If you have a Docker Hub or any other Docker registry account 
      or organization and you wish to push your Docker images there, 
      you can prefix the username/organization name with the tag like
      `-t <your-dockerhub-username>/<application-name>`.

1.  Then, you can run the Docker image you just build:

        docker run -p 8080:8080 -t sample-app
      
      or 
      
        docker run -p 8080:8080 -t <your-dockerhub-username>/sample-app
    
1.  Visit [http://localhost:8080](http://localhost:8080) to see the running app.

1.  Press Control+C to stop the app.

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

        runtime: custom
        env: flex

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://[YOUR_PROJECT_ID].appspot.com` to see the deployed app.

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.


## Improvements

You might want access Dropwizard's Admin context which usually runs on 8081 port. 
However, since AppEngine does not allows 8081 port, 
you can do a slight change in config and get both application and admin contexts
to 8080 port.

For that, you can add the following into your config.yml:
    
    server:
      type: simple
      applicationContextPath: /api
      adminContextPath: /admin
      connector:
        type: http
        port: 8080
        
Now you can access the application API endpoints as 
`http://[YOUR_PROJECT_ID].appspot.com/api` and admin API endpoints as 
`http://[YOUR_PROJECT_ID].appspot.com/admin`.