---
title: Run a Spring inventory manager app with Cloud SQL and Secret Manager on App Engine flexible environment
description: Learn how to deploy the Spring Inventory Management demonstration application to App Engine flexible environment with Cloud SQL, Secret Manager, and Cloud Build.
author: kioie
tags: App Engine, Secret Manager, Cloud SQL, Spring Boot, Java, Cloud Build
date_published: 2020-07-06
---

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

1.  Get the connection name (`connectionName`) of the instance in the format `project-id:zone-id:instance-id`:

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

1.  Do a simple test of your application to confirm that everything went successfully:

        curl http://localhost:8080/inventory/
    
## Set up Secret Manager

1.  [Enable the Secret Manager API.](https://console.cloud.google.com/flows/enableapi?apiid=secretmanager.googleapis.com)

1.  Grant the application access:

    1.  Go to [IAM & Admin page](https://console.cloud.google.com/iam-admin/iam).
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

1.  Replace the values in the `application-mysql.properties` file with the secrets URL. For this step, you need the fully-qualified name of the secret as defined
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
    
1.  Test your application again to confirm that everything went successfully:

        curl http://localhost:8080/inventory/1

## Set up GitHub repository with source files

1.  Create a [GitHub account](https://github.com/) if you don’t have one already.

2.  Enable the [Cloud Build API](https://console.cloud.google.com/flows/enableapi?apiid=cloudbuild.googleapis.com) in the target Cloud project.

3.  Fork our demo repository. This step is important as you will be pushing your changes to this repo  
    a. Navigate to [https://github.com/kioie/InventoryManagement](https://github.com/kioie/InventoryManagement)  
    
    b. On the top-right corner of the page, click **`Fork`**.
    
![](https://storage.cloud.google.com/gcp-community/tutorials/run-spring-inventory-manager-with-cloud-sql-secret-manager-on-app-engine-flexible-environment-using-cloud-build/Screenshot1.png)

4. Install the Google Cloud Build App on Github. You can follow this instructions [**here**](https://cloud.google.com/cloud-build/docs/automating-builds/run-builds-on-github#installing_the_google_cloud_build_app).

    **_Make sure you select the_** **_`kioie/InventoryManagement`_** **_repository fork as the repository you are connecting to, otherwise this build will not work._**

5. In the Google Cloud Console, open the Cloud Build [Build triggers](https://console.cloud.google.com/cloud-build/triggers?_ga=2.173763299.1749283848.1589680102-1322801348.1576371208&_gac=1.259777016.1587192241.CjwKCAjwp-X0BRAFEiwAheRui4GkVAiJEcD-d_dhMaMnTeAmRAMMUBXLV45atuLUiiLinEjPGLLbuhoCzD8QAvD_BwE) page.

    **_Make sure to delete all triggers created, that may be related to this project before moving to the next step. We are doing this to make sure that no other builds are running other than the single build we have configured._**

6. Select your Google Cloud project and click **`Open`**.

7. Click **`Create Trigger`**.

8. Fill out the options

    -   _Required_. In the **`Name`** field, enter a name
    -   _Optional_. In the **`Description`** field, enter a brief description of how the trigger will work
    -   Under **`Event`**, select **`Push to a branch`**
    -   In the **`Source`** drop-down list, select `kioie/InventoryManagement` repository  
    
      **_Note: If this repository does not appear, click the_** **_`Connect New Repository`_** **_button and connect your repo on GitHub, then return to step5._**
      
    -   Under **`Branch`**, enter `^master$`
    -   Under **`Build Configuration`** select **`Cloud Build configuration file (YAML or JSON)`**  
    For the `Cloud Build configuration file location` enter `cloudbuild.yaml`  
    **_Note: Do not add an extra_** **_`/`_**
    -   Click **`Create`**

Under your active triggers, you should now be able to see your newly created trigger.

## Some brief information

As a requirement for the Google Cloud Build app, your repository must contain either a `[Dockerfile](https://docs.docker.com/get-started/part2/#define-a-container-with-dockerfile)` or a `[cloudbuild.yaml](https://cloud.google.com/cloud-build/docs/build-config)` file to be able successfully configure your build.

`Dockerfile` is generally used for building Docker containers. Incase you are using Cloud Build for Docker Builds, you will require a `Dockerfile`. This tutorial is for an App Engine build, but you will notice that the sample repo contains a `Dockerfile`. This is because the cloud build contains a bonus step that completes by creating a container artifact, although this is not necessary for this tutorial.

`cloudbuild.yaml` is the config file for Cloud Build. You use a `cloudbuild.yaml` in the following scenarios:

   -   When using Cloud Build app for non-Docker builds.
   -   If you wish to fine-tune your Docker builds, you can provide a `cloudbuild.yaml` in addition to the `Dockerfile`. If your repository contains a `Dockerfile` and a `cloudbuild.yaml`, the Google Cloud Build app will use the `cloudbuild.yaml` to configure the builds.

## Set up App Engine

You will require app engine for our deployment. In the end, our application will be deployed and accessed on [https://YOUR_PROJECT_ID.appspot.com](https://YOUR_PROJECT_ID.appspot.com)

1.  The `pom.xml` file already contains configuration for `projectId` and `version`. Change this to reflect the current project ID.  

    `<deploy.projectId>sample-gcp-project-276208</deploy.projectId>`
    
2.  Enable [App Engine Admin API](https://console.developers.google.com/apis/library/appengine.googleapis.com)

3.  Enable [App Engine Flexible API](https://console.developers.google.com/apis/library/appengineflex.googleapis.com)

4.  Give more permission to the cloud build service account

    **Grant cloudbuild service account, admin access to Secret Manager, App Engine and Cloud Sql**.

    -   Go to [IAM & Admin page](https://console.cloud.google.com/iam-admin/iam?_ga=2.101936833.1749283848.1589680102-1322801348.1576371208&_gac=1.224978664.1587192241.CjwKCAjwp-X0BRAFEiwAheRui4GkVAiJEcD-d_dhMaMnTeAmRAMMUBXLV45atuLUiiLinEjPGLLbuhoCzD8QAvD_BwE)
    
    -   Click the **`Project selector`** drop-down list at the top of the page and select the current project organization.
    
    -   On the **`IAM`** page, next to the `cloud build service account`, (not to be confused with the `cloud build service agent` )click **`Edit`** (or the pencil button).
    
    -   On the **`Edit permissions panel`** that appears, add the necessary roles.
    
    -   Click **`Add another role`** and add these three roles:  
        — App Engine Admin  
        — Cloud SQL Admin  
        — Secret Manager Admin
        
    -   Click **`Save`**.

      The final permission list should look something like this
      
      ![](https://storage.cloud.google.com/gcp-community/tutorials/run-spring-inventory-manager-with-cloud-sql-secret-manager-on-app-engine-flexible-environment-using-cloud-build/Screenshot2.png)
      
      The final step that triggers a cloud build will require pushing your updated code-base to GitHub.
    
## Push to GitHub and trigger a build

1.  Add your remote GitHub fork repo as your upstream repo

    ````
    git remote add upstream [https://github.com/<YOUR_ACCOUNT_NAME>/InventoryManagement](https://github.com/YOUR_ACCOUNT_NAME/InventoryManagement)  
    git remote -vv
    ````
  
2. Commit your changes

    ````
    git add .  
    git commit
    ````

3. Push upstream

    ````
    git push upstream master
    ````

4. This should automatically trigger your build on GCP cloud build. You can check the status of your build using the below command

    ````
    gcloud builds list
    ````

5. You can fetch the url of the app with the command

    ````
    gcloud app browse
    ````

6. Now test out your endpoints

    ````
    curl [https://sample-gcp-project-277704.uc.r.appspot.com/inventory](https://sample-gcp-project-277704.uc.r.appspot.com/inventory)  
    
    curl [https://sample-gcp-project-277704.uc.r.appspot.com/inventory/1](https://sample-gcp-project-277704.uc.r.appspot.com/inventory/1)  
    
    curl [https://sample-gcp-project-277704.uc.r.appspot.com/inventory/2](https://sample-gcp-project-277704.uc.r.appspot.com/inventory/2)
    ````

You now have an app running on GCP App Engine, deployed using Cloud Build, and hosted on GitHub, and using Secret Manager to maintain your secrets.
