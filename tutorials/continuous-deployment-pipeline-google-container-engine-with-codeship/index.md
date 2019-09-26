---
title: Continuous deployment pipeline to Google Kubernetes Engine using Codeship
description: Learn how to create a continuous deployment pipeline to Google Kubernetes Engine from Codeship.
author: kellyjandrews
tags: CD, Kubernetes Engine, Codeship, Pipeline
date_published: 2017-08-28
---

This tutorial explains how to create a continuous deployment
pipeline to Google Kubernetes Engine using Codeship. You will
learn how to deploy a containerized application when new code is merged into the
master branch and all integration tests have passed.

Continuous deployment is the practice of automating the delivery of software to
production after passing a series of tests. Although not for everyone, it should
be the goal of any software development and DevOps team not restricted by
regulatory constraints.

## Before you begin

Take the following steps to enable the Google Kubernetes Engine API:

1.  Visit the [Kubernetes Engine](https://console.cloud.google.com/projectselector/kubernetes)
    page in the Google Cloud Platform Console.
1.  Create or select a project.
1.  Wait for the API and related services to be enabled, which can take several
    minutes.
1.  [Enable billing][billing] for your project.

[billing]: https://support.google.com/cloud/answer/6293499#enable-billing

Make sure you have the following:

*  [Docker CE Version 17.03.01](https://www.docker.com/community-edition)
*  [Codeship Account](https://app.codeship.com/registrations/new)
*  [Codeship Jet CLI](https://documentation.codeship.com/pro/builds-and-configuration/cli/)
*  [`hello-express` source code](https://github.com/codeship-library/hello-express)
*  [GitHub](https://github.com/), [Bitbucket](https://bitbucket.org/), or [GitLab](https://about.gitlab.com/) account
*  [Google Cloud SDK](https://cloud.google.com/sdk/docs/quickstarts) and [kubectl](https://kubernetes.io/)

## Setting up the continuous deployment pipeline

### Step 1: Create service account

The interactions with the Google Cloud Platform API from Codeship require a service
account with permissions to the Cloud Storage and Google Kubernetes Engine services.

Follow these steps to create a service account:

1.  Visit the [Service accounts](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts)
    page in the Google Cloud Platform Console.
1.  Select your project.
1.  Click `Create Service Account`.
1.  Enter a name.
1.  Click `Select a Role` and choose the following permissions:

    * Project &rarr; Service Account Actor
    * Container &rarr; Kubernetes Engine Developer
    * Storage &rarr; Storage Admin

1.  Select `Furnish a new private key` and leave the option on `JSON`.
1.  Click Create, and then close the dialog once it is created.

After the service account is created, a `JSON` file with your credentials
automatically downloads to your computer. This file will be used in the next
step.

### Step 2: Setup environment variables

The `hello-express` source code includes the file `example.env`.  Rename this file
to `.env`.

Inside the file, you will replace the `...` with your Google Cloud Platform
project details as follows:

1.  `DEFAULT_ZONE`: Select a default [compute zone](https://cloud.google.com/compute/docs/regions-zones/regions-zones#available)
    like `us-central1-b`
1.  `APP_NAME`: Give your application a name; in this case use `hello-express`
1.  `CONTAINER_CLUSTER`: Give your container cluster a name; in this case use
    `hello-express-cluster`
1.  `GOOGLE_PROJECT_ID`: The `Project ID` is found in the [Google Cloud Engine dashboard](https://console.cloud.google.com/home/dashboard)
1.  `GOOGLE_AUTH_EMAIL`: Use the `Service Account ID` for the [service account](https://console.cloud.google.com/iam-admin/serviceaccounts)
    created in the last step.
1.  `GOOGLE_AUTH_JSON`: Add the credentials downloaded in the previous step
    here. You must replace the newlines with spaces by running
    `tr '\n' ' ' < your_file_name`.

Save the `.env` file once these items are finished.

### Step 3: Run initial deployment

You need to create your clusters and push an image in Google Kubernetes Engine initially before you
can set up a fully automated pipeline in Codeship.

Create your container clusters using the Google Cloud SDK by running the following command:

    gcloud container clusters create hello-express-cluster --zone=us-central1-b --project=google-project-id

This step takes a few minutes to complete. Once completed, you can verify the clusters are available by running the following command:

    gcloud compute instances list --project=google-project-id

which should output something like the following:

    NAME                                                 ZONE           MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP      STATUS
    gke-hello-express-cluste-default-pool-8f1e33a1-2t09  us-central1-a  n1-standard-1               10.128.0.2   130.211.202.173  RUNNING
    gke-hello-express-cluste-default-pool-8f1e33a1-nzwp  us-central1-a  n1-standard-1               10.128.0.4   104.197.248.45   RUNNING
    gke-hello-express-cluste-default-pool-8f1e33a1-xcd6  us-central1-a  n1-standard-1               10.128.0.3   130.211.196.247  RUNNING

The `hello-express` source code includes a `bin` folder with `bash` scripts that perform these tasks using the
Codeship Jet CLI.

1.  Make sure the scripts in the `bin` folder are executable. In a terminal
    window, navigate to the project folder and run the following command:

        chmod -R +x ./bin

1.  Update the `image` line in the `codeship-service.yml` file with your Google
    Cloud Platform project ID.

    ```yaml
    app:
      build:
        dockerfile: Dockerfile
        image: gcr.io/YOUR_PROJECT_IDE/hello-express # update this line using your Google Cloud Platform project ID
    ...
    ```

1.  Update the `image_name` line in the `codeship_steps.yml` file with your
    Google Cloud Platform project ID.

    ```yaml
    - name: build-image
      service: app
      command: echo "Build completed"
    - name: push-image-with-sha
      service: app
      type: push
      image_name: "gcr.io/YOUR_PROJECT_ID/hello-express" #update this line using your Google Cloud Platform project ID
      image_tag: "{{printf \"%.8s\" .CommitID}}"
      registry: https://gcr.io
      dockercfg_service: codeship_gcr_dockercfg
    - name: tag-as-master
      service: app
      type: push
      tag: master
      image_name: "gcr.io/YOUR_PROJECT_ID/hello-express" #update this line using your Google Cloud Platform project ID
      image_tag: "master"
      registry: https://gcr.io
      dockercfg_service: codeship_gcr_dockercfg
    - name: gke-initial-deployment
      service: codeship_gce_service
      tag: master
      command: bin/create-deploy
    ...
    ```

This pipeline runs each step in series. The `build-image` step instructs Codeship to build the `hello-express` Docker image on the CI server. After Codeship builds the Docker image, the `push-image-with-sha` step will push the image to Google Container Registry using the name `gcr.io/YOUR_PROJECT_ID/hello-express`, adding a tag using the first 8 characters of the commit SHA for every commit to the repository.

The third and fourth step will run only if the branch is tagged as `master`. The `tag-as-master` step will add the `master` tag to the image pushed to Google Container Registry. This indicates the image in Google Container Registry that is currently deployed. The following step, `gke-initial-deployment`, builds the Google Kubernetes Engine cluster and deploys the `gcr.io/YOUR_PROJECT_ID/hello-express` Docker image.

You will run this pipeline locally using the [Codeship Jet CLI](https://documentation.codeship.com/pro/builds-and-configuration/cli/). Since there is no git commit or branch to reference, use the `ci-commit-id` and `tag` flags with the Codeship Jet CLI to pass in test strings at runtime, (for example, `1234ABCD` and `master`). The build on the Codeship CI server populates `ci-commit-id` with the git commit SHA, and `tag` with the branch or tag name. Finally, the `--push` flag instructs the Codeship Jet CLI to run the push steps in the `codeship-steps.yml` file.  

    jet steps --ci-commit-id 1234ABCD --tag master --push

This command creates your initial deployment and exposes the application. Once completed, navigate to the
[Discovery](https://console.cloud.google.com/kubernetes/discovery) page in the
Google Cloud Platform Console to verify the status is `ok`. Click the endpoint
to open the application in the browser. You should see `Hello Express!`.

### Step 4: Create a Codeship project

Now that you have set up the container cluster and deployed the application, you
can create the Codeship project. This project will connect to your source
control management service. Codeship integrates with the following services:

* [GitHub](https://codeship.com/github)
* [Bitbucket](https://codeship.com/bitbucket)
* [GitLab](https://codeship.com/gitlab)

Use the following steps to create a Codeship project:

1.  Create a new repository.
1.  Copy the clone URL.
1.  Visit the [Projects](https://app.codeship.com/projects) page in the Codeship
    dashboard.
1.  Click `New Project`.
1.  Select the service where you created the repository.
1.  Paste the clone URL in the `Repository Clone URL` field and click `Connect`.
1.  Click the `Select Pro Project` button.

![Select Pro Project](https://storage.googleapis.com/gcp-community/tutorials/continuous-deployment-pipeline-google-container-engine-with-codeship/select_pro_project.png "Select Pro Project")

### Step 5: Encrypt environment variables

You will now encrypt the `.env` file using the Codeship AES key provided in the
project.

Follow these steps to create an encrypted environment file:

1.  Navigate to the new project's `General` page.
1.  Scroll down to find the `AES Key` header.
1.  Click `Download Key`.
1.  Move the downloaded file to the `hello-express` source code root folder.
1.  Rename this file to `codeship.aes`.

After you have `codeship.aes` in the `hello-express` source code root folder, you
can run the encrypt command:

    jet encrypt .env encrypted.env

After you encrypt the `.env` file, you need to update the
`codeship-services.yml` file to use the encrypted file:

```yaml
app:
  build:
    dockerfile: Dockerfile
    image: gcr.io/YOUR_PROJECT_ID/hello-express
codeship_gcr_dockercfg:
  image: codeship/gcr-dockercfg-generator
  encrypted_env_file: encrypted.env
  add_docker: true
codeship_gce_service:
  image: codeship/google-cloud-deployment
  encrypted_env_file: encrypted.env
  add_docker: true
  working_dir: /deploy
  volumes:
    - ./:/deploy
```

### Step 6: Commit code to run Codeship build

Codeship will trigger a new build when you push a commit to the remote
repository. Before you commit the changes, ensure the following files are
listed in `.gitignore`:

    codeship.aes
    .env
    /path/to/your/service-account.json

These three files should not be included in your remote repository, as they
contain sensitive data. Be sure to exclude them from any commits.

You also need to update your `codeship-steps.yml` file to use the
`gke-update-services` step.

```yaml
...
#- name: gke-initial-deployment
#  service: codeship_gce_service
#  tag: master
#  command: bin/create-deploy
- name: gke-update-services
  service: codeship_gce_service
  tag: master
  command: bin/deploy
```

After you save these changes, stage all of these files for a commit. Commit
the changes to the master branch, and push to your remote repository. After the
push is complete, return to the Codeship project dashboard and watch for a green
build.

### Step 7: Deploy an update to your application (optional)

You can now modify the code in the `server.js` file to return something different.
Change `'Hello Express!'` to something like `'Hello World!'`. Once you have
changed the application, commit the change and push to your remote repository.

After the Codeship process is completed, navigate to the application
endpoint to verify your changes have taken effect.

## Cleaning up

After completing the tutorial, follow these steps to remove the resources from your Google Cloud Platform account to prevent any charges:

1. Delete the Service: This step will deallocate the Cloud Load Balancer created for your Service:

        kubectl delete service hello-express

1. Wait for the Load Balancer provisioned for the hello-web Service to be deleted: The load balancer is deleted asynchronously in the background when you run kubectl delete. Wait until the load balancer is deleted by watching the output of the following command:

        gcloud compute forwarding-rules list

1. Delete the container cluster: This step will delete the resources that make up the container cluster, such as the compute instances, disks and network resources.

        gcloud container clusters delete hello-cluster
