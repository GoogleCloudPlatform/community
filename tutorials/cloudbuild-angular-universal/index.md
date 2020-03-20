---
title: Perform Angular server-side (pre-)rendering with Cloud Build
description: Learn how to use Cloud Build to pre-generate your HTML for Angular.
author: johnlabarge
tags: Cloud Build, Angular Universal
date_published: 2018-11-08
---

# Perform Angular server-side (pre-)rendering with Cloud Build

This tutorial will show you how to pre-generate [server-side rendered Angular pages](https://angular.io/guide/universal)
using Cloud Build. Server-side rendering helps facilitate web crawlers (SEO), improve performance on mobile and low-powered
devices, and show the first page quickly.

![push new angular code to source repository](https://storage.googleapis.com/gcp-community/tutorials/cloudbuild-angular-universal/angular-cloudbuild.png)

## Prerequisites

1.  A Google Cloud Platform (GCP) account  [get a trial account here](https://console.cloud.google.com/freetrial?authuser=2&_ga=2.213928212.-2042919442.1528299768&_gac=1.89261801.1536929612.CjwKCAjwuO3cBRAyEiwAzOxKslw2lWJAN82nAhsu1azihQgX_7aQjek2MPEjanoAwKL5g70Rp0b9zRoCgFwQAvD_BwE)
1.  The necessary permissions; either:
    1.  **Project editor** access to an existing project
    1.  **Create a new project** permissions in an existing organization
    
## (OPTIONAL) Create a project with a billing account attached

This task helps you setup a new GCP project in which to run an Angular application.
**(You can also use an existing project and skip to the next step.)**

```sh
PROJECT=[NEW PROJECT NAME]
ORG=[YOUR ORGANIZATION NAME]
FOLDER=[YOUR FOLDER NAME]
BILLING_ACCOUNT=[YOUR_BILLING_ACCOUNT_NAME]
ZONE=[COMPUTE ZONE YOU WANT TO USE]
ACCOUNT=[GOOGLE ACCOUNT YOU WANT TO USE] or $(gcloud config get-value account)
ORG_NUMBER=$(gcloud organizations list --format="value(name)" --filter="(displayName='$ORG')")
FOLDER_NUMBER=$(gcloud alpha resource-manager folders list --format="value(name)" --organization=$ORG_NUMBER --filter="displayName=$FOLDER")
PROJECT_CREATE_OPTIONS="--organization=${ORG_NUMBER}"
if [ ! -z "$FOLDER" ]; then
PROJECT_CREATE_OPTIONS="--folder=${FOLDER_NUMBER}"
fi
gcloud projects create ${PROJECT} ${PROJECT_CREATE_OPTIONS}
gcloud beta billing projects link $PROJECT --billing-account=$(gcloud alpha billing accounts list --format='value(name)' --filter="(displayName='$BILLING_ACCOUNT')")
gcloud config configurations create --activate $PROJECT
gcloud config set project $PROJECT
gcloud config set compute/zone $ZONE
gcloud config set account $ACCOUNT
```

### Set the project variable (Skip this step if you created a new project above.)

To specify the project that you will use, replace `[CONFIGURATION NAME]` with the name of the project configuration:

```sh
gcloud config configurations activate [CONFIGURATION NAME]
PROJECT=$(gcloud config get-value project)
```

For more information on configurations see [configurations](https://cloud.google.com/sdk/gcloud/reference/config/configurations/).

### Enable the services required for the tutorial

```sh
gcloud services enable compute.googleapis.com
gcloud services enable sourcerepo.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Download the test Angular application, Tour of Heroes

1.  Download and unzip the test application:

        curl -L https://angular.io/generated/zips/universal/universal.zip > universal.zip
        unzip universal.zip -d angular-app
        cd angular-app

1.  Create a local Git repository for the sample code:

        curl -L https://github.com/angular/angular/blob/master/.gitignore > .gitignore
        git init
        git add .
        git commit -m "first"

### Create a Cloud Source repository for your copy of the test Angular application

You will create a repository called `tour-of-heroes-universal`

    gcloud source repos create tour-of-heroes-universal

### Make prerender changes to the Angular application

1.  Download the webpack prerender config file:

        curl -LO https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloudbuild-angular-universal/webpack.prerender.config.js

2.  Add the prerender webpack configuration file to Git:

        git add webpack.prerender.config.js

3.  Download the Typescript config file for prerendering:

        curl -LO https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloudbuild-angular-universal/prerender.tsconfig.json

4.  Add the  Typescript config file for prerendering:

        git add prerender.tsconfig.json

5.  Download the prerender Typescript file:

        curl -LO https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloudbuild-angular-universal/prerender.ts

6.  Add the prerender Typescript file to Git:

        git add prerender.ts

7.  Modify the `package.json` file to add the prerender steps.

    **Note** that jq is a tool for editing JSON and is installed in Cloud Shell by default. If you are going through this
    tutorial on your workstation, see [jq installation](https://stedolan.github.io/jq/download/) for instructions on 
    installing jq on your workstation.

        SCRIPT_ADDITIONS=$(echo '  {
        "build:prerender": "npm run build:client-and-server-bundles && npm run compile:prerender && npm run generate:prerender",
        "generate:prerender": "npm run webpack:prerender && node dist/prerender.js",
        "compile:prerender": "tsc -p prerender.tsconfig.json",
        "webpack:prerender": "webpack --config webpack.prerender.config.js"
        }')
        cat package.json | jq --argjson additions "$SCRIPT_ADDITIONS" '.scripts = .scripts+$additions' >tmpfile
        cp tmpfile package.json
        rm tmpfile

8.  Add the `package.json` changes to Git:

        git add package.json

9.  Commit your changes to the Git repository:

        git commit -m "pregenerate changes"

### Configure a Cloud Storage bucket and load balancer to host your Angular application on Cloud CDN

1.  Create the content Cloud Storage bucket:

        gsutil mb gs://$PROJECT-angular-app

1.  Create the backend bucket:

        gcloud compute backend-buckets create $PROJECT-angular-app-backend \
        --gcs-bucket-name=$PROJECT-angular-app \
        --enable-cdn

1.  Create a multi-regional IP address:

        gcloud compute addresses create angular-app-ip --global
        ANGULAR_APP_IP=$(gcloud compute addresses list  --filter="name=angular-app-ip" --format="value(address)")

1.  Create the URL map:

        gcloud compute url-maps create web-map --default-backend-bucket $PROJECT-angular-app-backend

1.  Create the HTTP proxy:

        gcloud compute target-http-proxies create http-lb-proxy \
        --url-map web-map

1.  Create the forwarding rule:

        gcloud compute forwarding-rules create http-content-rule \
        --address angular-app-ip \
        --global \
        --target-http-proxy http-lb-proxy \
        --ports 80

## Create the Cloud Build file and add it to the Git repsoitory

1.  Give the Cloud Build account Cloud Storage admin access:

        CLOUD_BUILD_ACCOUNT=$(gcloud projects get-iam-policy $PROJECT --filter="(bindings.role:roles/cloudbuild)"  --flatten="bindings[].members" --format="value(bindings.members[])")
        gcloud projects add-iam-policy-binding $PROJECT   --member $CLOUD_BUILD_ACCOUNT  --role roles/storage.admin

2.  Create the `cloudbuild.yaml` file:

         cat <<CLOUDBUILD_FILE>cloudbuild.yaml
         steps:
         - id: install_packages
           name: 'gcr.io/cloud-builders/npm'
           args:
           - 'install'
         - id: prerender_browser_files
           name: 'gcr.io/cloud-builders/npm'
           args:
           - 'run'
           - 'build:prerender'
           waitFor:
           - install_packages
         - id: copy_prerendered_files
           name: 'gcr.io/cloud-builders/gsutil'
           args: ['cp','-r','dist/browser/*', '\${_ANGULAR_APP_BUCKET_PATH}']
           waitFor:
           - prerender_browser_files
         - id: set_website_configuration
           name: 'gcr.io/cloud-builders/gsutil'
           args: ['web', 'set', '-m', 'index.html','\${_ANGULAR_APP_BUCKET_PATH}']
           waitFor:
           - copy_prerendered_files
         - id: set_permissions_for_website_files
           name: 'gcr.io/cloud-builders/gsutil'
           args: ['acl','ch','-u','AllUsers:R','-r', '\${_ANGULAR_APP_BUCKET_PATH}']
           waitFor:
           - copy_prerendered_files
         CLOUDBUILD_FILE

3.  Add and commit `cloudbuild.yaml` to the Git repository:

        git add cloudbuild.yaml && git commit -m "add cloudbuild.yaml"

### Create a build trigger that will build, test and deploy your application to the Cloud CDN

You can create a trigger on the [build triggers page](https://console.cloud.google.com/cloud-build/triggers) of the GCP Console by following these steps:

1.  Click **Create Trigger**.
1.  In the **Name** field, enter `angular-universal-tour`.
1.  Under **Event**, select **Push to a tag**.
1.  Under **Source**, select `tour-of-heroes-universal` as your
    **Repository** and the tag to match as your **Tag**.
1.  Under **Build Configuration**, select **Cloud Build configuration file (yaml or json)**.
1.  In the **Cloud Build configuration file location**, enter `cloudbuild.yaml`.
1.  Under **Substitution variables**, click **+ Add variable**.
1.  In the **Variable** field enter `_ANGULAR_APP_BUCKET_PATH` and in **Value**
    enter `gs://[PROJECT]-angular-app`, where `[PROJECT]` is the name of your project.
1.  Click **Create** to save your build trigger.

### Add your tour-of-heroes Cloud Source repository as a remote repository with the name 'google'

1.  (**OPTIONAL**: Only if not running in Cloud Shell) Set up your Google credentials for Git:

        gcloud init && git config --global credential.https://source.developers.google.com.helper gcloud.sh

2.  Add the google cloud repository as a remote:

        git remote add google \
        https://source.developers.google.com/p/$PROJECT/r/tour-of-heroes-universal

## Run the build trigger and deploy the application

1.  Tag the repository:

        git tag v0.0

2.  Push the repository to `google`:

        git push google master && git push google --tags

### Once the build and deployment finish, check that the website is deployed

1.  Open the [Cloud Build](https://console.cloud.google.com/cloud-build) console to show the build progress.
2.  Find the build that is in progress and click the link to view its progress.
3.  Once the build finishes, find the IP address of the load balancer you created above:

        gcloud compute addresses list  --filter="name=angular-app-ip" --format="value(address)"

4.  Point your browser at ```http://[ANGULAR_APP_IP]```, replacing ```[ANGULAR_APP_IP]``` with the IP address retrieved above.

## Cleanup

1.  Delete the load balancer:

        gcloud compute forwarding-rules delete http-content-rule --global --quiet

        gcloud compute target-http-proxies delete http-lb-proxy --quiet

        gcloud compute url-maps delete web-map  --quiet

        gcloud compute addresses delete angular-app-ip --global --quiet

2.  Delete the Cloud Storage bucket:

        gcloud compute backend-buckets delete $PROJECT-angular-app-backend --quiet

        gsutil rm gs://$PROJECT-angular-app/**
        gsutil rb gs://$PROJECT-angular-app

3.  Delete the build trigger:

    1. Navigate to the [build triggers page](https://console.cloud.google.com/cloud-build/triggers) of the GCP Console 
    1. On the line of the build trigger "tour-of-heroes-universal", select the menu ![trigger button](https://storage.googleapis.com/gcp-community/tutorials/cloudbuild-angular-universal/trigger-button.png)
    1. Select **Delete**

4.  Delete the Cloud Source repository:

        gcloud source repos delete tour-of-heroes-universal --quiet

5.  (OPTIONAL) Disable APIs:

        gcloud services disable sourcerepo.googleapis.com
        gcloud services disable containerregistry.googleapis.com
        gcloud services disable cloudbuild.googleapis.com
