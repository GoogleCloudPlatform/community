---
title: Run a Spring app with Cloud SQL and Secret Manager on App Engine flexible
description: Learn how to deploy the Spring Inventory Management demonstration application to App Engine flexible environment with Cloud SQL, Secret Manager, and Cloud Build.
author: kioie
tags: App Engine, Secret Manager, Cloud SQL, Spring Boot, Java, Cloud Build
date_published: 2020-07-06
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial demonstrates the deployment of a [Spring inventory management](https://github.com/kioie/InventoryManagement) app to production on App Engine 
flexible environment through a CI/CD (continuous integration and continuous delivery) pipeline.

This tutorial uses Spring Cloud, Cloud SQL for MySQL, App Engine, Secret Manager, Cloud Build, and GitHub:

- [Spring Cloud](https://spring.io/projects/spring-cloud) aims to shorten code length and provide you with the easiest way to develop a web application. With
  annotation configuration and default code, Spring Cloud shortens the time involved in developing an application. It helps to create a standalone application 
  with less configuration.
- [Inventory Management](https://github.com/kioie/InventoryManagement) is a demonstration application that you'll use with this tutorial. The
  Inventory Management application is built using Spring and creates REST endpoints that serve inventory items for a demonstration supplier.
- [Cloud SQL](https://cloud.google.com/sql) is a fully managed relational database service for MySQL, PostgreSQL, and SQL Server that offers easy integration 
  with existing apps and Google Cloud services.
- [App Engine](https://cloud.google.com/appengine) is a platform-as-a-service for developing and hosting web applications at scale on Google-managed 
  infrastructure. It allows you to choose from several popular languages, libraries, and frameworks to develop and deploy your apps, including Java with Spring.
  Applications are sandboxed and deployed across Google infrastructure, taking away the need for environment configuration and management, across the application 
  lifecycle.
- [Secret Manager](https://cloud.google.com/secret-manager) is a secure and convenient storage system for API keys, passwords, certificates, and other sensitive
  data. Secret Manager provides a central place and single source of truth to manage, access, and audit secrets across Google Cloud, or anywhere else for that 
  matter.
- [Cloud Build](https://cloud.google.com/cloud-build) is a service that executes your builds on Google Cloud infrastructure. Cloud Build can import source code 
  from Cloud Storage, Cloud Source Repositories, GitHub, or Bitbucket and then execute a build to your specifications to produce artifacts such as Docker 
  containers or Java archives.

## Before you begin

1. Create a project in the [Cloud Console](https://console.cloud.google.com/cloud-resource-manager).  
2. Enable billing for your project.  
3. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/downloads-interactive).  
4. Install [Maven](https://maven.apache.org/install.html).
5. Create or log in to a [GitHub account](https://github.com/).

## Set up the Cloud SDK

1.  Initialize the Cloud SDK:

        gcloud init  

1.  Create an App Engine application:

        gcloud app create  

1.  Authorize the Cloud SDK to use Google Cloud APIs in your local environment:

        gcloud auth application-default login

## Set up Cloud SQL

1.  [Enable the Cloud SQL API.](https://console.cloud.google.com/flows/enableapi?apiid=sqladmin)

1.  Create a Cloud SQL (MySQL) instance:

        gcloud sql instances create test-instance-inventory-management --tier=db-n1-standard-1 --region=us-central1
    
1.  Set the password for the `root@%` MySQL user following
    [these instructions](https://cloud.google.com/sql/docs/mysql/create-instance#create-2nd-gen):

        gcloud sql users set-password root --host=% --instance test-instance-inventory-management --password [PASSWORD]
    
    Replace `[PASSWORD]`with your own password.

1.  Create the `inventory` database:

        gcloud sql databases create inventory --instance=test-instance-inventory-management

1.  Get the connection name of the instance in the format `project-id:zone-id:instance-id`:

        gcloud sql instances describe test-instance-inventory-management | grep connectionName

## Set up and test the application
     
1.  Clone the project locally:

        git clone https://github.com/kioie/InventoryManagement.git
        
1.  Change directory to the app directory:

        cd InventoryManagement/

1.  Update your `application-mysql.properties` file by replacing `instance-connection-name`, `database-name`, `username`, and `password`.  
  
    The values that you see when you first open this file have been designed for a Secret Manager connection, which is discussed in a later section.

1.  Update `src/main/resources/application-mysql.properties`:

        #CLOUD-SQL-CONFIGURATIONS  
        spring.cloud.appId=sample-gcp-project  
        spring.cloud.gcp.sql.instance-connection-name=sample-gcp-project-277704:us-central1:test-instance-inventory-management  
        spring.cloud.gcp.sql.database-name=inventory  
        ##SQL DB USERNAME/PASSWORD  
        spring.datasource.username=root  
        spring.datasource.password=xxxxx

   Replace `xxxxx` with your preconfigured database instance password.  
  
1.  Start the Spring Boot application:

        mvn spring-boot:run

1.  Do a simple test of your application:

        curl http://localhost:8080/inventory/
    
## Set up Secret Manager

1.  [Enable the Secret Manager API.](https://console.cloud.google.com/flows/enableapi?apiid=secretmanager.googleapis.com)

1.  Grant the application access:

    1.  Go to the [**IAM & Admin** page](https://console.cloud.google.com/iam-admin/iam).
    1.  Click the **Project selector** drop-down list at the top of the page.  
    1.  In the **Select from** dialog that appears, select the organization for which you want to enable Secret Manager.  
    1.  On the **IAM** page, next to the **App Engine service account**, click **Edit**.  
    1.  In the **Edit permissions** panel that appears, add the necessary roles.  
    1.  Click **Add another role**.
    1.  Select **Secret Manager Admin**.  
    1.  Click **Save**.
  
1.  Create new secrets for your data source configuration file, using your own credentials for `spring_cloud_gcp_sql_instance_connection_name` and 
    `spring_datasource_password`:
  
        echo -n “sample-gcp-project-277704:us-central1:test-instance-inventory-management” | gcloud secrets create spring_cloud_gcp_sql_instance_connection_name — replication-policy=”automatic” — data-file=-  
   
        echo -n “inventory” | gcloud secrets create spring_cloud_gcp_sql_database_name — replication-policy=”automatic” — data-file=-  
   
        echo -n “root” | gcloud secrets create spring_datasource_username — replication-policy=”automatic” — data-file=-  
   
        echo -n “test123” | gcloud secrets create spring_datasource_password — replication-policy=”automatic” — data-file=-

1.  Confirm that your secrets have been created:
      
        gcloud secrets list
        
    This command should return a list of secrets.

1.  Replace the values in the `application-mysql.properties` file with the secrets URL. For this step, you need the fully qualified name of the secret as defined
    in Google Cloud.

        gcloud secrets describe spring_cloud_gcp_sql_instance_connection_name | grep name
        gcloud secrets describe spring_cloud_gcp_sql_database_name | grep name
        gcloud secrets describe spring_datasource_username | grep name
        gcloud secrets describe spring_datasource_password | grep name

    You will now use these names to create a Secret Manager URL. The URL will use the format `${sm://FULLY-QUALIFIED-NAME}`, where `FULLY-QUALIFIED-NAME` is as
    retrieved above.

1.  Update `src/main/resources/application-mysql.properties`:

        #CLOUD-SQL-CONFIGURATIONS  
        spring.cloud.appId=sample-gcp-project  
        spring.cloud.gcp.sql.instance-connection-name=${sm://projects/.../secrets/spring_cloud_gcp_sql_instance_connection_name}  
        spring.cloud.gcp.sql.database-name=${sm://projects/.../secrets/spring_cloud_gcp_sql_database_name}  
        ##SQL DB USERNAME/PASSWORD  
        spring.datasource.username=${sm://projects/.../secrets/spring_datasource_username}  
        spring.datasource.password=${sm://projects/.../secrets/spring_datasource_password}

1.  Restart the Spring Boot application:

        mvn spring-boot:run
    
1.  Test your application again:

        curl http://localhost:8080/inventory/1

## Set up your GitHub repository with source files

1.  Enable the [Cloud Build API](https://console.cloud.google.com/flows/enableapi?apiid=cloudbuild.googleapis.com) in the target Cloud project.

1.  Fork the demonstration repository, because you will be pushing your changes to this repository:

    1.  Navigate to https://github.com/kioie/InventoryManagement.
    
    1.  In the top-right corner of the page, click **Fork**.
    
1.  [Install the Google Cloud Build app](https://cloud.google.com/cloud-build/docs/automating-builds/run-builds-on-github#installing_the_google_cloud_build_app) on GitHub.

    Make sure that you select the `kioie/InventoryManagement` repository fork as the repository to connect to.

1.  In the Cloud Console, open the Cloud Build [Build triggers](https://console.cloud.google.com/cloud-build/triggers) page.

1.  Delete all triggers created that may be related to this project before moving to the next step. This ensures that no other builds are running other than the
    single build configured for this tutorial.

1.  Select your Cloud project and click **Open**.

1.  Click **Create Trigger**.

1.  Fill out the options:

    -   **Name**: Enter a name.
    -   **Description** (optional): Enter a brief description of how the trigger will work.
    -   **Event**: Select **Push to a branch**.
    -   **Source**: Select the `kioie/InventoryManagement` repository. (If the repository does not appear, click the **Connect New Repository** button, 
        connect your repository on GitHub, and return to step 5.)
    -   **Branch**: Enter `^master$`.
    -   **Build Configuration** Select **Cloud Build configuration file (YAML or JSON)**. For the Cloud Build configuration file location, enter 
        `cloudbuild.yaml`. (Do not add an extra `/`.)

1.  Click **Create**.

Under your active triggers, you should see your newly created trigger.

## Files required for Cloud Build

To configure your build for Cloud Build app, your repository must contain either a
[Dockerfile](https://docs.docker.com/get-started/part2/#define-a-container-with-dockerfile) or a
[`cloudbuild.yaml` file](https://cloud.google.com/cloud-build/docs/build-config).

A Dockerfile file is generally used for building Docker containers. If you're using Cloud Build for Docker builds, you need a Dockerfile. This tutorial is for an
App Engine build, but the sample repository contains a Dockerfile; this is because Cloud Build performs a bonus step that creates a container artifact, 
although this is not necessary for this tutorial.

The `cloudbuild.yaml` file is the configuration file for Cloud Build. You use a `cloudbuild.yaml` file when using Cloud Build for non-Docker builds or when you 
want to fine-tune your Docker builds. If your repository contains a `Dockerfile` file and a `cloudbuild.yaml` file, Cloud Build uses the `cloudbuild.yaml` file 
to configure the builds. 

## Set up App Engine

Using App Engine, your application will be deployed and accessed at `https://YOUR_PROJECT_ID.uc.r.appspot.com`.

1.  Open the `pom.xml` file and change the `projectId` and `version` values to the appropriate values for your project ID and version.  

    `<deploy.projectId>sample-gcp-project-276208</deploy.projectId>`
    
1.  [Enable the App Engine Admin API.](https://console.developers.google.com/apis/library/appengine.googleapis.com)

1.  [Enable the App Engine Flexible API.](https://console.developers.google.com/apis/library/appengineflex.googleapis.com)

1.  Give the necessary permissions to the Cloud Build service account:

    1.  Go to the [IAM & Admin page](https://console.cloud.google.com/iam-admin/iam).
    1.  Click the **Project selector** drop-down list at the top of the page and select the current project organization.
    1.  On the **IAM** page, next to the Cloud Build service account, (not to be confused with the Cloud Build service agent), click **Edit** (the pencil 
        button).
    1.  On the **Edit permissions** panel that appears, click **Add another role** and add these three roles: App Engine Admin, Cloud SQL Admin,
        Secret Manager Admin
    1.  Click **Save**.
    
## Push to GitHub and trigger a build

Push your updated code to GitHub to trigger a build by Cloud Build:

1.  Add your remote GitHub fork repository as your upstream repository:

        git remote add upstream https://github.com/<YOUR_ACCOUNT_NAME>/InventoryManagement 
        git remote -vv
  
1.  Commit your changes:

        git add .  
        git commit

1.  Push upstream:

        git push upstream master

    This should automatically trigger your build on Google Cloud.
    
1.  Check the status of your build:

        gcloud builds list

1.  Fetch the URL of the app:

        gcloud app browse
    
6. Test your endpoints:

        curl https://sample-gcp-project-277704.uc.r.appspot.com/inventory
        curl https://sample-gcp-project-277704.uc.r.appspot.com/inventory/1    
        curl https://sample-gcp-project-277704.uc.r.appspot.com/inventory/2

You now have an app running on App Engine, deployed using Cloud Build, hosted on GitHub, and using Secret Manager to maintain your secrets.
