---
title: Building Singularity Containers using Cloud Build
description: Learn how to use Cloud Build to build Singularity Containers for HPC workloads
author: wardharold
tags: Cloud Build, Singularity, HPC
date_published: 2019-01-18
---

This tutorial shows you how to use [Cloud Build](https://cloud.google.com/cloud-build/) to build [Singularity](https://www.sylabs.io/singularity/) containers. 
In constrast to [Docker](https://www.docker.com/), the Singularity container binary is designed specifically for HPC workloads. 

[![button](http://gstatic.com/cloudssh/images/open-btn.png)](https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/community&page=editor&tutorial=tutorials/singularity-containers-with-cloud-build/tutorial.md)

### How do I launch jobs on the cloud?

If you are traditionally an HPC user, you are most likely familiar with working
on a command line, and specifically launching jobs on a [SLURM](https://slurm.schedmd.com/) or 
[Sun Grid Engine](http://gridscheduler.sourceforge.net/) cluster with `qsub` or `sbatch`.
The cloud equivalent of that is [gcloud](https://cloud.google.com/sdk/install). With gcloud you
can manage and interact with resources on Google Cloud, and you don't need to leave your terminal.

If you haven't yet, be sure that you have [installed gcloud](https://cloud.google.com/sdk/install)
on your machine to interact with Google Cloud. You can next proceed by either creating a new project, or using an already existing one.

## Project Setup

The first sections here will help you to set up your project and working space.
This really only needs to be done once. If you already have done these steps,
you can source your env.sh and move on to creating [Singularity Builds](#singulrity-build)

### Step 1: Project environment variables

For this first step, you need to define some important variables.
Edit the file env.sh and replace

* [YOUR_ORG] with the name of the organization that will own your project
* [YOUR_BILLING_ACCOUNT_NAME] with the name of the account responsible for any costs associated with your project
* [NAME FOR THE PROJECT YOU WILL CREATE] with the name of your project
* [COMPUTE ZONE YOU WANT TO USE] with the name of the Cloud Platform compute zone that will contain your project

The Organization and billing account should already exist (if you need to create an organization,
see the [documentation here](https://cloud.google.com/resource-manager/docs/creating-managing-organization)), and if you are creating a new project, you can derive the the project name and zone right now! Otherwise,
you can fill in an existing project name.

**How do I find these variables on the command line?**

If you already have gcloud installed and an organization and/or project in mind, it can be a hassle to
go to a web browser and click around. Here is how you can look up your organization,
billing account name, project, and zone:

```bash

# List organizations - you can use the name or the id
$ gcloud organizations list

# List billing accounts
$ gcloud alpha billing accounts list

# List projects
$ gcloud projects list

# List zones
$ gcloud compute zones list

```

When you have your env.sh template filled in, source it! This will 
define the environment variables to your current shell session.

```bash
$ source ./env.sh
```


### Step 2: (Optional) Project Creation

If you defined a new project in the step above, you need to use the gcloud
command to create it. Otherwise, skip over this step. Nothing to see here, folks.

```bash
$ gcloud projects create $PROJECT --organization=$ORG
```
```bash
$ gcloud beta billing projects link $PROJECT --billing-account=$(gcloud beta billing accounts list | grep $BILLING_ACCOUNT | awk '{print $1}')
```
```bash
$ gcloud config configurations create -- activate $PROJECT
```

### Step 3: Enable APIs and Set Project

Once you've created the project, it's good to ensure it's the active one.

```bash
$ gcloud config set compute/zone $ZONE
Updated property [compute/zone].
```

The following commands will enable Google Compute Engine, Google Cloud Builder,
and Google Container Registry:

```bash
$ gcloud services enable compute.googleapis.com
$ gcloud services enable cloudbuild.googleapis.com
$ gcloud services enable containerregistry.googleapis.com
```

## Singularity Build

The next section will walk you through issuing a gcloud command to build
a container. Specifically, the first step is *not* actually building the container 
- it's basically defining the builder we will use in future steps (with build recipes).
Once we have this custom build step defined, then we can use it against a Singularity recipe
to build a container and send it to Google Storage. Let's go!

### Step 1. Create a Singularity build step

Cloud Build supports the definition and use of *custom build steps* to extend the range of tasks it can handle. You will create a Singularity custom build step to use when building your Singularity containers. 

```bash
cd singularity-buildstep
```

This would ideally be a *version controlled* Github repository folder. For now, we can
use this local folder - this ```singularity-buildstep``` directory contains two files you will use to create the Singularity build step for your project.

* ```cloudbuild.yaml``` is a Cloud Build configuration file you will submit to build the custom build step
* ```Dockerfile``` contains the steps required to download and build Singularity in a ```go``` container

Use this command to build the custom build step.

```bash
$ gcloud builds submit --config=cloudbuild.yaml --substitutions=_SINGULARITY_VERSION="3.0.2" .
```

At the time of this writing the latest stable version of Singularity is 3.0.2. 
To use a different, possibly newer, version modify the value of the _SINGULARITY_VERSION 
substitution accordingly. What does this verison coincide with?
It should match a [release tag](https://github.com/sylabs/singularity/releases) on the [sylabs/singularity](https://github.com/sylabs/singularity) repository.


**Help! It says that gcloud builds isn't a valid command**

You likely need to update your gcloud SDK installation, as follows:

```bash
$ gcloud components update
```

If you installed from a package manager (e.g., apt-get or yum) you might get an
error message that you should update via your package manager. If this update fails,
you can [follow instructions here](https://cloud.google.com/sdk/docs/uninstall-cloud-sdk) 
to completely remove and use the [installer](https://cloud.google.com/sdk/docs/downloads-interactive)
to install the most uptodate version.


### Step 2: Build a Singularity container

Singularity uses a [Singularity Definition File](https://github.com/sylabs/singularity-userdocs/blob/master/definition_files.rst) as a blueprint for building a container. The definition file 
contains a number of sections which control how the ```singularity build```
command constructs a container. Let's go back up one directory to look at [julia.def](../julia.def)

```bash
$ cd ..
```

The julia.def file is a simple example of a Singularity definition file. 
It creates a [CentOS](https://www.centos.org) 7 container with the 
[Julia](https://julialang.org) programming language installed. When you run 
the container, the entrypoint is the Julia executable. This means that if the user 
provides a script, Julia will execute it. If not, an interactive shell will
greet the user. The file has three sections.

 * %post: is a section of commands that are executed after the base operating system has been installed at build time
 * %environment: this section defines environment variables that will be set at runtime (shell, run, exec)
 * %runscript: the contents of this section are written to a file within the container and executed when the container is run

The cloudbuild.yaml file uses the Singularity custom build step to create a container from the ```julia.def```
defintion file. The ```singularity build``` command takes the ```julia.def``` definition file and produces a Singularity
Image Format container named ```julia-centos.sif```. The resulting container is written to a Cloud Storage bucket rather
than the Container Registry since it isn't a Docker container image.

Before you build the container create the Cloud Storage bucket where the build will store it.
```bash
gsutil mb gs://${PROJECT_ID}-singularity
```

Use this command to build the container.
```bash
gcloud builds submit --config=cloudbuild.yaml --substitutions=_SINGULARITY_VERSION="3.0.2" .
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
