---
title: Building Singularity containers using Cloud Build
description: Learn how to use Cloud Build to build Singularity containers for HPC workloads.
author: wkharold,vsoch
tags: Cloud Build, Singularity, HPC
date_published: 2019-02-21
---

Ward Harold | Google

Vanessa Sochat | Stanford

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to use [Cloud Build](https://cloud.google.com/cloud-build/) to build [Singularity](https://www.sylabs.io/singularity/) containers. 
In contrast to [Docker](https://www.docker.com/), the Singularity container binary is designed specifically for high performance computing (HPC) workloads. 

## Before you begin

### Set the required environment variables

Edit the file `env.sh` and replace the placeholders with the following:

* `[YOUR_ORG]`: the name of the organization that will own your project
* `[YOUR_BILLING_ACCOUNT_NAME]`: the name of the account responsible for any costs associated with your project
* `[NAME_FOR_THE_PROJECT_YOU_WILL_CREATE]`: the name of your project
* `[COMPUTE_ZONE_YOU_WANT_TO_USE]`: the name of the GCP compute zone that will contain your project

The organization and billing account should already exist. If you need to create an organization,
see [Creating and managing organizations](https://cloud.google.com/resource-manager/docs/creating-managing-organization).

Use these `gcloud` commands to retrieve the values required by `env.sh`:

```bash
gcloud organizations list
```
```bash
gcloud alpha billing accounts list
```
```bash
gcloud projects list
```
```bash
gcloud compute zones list
```

If you are creating a new project, use the name you intend to give it.

### Clone the repository

The files that you use in this tutorial are available in the
[`GoogleCloudPlatform/community` repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/singularity-containers-with-cloud-build)

Clone the repository:

```bash
git clone https://github.com/GoogleCloudPlatform/community
```

Change directory into the folder for the tutorial:

```bash
cd tutorials/singularity-containers-with-cloud-build
```

Commands in the tutorial require some of these files. If you don't clone the repository, you might see an error unless you create the example files yourself.

### Source `env.sh` to define the environment variables in your current shell session

```bash
source ./env.sh
```

### (Optional) Create a new project

To use a new project rather than an existing one, create the new project with the following commands:

```bash
gcloud projects create $PROJECT --organization=$ORG
```
```bash
gcloud beta billing projects link $PROJECT --billing-account=$(gcloud beta billing accounts list | grep $BILLING_ACCOUNT | awk '{print $1}')
```
```bash
gcloud config configurations create -- activate $PROJECT
```

### Use the desired project and zone

```bash
gcloud config set core/project $PROJECT
```
```bash
gcloud config set compute/zone $ZONE
```

### Enable the necessary GCP APIs

The following commands enable Compute Engine, Cloud Build, and Container Registry:

```bash
gcloud services enable compute.googleapis.com
```
```bash
gcloud services enable cloudbuild.googleapis.com
```
```bash
gcloud services enable containerregistry.googleapis.com
```

## Build a Singularity container

Cloud Build supports the definition and use of _custom build steps_ to extend the range of tasks it can handle.
In the first step of this section, you create a Singularity custom build step. In the second step, you use the Singularity
custom build step to build a Singularity container and save it in Cloud Storage. Once the Singuarlity custom build
step has been created in your project you can use it to create as many Singularity containers as you like.

### Create a Singularity builder

The `singularity-buildstep` directory contains the files you use to create the Singularity custom build step.

* `builder.yaml` is the recipe to create the Singularity builder. Specifically, it's a configuration file you will submit to build the custom build step.
* `Dockerfile` contains the steps required to download and build Singularity in a `go` container.

Move to that directory:

```bash
cd singularity-buildstep
```

Then use this command to build the custom build step:

```bash
gcloud builds submit --config=builder.yaml --substitutions=_SINGULARITY_VERSION="3.0.2" .
```

At the time of this writing, the latest stable version of Singularity is 3.0.2. To use a different (possibly newer) version,
modify the value of the `_SINGULARITY_VERSION` substitution accordingly; it should match a
[release tag](https://github.com/sylabs/singularity/releases) on the
[sylabs/singularity](https://github.com/sylabs/singularity) repository.

### Create a bucket

You need a place to store the containers the Singularity build step creates. In this tutorial you will use a Cloud
Storage bucket to hold your Singularity containers. You can use an existing bucket you have access to or use this
command to create a new one:

```bash
gsutil mb gs://${PROJECT}-singularity
```

### Build a Singularity container

Singularity uses a
[Singularity definition file](https://github.com/sylabs/singularity-userdocs/blob/master/definition_files.rst)
as a blueprint for building a container. The definition file contains a number of sections which control how the
`singularity build` command constructs a container. 

Go back up one directory to look at `julia.def`:

```bash
cd ..
```
```bash
cat julia.def
```
```
Bootstrap: library
From: centos:7

%runscript
# run your script here.

# check if there any arguments,
if [ -z "$@" ]; then
    # if there are none, test julia:
    echo 'println("hello world from julia container!!!")' | julia
else
    # if there is an argument, then run it! and hope its a julia script :)
    julia "$@"
fi


%environment
    PATH=/julia-1.0.3/bin:$PATH
    LD_LIBRARY_PATH=/julia-1.0.3/lib:/julia-1.0.3/lib/julia:$LD_LIBRARY_PATH
    LC_ALL=C
    export PATH LD_LIBRARY_PATH LC_ALL

%post
    yum -y update

    # install some basic tools
    yum -y install curl tar gzip

    # now, download and install julia
    curl -sSL "https://julialang-s3.julialang.org/bin/linux/x64/1.0/julia-1.0.3-linux-x86_64.tar.gz" > julia.tgz
    tar -C / -zxf julia.tgz
    rm -f julia.tgz
```

The `julia.def` file is a simple example of a Singularity definition file. It creates a [CentOS](https://www.centos.org) 7
container with the [Julia](https://julialang.org) programming language installed. When you run the container, the entry
point is the Julia executable. This means that if the user provides a script, Julia will execute it. If not, Julia will
print a "hello world" message. The file has three sections:

 * `%runscript`: The contents of this section are written to a file within the container and executed when the container
   is run.
 * `%environment`: This section defines environment variables that will be set at runtime (shell, run, exec).
 * `%post`: These commands are executed after the base operating system has been installed at build time.

To create a Singularity container from the `julia.def` definition file, use the custom Singularity build step created above.
The `cloudbuild.yaml` file specifies the steps required to build the container and store the result in a Cloud Storage
bucket.

```bash
cat cloudbuild.yaml
```
```yaml
# In this directory, run the following command to build this builder.
# $ gcloud builds submit . --config=cloudbuild.yaml --substitutions=_SINGULARITY_VERSION=3.0.0."

steps:
- name: gcr.io/$PROJECT_ID/singularity-${_SINGULARITY_VERSION}
  args: ['build', 'julia-centos.sif', 'julia.def']
artifacts:
  objects:
    location: 'gs://${PROJECT_ID}-singularity'
    paths: ['julia-centos.sif']
```

The first step (the only step in this example) runs the `singularity` command to build the `julia-centos.sif` container
from the `julia.def` definition file. The `artifacts` section directs Cloud Build to store the resulting container in the
Cloud Storage bucket you created above.

Use this command to execute the build:

```bash
gcloud builds submit --config=cloudbuild.yaml --substitutions=_SINGULARITY_VERSION="3.0.2" .
```

After the build completes, verify that the container was created using the list (`ls`) command.

```bash
gsutil ls gs://${PROJECT}-singularity/julia-centos.sif
```

If the build was successful, you should see a response similar to the following:

```
gs://my-project-singularity/julia-centos.sif
```

## Test the container

Verify that your container is working properly by downloading and executing it. To do that, you need a Compute Engine
instance with the `singularity` binary installed. This command will create the required Compute Engine instance:

```bash
gcloud compute instances create singularity-test \
  --machine-type=n1-standard-1 \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata-from-file startup-script=startup.sh
```

When the new instance is running, download the `julia-centos.sif` container:

```bash
gcloud compute ssh singularity-test --command "gsutil cp gs://${PROJECT}-singularity/julia-centos.sif ."
```

The `startup.sh` startup script downloads and builds the Singularity binary from scratch. This can take several minutes.
Use the following command to determine if the build is complete:

```bash
gcloud compute ssh singularity-test --command "which singularity"
```

When the response is `/usr/local/bin/singularity`, you are ready to proceed. Now you can run the container with this
command:

```bash
gcloud compute ssh singularity-test --command "singularity run julia-centos.sif"
```

The response should be this:

```bash
hello world from julia container!!!
```

If you prefer, you can also log into the Compute Engine instance and verify the container you built
from the command line there:

```bash
gcloud compute ssh singularity-test
```

```bash
singularity run julia-centos.sif
```
```bash
exit
```

## Clean up

Delete the test Compute Engine instance:

```bash
gcloud compute instances delete singularity-test
```

Delete the container bucket:

```bash
gsutil rm -r gs://${PROJECT}-singularity
```
