---
title: Run Spring Pet Clinic with Cloud SQL on Google App Engine Flexible Environment
description: Learn how to deploy Spring Boot Pet Clinic application to Google App Engine Flexible environment and use Cloud SQL.
author: jabubake
tags: App Engine, Cloud SQL, Spring Boot
date_published: 2017-05-12
---

This tutorial will walk you through getting the Spring Pet Clinic application up and running on App Engine flexible environment with Cloud SQL.

### Spring Boot and Spring Pet Clinic
[Spring Boot](https://projects.spring.io/spring-boot/) provides Java developers a quick, annotation driven way to deploy services using minimal code.
[Spring Pet Clinic](https://github.com/spring-projects/spring-petclinic) is a popular Spring application that will quickly demonstrate the power of Spring Boot.

### App Engine flexible environment for Java
[App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/java/) provides the ability to run your Java applications in Docker containers on Google Compute Engine machines, with the ability
to have them deployed, monitored and auto-scaled.
We will be using the [Java 8 runtime environment](https://cloud.google.com/appengine/docs/flexible/java/dev-java-only) for this tutorial.

### Cloud SQL
[Cloud SQL for MySQL](https://cloud.google.com/sql/docs/mysql/) is a fully managed MySQL database service on Google Cloud Platform (GCP).

### Prerequisites
1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

### Prepare
1. Initialize the Cloud SDK, create an App Engine application, and authorize the Cloud SDK for using GCP APIs in your local environment:
```
   gcloud init
   gcloud app create
   gcloud auth application-default login
```
1. Clone and test the Pet Clinic application locally:
```
    git clone https://github.com/spring-projects/spring-petclinic.git
    cd spring-petclinic
    ./mvnw spring-boot:run
```

  Access http://localhost:8080 via your web browser to see the application homepage.

  By default, the application uses an in-memory [HyperSQL database](http://hsqldb.org/).
  You will now switch from HyperSQL to using Cloud SQL as your database.

### Using Cloud SQL as your database

1. Enable the [Cloud SQL API](https://console.cloud.google.com/flows/enableapi?apiid=sqladmin).

1. Create a Second Generation Cloud SQL (MySQL) instance and set the root user password following [these instructions](https://cloud.google.com/sql/docs/mysql/create-instance#create-2nd-gen).

1. Create the `petclinic` database.
```
    gcloud beta sql databases create petclinic --instance=INSTANCE_NAME
```
1. Get the `connectionName` of the instance in the format `project-id:zone-id:instance-id` by running the following command:
```
   gcloud beta sql instances describe INSTANCE_NAME
```
1. Update `src/main/resources/application-mysql.properties`, replacing INSTANCE_CONNECTION_NAME with the `connectionName` from the previous step:
```
    database=mysql
    spring.datasource.driverClassName=com.mysql.jdbc.Driver
    spring.datasource.url=jdbc:mysql://google/petclinic?Cloud SQLInstance=INSTANCE_CONNECTION_NAME&socketFactory=com.google.cloud.sql.mysql.SocketFactory
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
   The socket library allows you to connect to your Cloud SQL instance for local testing and deployment.
1. Restart the Spring Boot application using the mysql [profile](http://docs.spring.io/spring-boot/docs/current/maven-plugin/examples/run-profiles.html):
```
   ./mvnw -Drun.profiles=mysql spring-boot:run
```
  Access the application homepage http://localhost:8080 via your web browser and add some data.
1. You can verify the data exists in Cloud SQL by running queries agains the `petclinic` database using the [Cloud Shell](https://cloud.google.com/sql/docs/mysql/quickstart#connect_to_your_instance_using_the_db_client_client_in_the_cloud_shell).


### Deploying to App Engine flexible environment on GCP
Now that you've tested the application locally, you can deploy the application to the App Engine flexible environment.
Once deployed, it will be accessible at https://<your-project-id>.appspot.com.

1. App Engine flexible environment provides Maven plugins to make your build and deploy process extremely easy.
   Add the following plugin to your `pom.xml`'s `build` plugins section:
```
  <plugin>
    <groupId>com.google.cloud.tools</groupId>
    <artifactId>appengine-maven-plugin</artifactId>
    <version>1.3.1</version>
  </plugin>
```

1. Create an `app.yaml` under `src/main/appengine` with the following contents.
For more on configuring `app.yaml`, refer to [this resource](https://cloud.google.com/appengine/docs/flexible/java/configuring-your-app-with-app-yaml) :
```
    runtime: java
    env: flex

    resources:
      memory_gb: 2.3

    handlers:
    - url: /.*
      script: this field is required, but ignored
 ```

1. App Engine flexible environment monitors the health of your application using the `/_ah/health` endpoint.
(Note : A `200` or`404` status is interpreted as the application being healthy).
Because Spring Boot automatically provides a [health check endpoint](https://docs.spring.io/spring-boot/docs/current/reference/html/production-ready-endpoints.html#production-ready-health),
we can hook that up as our health check endpoint.

Update the following fields in `src/main/resources/application.properties`:
```
   management.contextPath=/_ah
   spring.profiles.active=mysql
```

1. Run the following command to deploy your app:
```
    ./mvnw -DskipTests=true appengine:deploy
```

1. Visit `https://YOUR_PROJECT_ID.appspot.com` to access the Pet Clinic application, now running on GCP.
View the application logs using the [Cloud Platform Console](https://console.cloud.google.com/logs/viewer).
