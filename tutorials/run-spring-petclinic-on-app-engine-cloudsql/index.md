---
title: Run Spring Pet Clinic with Cloud SQL on Google App Engine Flexible Environment
description: Learn how to deploy Spring Boot Pet Clinic application to Google App Engine flexible environment and use Cloud SQL.
author: jabubake
tags: App Engine, Cloud SQL, Spring Boot, Java
date_published: 2017-05-12
---

This tutorial will walk you through getting the Spring Pet Clinic application up
and running on App Engine flexible environment with Cloud SQL.

### Spring Boot and Spring Pet Clinic
[Spring Boot][boot] provides Java developers a quick, annotation driven way to
deploy services using minimal code.

[Spring Pet Clinic][clinic] is a popular Spring application that will quickly
demonstrate the power of Spring Boot.

[boot]: https://projects.spring.io/spring-boot/
[clinic]: https://github.com/spring-projects/spring-petclinic

### App Engine flexible environment for Java

[App Engine flexible environment][flexible] provides the ability to run your
Java applications in Docker containers on Google Compute Engine machines, with
the ability to have them deployed, monitored and auto-scaled. We will be using
the [Java 8 runtime environment][runtime] for this tutorial.

[flexible]: /appengine/docs/flexible/java/
[runtime]: /appengine/docs/flexible/java/dev-java-only

### Cloud SQL

[Cloud SQL for MySQL][mysql] is a fully managed MySQL database service on Google
Cloud Platform (GCP).

[mysql]: /sql/docs/mysql/

### Prerequisites

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK][sdk].

[console]: https://console.cloud.google.com/
[sdk]: /sdk

### Prepare

1.  Initialize the Cloud SDK, create an App Engine application, and authorize
    the Cloud SDK for using GCP APIs in your local environment:

        gcloud init
        gcloud app create
        gcloud auth application-default login

1.  Clone and test the Pet Clinic application locally:

        git clone https://github.com/spring-projects/spring-petclinic.git
        cd spring-petclinic
        ./mvnw spring-boot:run

    Access http://localhost:8080 via your web browser to see the application
    homepage. By default, the application uses an in-memory
    [HyperSQL database][hyper]. You will now switch from HyperSQL to using Cloud
    SQL as your database.

[hyper]: http://hsqldb.org/

### Using Cloud SQL as your database

1.  Enable the [Cloud SQL API][api].

1.  Create a Second Generation Cloud SQL (MySQL) instance and set the root user
    password following [these instructions][instructions].

1.  Create the `petclinic` database.

        gcloud beta sql databases create petclinic --instance=INSTANCE_NAME

1.  Get the `connectionName` of the instance in the format
    `project-id:zone-id:instance-id` by running the following command:

        gcloud beta sql instances describe INSTANCE_NAME

1.  Update `src/main/resources/application-mysql.properties`, replacing
    INSTANCE_CONNECTION_NAME with the `connectionName` from the previous step:

        database=mysql
        spring.datasource.driverClassName=com.mysql.jdbc.Driver
        spring.datasource.url=jdbc:mysql://google/petclinic?cloudSqlInstance=INSTANCE_CONNECTION_NAME&socketFactory=com.google.cloud.sql.mysql.SocketFactory
        spring.datasource.username=root
        spring.datasource.password=my-smart-password

1.  Update `pom.xml` to include [Cloud SQL MySQL Socket Factory][socket].
    The socket library allows you to connect to your Cloud SQL instance for
    local testing and deployment.

1.  Restart the Spring Boot application using the mysql [profile][profile]:

        ./mvnw -Drun.profiles=mysql spring-boot:run

    Access the application homepage http://localhost:8080 via your web browser
    and add some data.

1.   You can verify the data exists in Cloud SQL by running queries agains the
    `petclinic` database using the [Cloud Shell][shell].

[api]: https://console.cloud.google.com/flows/enableapi?apiid=sqladmin
[instructions]: /sql/docs/mysql/create-instance#create-2nd-gen
[socket]: https://mvnrepository.com/artifact/com.google.cloud.sql/mysql-socket-factory
[profile]: http://docs.spring.io/spring-boot/docs/current/maven-plugin/examples/run-profiles.html
[shell]: /sql/docs/mysql/quickstart#connect_to_your_instance_using_the_db_client_client_in_the_cloud_shell

### Deploying to App Engine flexible environment on GCP

Now that you've tested the application locally, you can deploy the application
to the App Engine flexible environment. Once deployed, it will be accessible at
https://YOUR_PROJECT_ID.appspot.com.

1.  App Engine flexible environment provides Maven plugins to make your build
    and deploy process extremely easy.
    Add [`appengine-maven-plugin`][appengine-maven] to your
    `pom.xml`'s `build` plugins section.

1.  Create an `app.yaml` under `src/main/appengine` with the following contents.
    For more on configuring `app.yaml`, refer to [this resource][yaml]:

        runtime: java
        env: flex

        resources:
          memory_gb: 2.3

        handlers:
          - url: /.*
            script: this field is required, but ignored

1.  App Engine flexible environment monitors the health of your application
    using the `/_ah/health` endpoint. (Note: A `200` or`404` status is
    interpreted as the application being healthy.) Because Spring Boot
    automatically provides a [health check endpoint][health], we can hook that
    up as our health check endpoint. Update the following fields in
    `src/main/resources/application.properties`:

         management.contextPath=/_ah
         spring.profiles.active=mysql

1.  Run the following command to deploy your app:

        ./mvnw -DskipTests=true appengine:deploy

1.  Visit `https://YOUR_PROJECT_ID.appspot.com` to access the Pet Clinic
    application, now running on GCP. View the application logs using the
    [Cloud Platform Console][logs].

[yaml]: /appengine/docs/flexible/java/configuring-your-app-with-app-yaml
[health]: https://docs.spring.io/spring-boot/docs/current/reference/html/production-ready-endpoints.html#production-ready-health
[logs]: https://console.cloud.google.com/logs/viewer
[appengine-maven]: http://mvnrepository.com/artifact/com.google.cloud.tools/appengine-maven-plugin

### Next steps

- [Build][build] your own Spring application.
- Deploy the application to [Google Container Engine][gke].
- Try out [other Java samples][samples] on GCP.

[build]: http://start.spring.io/
[gke]: /appengine/docs/flexible/java/run-flex-app-on-gke
[samples]: /java/samples
