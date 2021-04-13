---
title: Building CI/CD pipelines for a data lake's serverless data processing services
description: Learn how to set up continuous integration and continuous delivery for a data lake's data processing pipeline with Terraform, GitHub, and Cloud Build using the popular GitOps methodology.
author: prasadalle
tags: datalake, analytics, cicd, Cloud Build, BigQuery, Dataflow, Cloud Storage, GitHub, devops, GitOps, continuous integration, continuous deployment
date_published: 2021-01-08
---

Prasad Alle | Customer Engineer, Data and Analytics Specialist | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Many enterprise customers build data processing pipelines for a [data lake](https://en.wikipedia.org/wiki/Data_lake) on Google Cloud. They often have
[hybrid and multi-cloud architecture patterns](https://cloud.google.com/solutions/hybrid-and-multi-cloud-architecture-patterns) and use CI/CD tools, yet see 
challenges with version control, building, testing, and deploying pipelines seamlessly across their global development teams.

Data engineers, data scientists, and data analysts across global teams can adapt the methodologies from CI/CD practices to help to ensure high quality, 
maintainability, and adaptability of the data lake data processing pipelines. 

This document show you how to do the following:

* Set up continuous integration and continuous delivery (CI/CD) for a data lake’s data processing pipelines by implementing CI/CD methods with Terraform,
  GitHub, and Cloud Build using the popular GitOps methodology.
* Build serverless data processing and CI/CD pipelines.

This document covers building CI/CD pipelines for data lakes for serveless data services Cloud Storage, Dataflow, and BigQuery. A future document in this series
will cover building CI/CD pipelines for data lakes for Apache Spark applications on Dataproc.

You use the following Google Cloud services and open source tools in this document:

* [Cloud Storage](https://cloud.google.com/storage/) is a highly available, durable object store to store any amount of data. In this document, you use it to
  store raw, unprocessed sample data.

* [Dataflow](https://cloud.google.com/dataflow) is a serverless unified batch and streaming data processing service. This document uses a Google-provided
  open source Dataflow template to build a 
  [Cloud Storage text to BigQuery](https://cloud.google.com/dataflow/docs/guides/templates/provided-batch#gcstexttobigquery) data processing pipeline.

* [BigQuery](https://cloud.google.com/bigquery) is a serverless, highly scalable, and cost-effective multi-cloud data warehouse designed for business agility.
  This document uses BigQuery to store processed data for analytics use.

* [Cloud Build](https://cloud.google.com/cloud-build) is used to create a CI/CD pipeline for building, deploying, and testing a data-processing workflow, and
  the data processing itself. 

* [GitHub](https://github.com/) is a distributed version-control system for tracking changes in source code during software development. This document uses 
  GitHub to store and perform version control for data processing pipelines and Terraform infrastructure-as-code models.

* [Terraform](https://www.terraform.io/) is an open source tool that uses *infrastructure as code* to provision and manage
  [Google Cloud resources](https://cloud.google.com/docs/terraform). This document uses Terraform to create a data processing pipeline.

## Deployment architecture

In this solution, you build a serverless data processing pipeline as shown in the following diagram:

![Deployment architecture](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/architecture1.png)

The general outline of the process is as follows:

1.  Create a Cloud Storage bucket. 
1.  Load sample data and define schema and mapping files.
1.  Create a Dataflow pipeline.
1.  Create a dataset and table in BigQuery. 
1.  Load data into the BigQuery table.

In addition to a serverless data processing pipeline, you also build a CI/CD pipeline for data processing that enables version control, allowing you to build,
test, and deploy this code into various environments.

![DataLake-CICD-Part1](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/architecture2.png)

While implementing this architecture in your production environment, make sure to consider factors like security, monitoring, failure handling, and any 
operational issues.

## Prerequisites

* **Google Cloud account**: If you don’t already have one, you can [sign up for a new account](https://accounts.google.com/SignUp).

* **Google Cloud project**: You can create a new project or select an existing project in the [Cloud Console](https://console.cloud.google.com/project).

  If you don't plan to keep the resources that you create in this document, create a project instead of selecting an existing project. After you finish these
  steps, you can delete the project, removing all resources associated with the project.

* **GitHub account**: If you don’t already have one, you can [sign up for a new account](https://github.com/join)).

* **Cloud Shell**: In this document, you run commands in [Cloud Shell](https://cloud.google.com/shell/docs). Cloud Shell is a shell environment with the Cloud 
  SDK already installed, including the `gcloud` command-line tool, and with values already set for your current project.

## Costs

This document uses the following billable components of Google Cloud:

* [Cloud Storage](https://cloud.google.com/storage/pricing)
* [Dataflow](https://cloud.google.com/dataflow/pricing)
* [BigQuery](https://cloud.google.com/bigquery/pricing)
* [Cloud Build](https://cloud.google.com/cloud-build/pricing)

To generate a cost estimate based on your projected usage, use the [pricing calculator](https://cloud.google.com/products/calculator).

## Deployment steps

In this section, you go through the following steps:

1.  Set up your environment and grant required permissions.
1.  Set up your GitHub repository.
1.  Create Cloud Storage bucket to store your data lake raw data and mapping files.
1.  Connect Cloud Build to your GitHub repository.
1.  Create a build trigger to respond to changes in your GitHub repository.
1.  Make changes in a feature branch.
1.  Promote changes to the development environment.
1.  Promote changes to the production environment.

### Set up your environment and grant required permissions

1.  Set environment variables with values appropriate for your environment:

        SA_ID=datalake-deployer (SA=Service Account)

        PROJECT_ID=$(gcloud config list --format 'value(core.project)')

        PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='get(projectNumber)')

        SA_EMAIL=$SA_ID@$PROJECT_ID.iam.gserviceaccount.com

        BUCKET_NAME=$PROJECT_ID

        GITHUB_USERNAME=[YOUR_GITHUB_USERNAME]

1.  Enable the required APIs:

        gcloud services enable cloudbuild.googleapis.com compute.googleapis.com bigquery-json.googleapis.com storage.googleapis.com dataflow.googleapis.com --project $PROJECT_ID

1.  Create a data lake service account:

        gcloud iam service-accounts create $SA_ID \
          --display-name $SA_ID \
          --project $PROJECT_ID

1.  Add the appropriate IAM roles to the data lake service account:

        for role in bigquery.admin storage.admin dataflow.admin compute.admin dataflow.worker; do \
          gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:$SA_EMAIL" \
          --role="roles/$role"; \
          done

1.  Add the appropriate IAM roles to the default Cloud Build service account:

        for role in bigquery.admin storage.admin dataflow.admin compute.admin dataflow.worker; do \
          gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
          --role="roles/$role"; \
        done

1.  Add the Cloud Build service account as a service account user of the data lake service account within the project:

        gcloud iam service-accounts add-iam-policy-binding \
           $SA_EMAIL \
          --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
          --role=roles/iam.serviceAccountUser \
          --project $PROJECT_ID

1.  Get `PROJECT_ID` and `SA_EMAIL` for use in later steps:

        echo $PROJECT_ID

        echo $SA_EMAIL
    
### Set up your GitHub repository

You use a single GitHub repository to define your cloud infrastructure and orchestrate this infrastructure by having different branches corresponding to 
different environments:

*   The `dev` branch contains the latest changes that are applied to the development environment.
*   The `prod` branch contains the latest changes that are applied to the production environment.

With this infrastructure, you can always reference the repository to know what configuration is expected in each environment and to propose new changes by first
merging them into the `dev` environment. You can then promote the changes by merging the `dev` branch into the subsequent `prod` branch.

1.  In Cloud Shell, clone the [Google Cloud Community](https://github.com/GoogleCloudPlatform/community) repository:

        cd ~

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  [Create a new repository](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/create-a-repo) in your GitHub account.

1.  Add your project to your repository:

        cd ~/community/tutorials/cicd-datalake-part-1/

        echo "# cicd-datalake-part-1" >> README.md
        git init
        git add .
        git commit -m "commit CICD data lake project"
        git branch -M dev
        git branch -M prod

        git remote add origin https://github.com/$GITHUB_USERNAME/cicd-datalake-part-1.git

        git push -u origin dev
        git push -u origin prod

The code in this repository is structured as follows:

* The `environments/` folder contains subfolders that represent environments, such as `dev` and `prod` data processing pipelines, which provide logical 
  separation between workloads at the development and production stages. Although it's a good practice to have these environments as similar as possible,
  each subfolder has its own Terraform configuration to ensure that they can have unique settings if necessary.

* The `testdata/` folder contains the test data and mapping scripts to build data processing pipeline.

* The `cloudbuild.yaml` file is a build configuration file that contains instructions for Cloud Build, such as how to perform tasks based on a set of steps.
  This file specifies conditional execution depending on the branch that Cloud Build is fetching the code from.

  For `dev` and `prod` branches, the following steps are executed:

   * `terraform init`
   * `terraform plan`
   * `terraform apply`

  For `dev` and `prod` branches, the following steps are executed:

   * `terraform init` for all environments' subfolders
   * `terraform plan` for all environments' subfolders

The reason that `terraform init` and `terraform plan` run for all environments' subfolders is to make sure that the changes being proposed hold for every single 
environment. This way, before merging the pull request, you can review the plans to make sure that access is not being granted to an unauthorized entity.

### Set up your Cloud Storage buckets

Sample data used in this document is from [E for Excel](http://eforexcel.com/). You can
[download the complete dataset as a ZIP file](http://eforexcel.com/wp/wp-content/uploads/2017/07/1500000%20CC%20Records.zip). This is not real transaction data,
and it should not be used for any other purpose other than testing.

Create a Cloud Storage bucket to store raw unprocessed sample data files and mapping files required to build data processing pipelines.

1.  Set up Cloud Storage bucket, with a region appropriate for your setup:

        gsutil mb -c standard -l us-west1 gs://$BUCKET_NAME

1.  Upload the contents from `testdata` folder into the Cloud Storage bucket:

        cd ~/community/tutorials/cicd-datalake-part-1/testdata

1.  Copy the downloaded test data and schema files from the GitHub repository to your Cloud Storage bucket:

        gsutil cp *.* gs://$BUCKET_NAME

        gsutil ls gs://$BUCKET_NAME

### Connect Cloud Build to your GitHub repository

This section shows how to install the [Cloud Build GitHub app](https://github.com/marketplace/google-cloud-build). This installation allows you to connect a 
GitHub repository to a Google Cloud project so that Cloud Build can automatically apply Terraform manifests each time a new branch is created or code is pushed
to GitHub.

The following steps provide instructions for installing the app only for your new repository, but you can choose to install the app for more repositories.

1.  Go to the [GitHub Marketplace page](https://github.com/marketplace/google-cloud-build) for the Cloud Build app.

1.  If this is your first time configuring an app in GitHub, click **Setup with Google Cloud Build**. Otherwise, click **Edit your plan**, select your billing 
    information and, on the **Edit your plan** page, click **Grant this app access**.

1.  On the **Install Google Cloud Build** page, select **Only select repositories** and enter `[YOUR_GITHUB_USERNAME]/cicd-datalake-part-1` to connect to your 
    repository.

1.  Click **Install**.

1.  Sign in to Google Cloud.

    The **Authorization** page is displayed. You are asked to authorize the Cloud Build GitHub app to connect to Google Cloud.
    
1.  Click **Authorize Google Cloud Build by GoogleCloudBuild**.

    You are redirected to the Cloud Console.

1.  Select the Google Cloud project you are working on. If you agree to the terms and conditions, select the checkbox, and then click **Next**.

1.  In **Repository selection**, select `[YOUR_GITHUB_USERNAME]/cicd-datalake-part-1` to connect to your Google Cloud project, and then click
    **Connect repository**.

1.  Click **Skip for now** on the next screen.

1.  Click **Done**.

The Cloud Build GitHub app is now configured and your GitHub repository linked to your Google Cloud project. From now on, any changes to the GitHub repository 
will trigger Cloud Build executions, which report the results back to GitHub by using [GitHub checks](https://developer.github.com/v3/checks/).

### Configure a build trigger to respond to changes in your GitHub repository

Following the previous steps, you should have a configuration to establish connectivity between Cloud Build and your GitHub repositories. Now create a trigger in
the Cloud build to respond to changes in the GitHub repository to test and run your infrastructure for data processing pipelines.

1.  Go to the Cloud Build [**Triggers**](https://console.cloud.google.com/cloud-build/triggers) page in the Cloud Console.

1.  Click **Create trigger**.

1.  Provide the **Name** and **Description** of your trigger.

1.  In the **Event** section, select **Push to a branch**.

1.  In the **Source section**, do the following:
      * **Repository**: Select your repository.
      * **Branch**: Select **.*(any branch)**.

1.  In the **Build configuration** section, select **Cloud Build configuration file**.

1.  In the **Cloud Build configuration file location** field, specify the file location
    as `cloudbuild.yaml` after the `/`.

1.  In the **Advanced** section, click **Add variable** and add your environment variables such as `ProjectID`, `ServiceAccountEmail`, `Region`,    
    and `SourceDatabucket`. Use the following naming standard, which refers to variables created in previous sections:

        _PROJECT_ID=[YOUR_PROJECT_ID]
        _REGION=[YOUR_REGION]
        _SERVICE_ACCOUNT_EMAIL=[YOUR_SERVICE_ACCOUNT_EMAIL_ADDRESS]
        _SOURCE_GCS_BUCKET=[YOUR_SOURCE_FILE_CLOUD_STORAGE_BUCKET]

      ![Image4](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image4.png)

1.  Click **Create**

### Make changes in a new feature branch

By now, you have most of your environment configured. So now it's time to make some code changes in your development environment and test the build trigger.

1.  In GitHub, go to the main page of your repository (`cicd-datalake-part-1`).

1.  Make sure that you're in the `dev` branch.

    ![Image5](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image5.png)

1.  Open the `environments/dev/main.tf` file for editing by clicking the pencil icon.

1.  Add comments (such as `“#cicd-datalake-part-1”`) to the `main.tf` file.

1.  Add a commit message at the bottom of the page, such as `cicd-datalake-part-1`, and select **Create a new branch for this commit**.
 
1.  Click the **Propose change**.

1.  On the following page, click **Create pull request** to create a new  pull request with your change.

    When your pull request is created, a Cloud Build job is automatically initiated.

1.  Click **Show all checks** and wait for the check to become green.

    ![Image6](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image6.png)

1.  In the Cloud Console, go to the **Cloud Build History** page to see build details.

1.  Make sure that you don’t have any build exceptions and that you are ready to promote changes to `dev` branch.

### Promote changes to the development environment

You have a pull request waiting to be merged. It's time to apply the state you want to your `dev` environment.

1.  In GitHub, go to the main page of your repository (`cicd-datalake-part-1`).

1.  Under your repository name, click **Pull requests**.

1.  Click the pull request that you just created.

1.  Click **Merge pull request**, and then click **Confirm merge**.

    ![Image7](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image7.png)

1.  Check the **Cloud Build History** page in the Cloud Console to confirm that a new build has been triggered. Make sure that it's successful.

    ![Image18](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image18.png)

1.  After the Cloud Build job has successfully run, it creates a data processing pipeline in the `dev` environment with the following actions:

      1.  Create a Dataflow job.

      1.  Create a dataset and table in BigQuery. (This tutorial uses `dev_datalake_demo` and `prod_datalake_demo` as dataset names and `sample_userdata` as a 
      table name. You can change these in the `main.tf` file.)

      1.  Load data from the Cloud Storage bucket to a BigQuery table.

1.  Go to the [Dataflow page](http://console.cloud.google.com/dataflow) in the Cloud Console to check the job status.

    ![Image8](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image8.png)

1.  After successful completion of the Dataflow job, a BigQuery dataset and table are created, and the data from the CSV file in the Cloud Storage bucket
    is loaded into the BigQuery table.

    ![Image9](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image9.png)

### Promote changes to the production environment

Now that you have your development environment fully tested, you can promote your data processing pipeline code to production.

1.  In GitHub, go to the main page of your repository (`cicd-datalake-part-1`).

1.  Click **New pull request**.

1.  For **base**, select **prod** and for **compare**, select **dev**.
    
    ![Image11](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image11.png)

1.  Click **Create pull request**.

1.  Enter a title, such as `Promoting data lake changes`, and then click **Create pull request**.

1.  Review the proposed changes, including the Terraform plan details from Cloud Build, and then click **Merge pull request**.

1.  Click **Confirm merge**.
	
    ![Image12](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image12.png)

    ![Image13](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image13.png)
 
1.  In the Cloud Console, open the **Build History** page to see your changes being applied to the production environment:

    ![Image14](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image14.png)

1.  Open Dataflow page to see the job status:

    ![Image15](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image15.png)
   
1.  Wait for the Dataflow to finish, and then check BigQuery to make sure that the job created the production dataset and tables.
    
    ![Image16](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image16.png)

    ![Image17](https://storage.googleapis.com/gcp-community/tutorials/cicd-datalake-part-1/image17.png)


## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this document, you can delete the project or delete the individual resources
(Cloud Storage bucket, BigQuery table and dataset, Cloud Build trigger) that you created while working through this document.

### What's next

- Learn more about [Google Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
