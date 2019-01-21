---
title: Building Singularity Containers using Cloud Build
description: Learn how to use Cloud Build to build Singularity Containers for HPC workloads
author: wardharold
tags: Cloud Build, Singularity, HPC
date_published: 2019-01-18
---
This tutorial shows you how to use [Cloud Build](https://cloud.google.com/cloud-build/) to build [Singularity](https://www.sylabs.io/singularity/) containers. 
In constrast to [Docker](https://www.docker.com/), the Singularity container mechanism is designed specifically for HPC workloads. 

[![button](http://gstatic.com/cloudssh/images/open-btn.png)](https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/community&page=editor&tutorial=tutorials/singularity-containers-with-cloud-build/index.md)

## (OPTIONAL) Create a project with a billing account attached 
**(you can also use an existing project and skip to the next step)**

### Setup project related environment variables
Edit the file <walkthrough-editor-open-file filePath="community/tutorials/singularity-containers-with-cloud-build/env.sh">env.sh</walkthrough-editor-open-file> and replace
* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/env.sh" regex="\[YOUR_ORG\]">[YOUR_ORG]</walkthrough-editor-select-regex> with the name of the organization that will own your project
* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/env.sh" regex="\[YOUR_BILLING_ACCOUNT_NAME\]">[YOUR_BILLING_ACCOUNT_NAME]</walkthrough-editor-select-regex> with the name of the account responsible for any costs associated with your project
* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/env.sh" regex="\[NAME FOR THE PROJECT YOU WILL CREATE\]">[NAME FOR THE PROJECT YOU WILL CREATE]</walkthrough-editor-select-regex> with the name of your project
* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/env.sh" regex="\[COMPUTE ZONE YOU WANT TO USE\]">[COMPUTE ZONE YOU WANT TO USE]</walkthrough-editor-select-regex> with the name of the Cloud Platform compute zone that will contain your project

```bash
source ./env.sh
```

### Create your project
```bash
gcloud projects create $PROJECT --organization=$ORG
```
```bash
gcloud beta billing projects link $PROJECT --billing-account=$(gcloud beta billing accounts list | grep $BILLING_ACCOUNT | awk '{print $1}')
```
```bash
gcloud config configurations create -- activate $PROJECT
```
```bash
gcloud config set compute/zone $ZONE
```

## Enable the required Google APIs
```bash
gcloud services enable compute.googleapis.com
```
```bash
gcloud services enable cloudbuild.googleapis.com
```
```bash
gcloud services enable containerregistry.googleapis.com
```

## Create a custom Singularity build step

Cloud Build supports the definition and use of *custom build steps* to extend the range of tasks it can handle.
You will create a Singularity custom build step to use when building your Singularity containers. 

```bash
cd singularity-buildstep
```

The ```singularity-buildstep```
directory contains two files you will use to create the Singularity build step for your project

* ```cloudbuild.yaml``` is a Cloud Build configuration file you will submit to build the custom build step
* ```Dockerfile``` contains the steps required to download and build Singularity in a ```go``` container

Use this command to build the custom build step.
```bash
gcloud builds submit --config=cloudbuild.yaml --substitutions=_SINGULARITY_VERSION="3.0.0" .
```

At the time of this writing the latest stable version of Singularity is 3.0.0. To use a different, possibly newer, version modify the
value of the _SINGULARITY_VERSION substitution accordingly.

## Build a Singularity container

Singularity uses a [Singularity Definition File](https://github.com/sylabs/singularity-userdocs/blob/master/definition_files.rst) as a
blueprint for building a container. The definition file contains a number of sections which control how the ```singularity build```
command constructs a container.

```bash
cd ..
```

The <walkthrough-editor-open-file filePath="community/tutorials/singularity-containers-with-cloud-build/julia.def">julia.def</walkthrough-editor-open-file> file is a simple example of a Singularity definition file. It creates a [CentOS](https://www.centos.org) 7 container
with the [Julia](https://julialang.org) programming language installed, when the container is executed it uses Julia to execute a script
or print a greeting message if no script is provided on the command line. The file has three sections.

* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/julia.def" regex="\%post">%post</walkthrough-editor-select-regex> these commands are executed after the base operating system has been installed at build time
* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/julia.def" regex="\%environment">%environment</walkthrough-editor-select-regex> this section defines environment variables that will be set at runtime
* <walkthrough-editor-select-regex filePath="community/tutorials/singularity-containers-with-cloud-build/julia.def" regex="\%runscript">%runscript</walkthrough-editor-select-regex> the contents of this section are written to a file within the container and executed when the container is run

The <walkthrough-editor-open-file filePath="community/tutorials/singularity-containers-with-cloud-build/cloudbuild.yaml">cloudbuild.yaml</walkthrough-editor-open-file> file uses the Singularity custom build step to create a container from the ```julia.def```
defintion file. The ```singularity build``` command takes the ```julia.def``` definition file and produces a Singularity
Image Format container named ```julia-centos.sif```. The resulting container is written to a Cloud Storage bucket rather
than the Container Registry since it isn't a Docker container image.

Before you build the container create the Cloud Storage bucket where the build will store it.
```bash
gsutil mb gs://${PROJECT_ID}-singularity
```

Use this command to build the container.
```bash
gcloud builds submit --config=cloudbuild.yaml --substitutions=_SINGULARITY_VERSION="3.0.0" .
```

Once the build completes verify that the container with created using the command.
```bash
gsutil ls gs://${PROJECT_ID}-singularity/julia-centos.sif
```

If the build was successful you should see this.
```
gs://wkh-goog-le-com-slurm-singularity/julia-centos.sif
```

## Test the container

Verify your container is working properly by downloading and executing it. You will need a
compute instance with singularity installed. This command will create the compute required
instance.

```bash
gcloud compute instances create singularity-test \
  --machine-type=n1-standard-1 \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata-from-file startup-script=startup.sh
```

Download the container with this command.
```bash
gcloud compute ssh singularity-test --command "gsutil cp gs://${PROJECT_ID}-singularity/julia-centos.sif ."
```

Use ```singularity run``` to execute the container.
```bash
gcloud compute ssh singularity-test --command "singularity run julia-centos.sif"
```

You should see the response
```
hello world from julia container!!!
```

## Clean up

Delete the test compute instance.
```bash
gcloud compute instances delete singularity-test
```

Delete the container bucket.
```bash
gsutil rm -r gs://${PROJECT_ID}-singularity
```
