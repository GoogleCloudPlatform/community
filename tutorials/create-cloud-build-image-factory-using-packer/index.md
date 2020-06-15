---
title: Create a Cloud Build image factory using Packer
description: Learn how to create an image factory using Cloud Build and Packer.
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

- A Google Cloud account
- One of the following:
    - At least project editor access to an existing project
    - Organization permissions to create a new project in an existing organization

## (Optional) Create a project with a billing account attached

This task will help you setup a new Google Cloud project in which to run your Packer
build factory. You can also use an existing project and skip to the next
step.

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

## Set the project variable

Skip this step if you created a new project in the previous section.

Ensure that you're working with the project that you want to use with `gcloud`.
For more information on configurations see [configurations](https://cloud.google.com/sdk/gcloud/reference/config/configurations/).
Fill in `[CONFIGURATION NAME]` with the name of the configuration you want to use.

```sh
gcloud config configurations activate [CONFIGURATION NAME] #The configuration for the project you want to use
PROJECT=$(gcloud config get-value project)
```

## Copy the files for this tutorial to a new working directory and git repository

1.  Create a new working directory:

        mkdir helloworld-image-factory
        cd helloworld-image-factory

2.  Download the tutorial scripts:

         curl -L https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/create-cloud-build-image-factory-using-packer/cloudbuild.yaml >cloudbuild.yaml
         curl -L https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/create-cloud-build-image-factory-using-packer/install-website.sh >install-website.sh 

3.  Initialize a git repository in the working directory:

        git init

## Enable the required services

    gcloud services enable sourcerepo.googleapis.com
    gcloud services enable cloudapis.googleapis.com
    gcloud services enable compute.googleapis.com
    gcloud services enable servicemanagement.googleapis.com
    gcloud services enable storage-api.googleapis.com
    gcloud services enable cloudbuild.googleapis.com

## Give the Cloud Build user Project Editor permissions

Find the Cloud Build service account and add the editor role to it:

    CLOUD_BUILD_ACCOUNT=$(gcloud projects get-iam-policy $PROJECT --filter="(bindings.role:roles/cloudbuild.builds.builder)"  --flatten="bindings[].members" --format="value(bindings.members[])")

    gcloud projects add-iam-policy-binding $PROJECT \
      --member $CLOUD_BUILD_ACCOUNT \
      --role roles/editor

## Create the Cloud Source Repository for your image creator

    gcloud source repos create helloworld-image-factory

## Create the build trigger for the image creator source repository

You can create a trigger on the [build triggers page](https://console.cloud.google.com/cloud-build/triggers)
of the Cloud Console by following these steps:

1.  Click **Create Trigger**.
1.  In the **Name** field, enter `Hello world image factory`.
1.  Under **Event**, select **Push to a tag**.
1.  Under **Source**, select `helloworld-image-factory` as your
    **Repository** and the tag to match as your **Tag**.
1.  Under **Build Configuration**, select **Cloud Build configuration file (yaml or json)**.
1.  In the **Cloud Build configuration file location**, enter `cloudbuild.yaml`.
1.  Under **Substitution variables**, click **+ Add variable**.
1.  In the **Variable** field enter `_IMAGE_FAMILY` and in **Value** enter `centos-7`.
1.  In the **Variable** field enter `_IMAGE_ZONE` and in **Value** enter `$ZONE`.
1.  Click **Create** to save your build trigger.

To see a list of image families:

    gcloud compute images list | awk '{print $3}'  | awk '!a[$0]++'

## Add the packer Cloud Build image to your project

Get the builder from the community repository and submit it to your project:

    project_dir=$(pwd)
    cd /tmp
    git clone https://github.com/GoogleCloudPlatform/cloud-builders-community.git
    cd cloud-builders-community/packer
    gcloud builds submit --config cloudbuild.yaml
    rm -rf /tmp/cloud-builders-community
    cd $project_dir

## Add your repository as a remote repository and push

1.  (Only if not running in Cloud Shell) Set up your Google credentials for git:

        gcloud init && git config --global credential.https://source.developers.google.com.helper gcloud.sh

2.  Add the `google` repository as a remote:

        git remote add google \
          https://source.developers.google.com/p/$PROJECT/r/helloworld-image-factory

## Task 9: Push the repository and tags to google

1.  Add your files to the repository:

        git add .
        git commit -m " first image" 

1.  Tag the repository with a version number:

        git tag v0.1

2.  Push the branch and the tags to your `google` repository:

        git push google master --tags

## View build progress

1.  Open the [**Cloud Build** page](https://console.cloud.google.com/cloud-build) in the Cloud Console
    to show the build progress.
2.  Find the build that is in progress and click the link to view its progress.

## Create a compute instance for the image in your gcp project

Once the build completes, create the instance and requisite firewall rule to test that the image works.

    gcloud compute firewall-rules create http --allow=tcp:80 --target-tags=http-server --source-ranges=0.0.0.0/0
    gcloud compute instances create helloworld-from-factory --image https://www.googleapis.com/compute/v1/projects/$PROJECT/global/images/helloworld-v01 --tags=http-server --zone=$ZONE

## Check the website

Wait a minute or two and open the browser to the IP address of the instance to see the special message.

1.  Retrieve the instace IP address:

        gcloud compute instances list --filter="name:helloworld*" --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

2.  Go to the IP address in the browser and make sure that you see the "Hello from the image factory!" message.

## Cleaning up

1.  Delete the firewall rule, the instance, and the image:

        gcloud compute firewall-rules delete --quiet http
        gcloud compute instances delete --quiet helloworld-from-factory
        gcloud compute images delete --quiet helloworld-v01

2.  Delete the packer Cloud Build image:

        gcloud container images delete --quiet gcr.io/$PROJECT/packer  --force-delete-tags

3.  Delete the source repository:

        gcloud source repos delete --quiet helloworld-image-factory
        
    Only do this if you don't want to perform the tutorial in this project again. The repository name won't be usable
    again for up to seven days.
