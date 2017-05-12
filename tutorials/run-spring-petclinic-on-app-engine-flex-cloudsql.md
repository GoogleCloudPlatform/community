---
title: Run Spring Pet Clinic with CloudSQL on Google App Engine Flexible Environment
description: Learn how to deploy Spring Boot Pet Clinic application to Google App Engine flexible environment and use CloudSQL.
author: jishaa
tags: App Engine Flex, CloudSQL, Spring Boot
date_published: 2017-05-12
---

This tutorial will walk you through getting Spring Pet Clinic application up and running on App Engine Flex with CloudSQL.

### Spring Boot and Spring Pet Clinic
[Spring Boot](https://projects.spring.io/spring-boot/) provides Java developers a quick annotation driven way to deploy services using minimal code.
[Spring Pet Clinic](https://github.com/spring-projects/spring-petclinic) is a popular Spring application that will quickly demonstrate the power of SpringBoot.

### App Engine Flex environment for Java
[App Engine Flex](https://cloud.google.com/appengine/docs/flexible/java/) provide the ability to run your Java applications in Docker containers on GCE machines, with the ability
to have them deployed, monitored and auto-scaled.
We will be using the [Java 8 Runtime environment](https://cloud.google.com/appengine/docs/flexible/java/dev-java-only) for this tutorial.

### CloudSQL
[CloudSQL for MySQL](https://cloud.google.com/sql/docs/mysql/) is a fully managed MySQL database service on GCP.

### Prerequisites
1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

### Prepare
1. Initialize, create an app engine application and authorize `gcloud` for using GCP APIs in your local environment :
```
   gcloud init
   gcloud app create
   gcloud auth application-default login
```
1. Clone and test the Pet Clinic application locally :
```
    git clone https://github.com/spring-projects/spring-petclinic.git
    cd spring-petclinic
    ./mvnw spring-boot:run
```

  Access http://localhost:8080 via your web browser to see the application homepage.

  By default, the application uses an [hsqldb](http://hsqldb.org/), an in-memory database.
  We will now switch from `hsqldb` to using CloudSQL as your database.

### Using CloudSQL as your database

1. Enable the [Cloud SQL API](https://console.cloud.google.com/flows/enableapi?apiid=sqladmin).

1. Create a 2nd Generation CloudSQL (MySQL) instance and set the root user password following the instructions [here](https://cloud.google.com/sql/docs/mysql/create-instance#create-2nd-gen).

1. Create the `petclinic` database.
```
    gcloud beta sql databases create petclinic --instance=INSTANCE_NAME
```
1. Note the `connectionName` of the instance in the format `project-id:zone-id:instance-id`  using
```
   gcloud beta sql instances describe INSTANCE_NAME
```
1. Update `src/main/resources/application-mysql.properties`, replacing INSTANCE_CONNECTION_NAME with the `connectionName` from the previous step.
```
    database=mysql
    spring.datasource.driverClassName=com.mysql.jdbc.Driver
    spring.datasource.url=jdbc:mysql://google/petclinic?cloudSqlInstance=INSTANCE_CONNECTION_NAME&socketFactory=com.google.cloud.sql.mysql.SocketFactory
    spring.datasource.username=root
    spring.datasource.password=my-smart-password
```
1. Update `pom.xml` to include the [Cloud SQL MySQL Socket Factory socket library](https://github.com/GoogleCloudPlatform/cloud-sql-mysql-socket-factory).
```
    <dependency>
        <groupId>com.google.cloud.sql</groupId>
        <artifactId>mysql-socket-factory</artifactId>
        <version>1.0.2</version>
    </dependency>
```
   The socket library allows to connect to your Cloud SQL instance for local testing and in deployment.
1. Restart the SpringBoot application using the sql [profile](http://docs.spring.io/spring-boot/docs/current/maven-plugin/examples/run-profiles.html)
```
   ./mvnw -Drun.profiles=mysql spring-boot:run
```
  Access the application homepage http://localhost:8080 via your web browser and add some data.
1. You can verify the data exists in CloudSQL running queries agains the `petclinic` database using the [Cloud shell](https://cloud.google.com/sql/docs/mysql/quickstart#connect_to_your_instance_using_the_db_client_client_in_the_cloud_shell)


### Deploying to App Engine Flex on GCP
Now that you've tested the application locally, let us deploy this application to the App Engine Flex Environment.
Once deployed, it will be accessible at https://<your-project-id>.appspot.com

1. App Engine provides Maven plugins to make your build and deploy process extremely easy.
   Add the following plugin to your `pom.xml`'s `build` plugins section :
```
  <plugin>
    <groupId>com.google.cloud.tools</groupId>
    <artifactId>appengine-maven-plugin</artifactId>
    <version>1.3.1</version>
  </plugin>
```

1. Create an `app.yaml` under `src/main/appengine` with the contents.
For more on configuring app.yaml, refer to this [resource](https://cloud.google.com/appengine/docs/flexible/java/configuring-your-app-with-app-yaml) :
```
    runtime: java
    env: flex

    resources:
      memory_gb: 2.3

    handlers:
    - url: /.*
      script: this field is required, but ignored
 ```

1. App Engine Flex monitors the health of your application using the `/_ah/health` endpoint.
(Note : a `200` or`404` status is interpreted as application being healthy).
Given Spring Boot automatically provides a [health check endpoint](https://docs.spring.io/spring-boot/docs/current/reference/html/production-ready-endpoints.html#production-ready-health)
, we can hook that up as our health check endpoint.

Update the followign fields in `src/main/resources/application.properties` :
```
   management.contextPath=/_ah
   spring.profiles.active=mysql
```

1. Run the following command to deploy your app :
```
    ./mvnw -DskipTests=true appengine:deploy
```

1. Visit `https://YOUR_PROJECT_ID.appspot.com` to access the Petclinic application now running on GCP.
View the application logs using the [console](https://console.cloud.google.com/logs/viewer).
