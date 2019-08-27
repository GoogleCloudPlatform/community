---
title: Create A Cloud Build Image Factory Using Packer
description: Learn how to create an image factory using Google Cloud Build and Packer.
author: johnlabarge
tags: Cloud Build, Packer, Compute Engine, Image
date_published: 2018-09-14
---

This tutorial will show you how to create an image factory using Cloud Build and
[Packer by HashiCorp](https://packer.io). The image factory will automatically
create new images from a Cloud Source Repository every time a new tag is pushed
to that repository as depicted in the diagram below.

![ push to repository triggers cloud build with packer which builds machine image](https://storage.googleapis.com/gcp-community/tutorials/create-cloud-build-image-factory-using-packer/packer-tutorial.png)

## Prerequisites

1.  A Google Cloud account
1.  At least project editor access to an existing project
1.  Or organization permissions to create a new project in an existing
    organization [get a trial account here](https://console.cloud.google.com/freetrial?authuser=2&_ga=2.213928212.-2042919442.1528299768&_gac=1.89261801.1536929612.CjwKCAjwuO3cBRAyEiwAzOxKslw2lWJAN82nAhsu1azihQgX_7aQjek2MPEjanoAwKL5g70Rp0b9zRoCgFwQAvD_BwE)

## Task 0 (OPTIONAL): Create a project with a billing account attached

This task will help you setup a new GCP project in which to run your packer
build factory. **(you can also use an existing project and skip to the next
step)**

```sh
PROJECT=[NEW PROJECT NAME]
ORG=[YOUR ORGANIZATION NAME]
BILLING_ACCOUNT=[YOUR_BILLING_ACCOUNT_NAME]
ZONE=[COMPUTE ZONE YOU WANT TO USE]
ACCOUNT=[GOOGLE ACCOUNT YOU WANT TO USE] or $(gcloud config get-value account)

gcloud projects create "$PROJECT" --organization=$(gcloud organizations list --format="value(name)" --filter="(displayName='$ORG')")
gcloud beta billing projects link $PROJECT --billing-account=$(gcloud alpha billing accounts list --format='value(name)' --filter="(displayName='$BILLING_ACCOUNT')")
gcloud config configurations create --activate $PROJECT
gcloud config set project $PROJECT
gcloud config set compute/zone $ZONE
gcloud config set account $ACCOUNT
```

## Task 1: Set the project variable (Skip this step if you created a new project above)

Ensure you are working with the project you want to use in gcloud.
For more information on configuraitons see [configurations](https://cloud.google.com/sdk/gcloud/reference/config/configurations/).
Fill in `[CONFIGURATION NAME]` with the name of the configuration you want to use.

```sh
gcloud config configurations activate [CONFIGURATION NAME] #The configuration for the project you want to use
PROJECT=$(gcloud config get-value project)
```

## Task 2: Copy the files for this tutorial to a new working directory and git repository

1.  Create a new working directory

        mkdir helloworld-image-factory
        cd helloworld-image-factory

2.  Download the tutorial scripts 

         curl -L https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/create-cloud-build-image-factory-using-packer/cloudbuild.yaml >cloudbuild.yaml
         curl -L https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/create-cloud-build-image-factory-using-packer/install-website.sh >install-website.sh 

3.  Initialize a git repository in the working directory

        git init

## Task 3: Enable the required services

    gcloud services enable sourcerepo.googleapis.com
    gcloud services enable cloudapis.googleapis.com
    gcloud services enable compute.googleapis.com
    gcloud services enable servicemanagement.googleapis.com
    gcloud services enable storage-api.googleapis.com
    gcloud services enable cloudbuild.googleapis.com

## Task 4: Give the Cloud Build user Project Editor permissions

First find the cloudbuild service account. Next add the editor role to it.

    CLOUD_BUILD_ACCOUNT=$(gcloud projects get-iam-policy $PROJECT --filter="(bindings.role:roles/cloudbuild.builds.builder)"  --flatten="bindings[].members" --format="value(bindings.members[])")

    gcloud projects add-iam-policy-binding $PROJECT \
      --member $CLOUD_BUILD_ACCOUNT \
      --role roles/editor

## Task 5: Create the Cloud Source Repository for your image creator

    gcloud source repos create helloworld-image-factory

## Task 6: Create the build trigger for the image creator source repository

You can create a trigger on the [build triggers page](https://console.cloud.google.com/cloud-build/triggers) of the GCP Console by following these steps:

1. Click **"Create Trigger"**
1. Select "Cloud Source Repository" and click "Continue".
1. Select "helloworld-image-factory" and click "Continue".
1. Enter "Hello world image factory" for "Name".
1. Set the trigger for "Tag".
1. Set the build type to "cloudbuild.yaml".
1. Set the substitution, `_IMAGE_FAMILY` to centos-7.
1. Set the substitution, `_IMAGE_ZONE` to the zone you want to use the value of `$ZONE`.
1. Click "Create Trigger".

**Note: To see a list of image families:**

    gcloud compute images list | awk '{print $3}'  | awk '!a[$0]++'

## Task 7: Add the packer Cloud Build image to your project

Grab the builder from the community repo and submit it to your project.

    project_dir=$(pwd)
    cd /tmp
    git clone https://github.com/GoogleCloudPlatform/cloud-builders-community.git
    cd cloud-builders-community/packer
    gcloud builds submit --config cloudbuild.yaml
    rm -rf /tmp/cloud-builders-community
    cd $project_dir

## Task 8: Add your helloworld-image-factory google repository as a remote repository with the name 'google' and push

1.  (Only if not running in Cloud Shell) setup your google credentials for git.

        gcloud init && git config --global credential.https://source.developers.google.com.helper gcloud.sh

2.  Add the google cloud repo as a remote.

        git remote add google \
          https://source.developers.google.com/p/$PROJECT/r/helloworld-image-factory

## Task 9: Push the repository and tags to google

1.  Add your files to the repository

        git add .
        git commit -m " first image" 

1.  Tag the repository with a version number.

        git tag v0.1

2.  Push the branch and the tags to your google repository.

        git push google master --tags

## Task 10: View build progress

1.  Open up the [Cloud Build](https://console.cloud.google.com/cloud-build) console to show the build progress.
2.  Find the build that is in progress and click the link to view its progress.

## Task 11: Create a compute instance for the image in your gcp project

Once the build completes, create the instance and requisite firewall rule to test that the image works.

    gcloud compute firewall-rules create http --allow=tcp:80 --target-tags=http-server --source-ranges=0.0.0.0/0
    gcloud compute instances create helloworld-from-factory --image https://www.googleapis.com/compute/v1/projects/$PROJECT/global/images/helloworld-v01 --tags=http-server --zone=$ZONE

## Task 12: Check the website to make sure it's up!

Wait a minute or two minutes and open the browser to the ip address of the instance to see the special message.

1.  Retrieve the instace ip:

        gcloud compute instances list --filter="name:helloworld*" --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

2.  Open the IP in the browser and make sure you see the "Hello from the image factory!" message.

## Cleaning up

1.  Delete the firewall rule, the instance and the image.

        gcloud compute firewall-rules delete --quiet http
        gcloud compute instances delete --quiet helloworld-from-factory
        gcloud compute images delete --quiet helloworld-v01

2.  Delete the packer Cloud Build Image

        gcloud container images delete --quiet gcr.io/$PROJECT/packer  --force-delete-tags

3.  Delete the source repository. (NOTE only do this if you don't want to
    perform the tutorial in this project again as the repo name won't be usable
    again for up to seven days.)

        gcloud source repos delete --quiet helloworld-image-factory
