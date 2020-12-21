---
title: Using the Slurm Resource Manager to host Jupyter notebooks
description: Learn how to run your Jupyter notebooks on a Compute Engine instance managed by the Slurm Resource Manager.
author: wardharold
tags: GCE, Slurm, Jupyter
date_published: 2019-01-11
---

Ward Harold | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to run a [Jupyter Notebook](https://jupyter.org) as a job managed by the [Slurm Resource Manager](https://slurm.schedmd.com).

Slurm is a popular resource manager used in many high-performance computing centers. Jupyter notebooks are a
favorite tool of machine learning and data science specialists. While they are often run on an individual user's
laptop, there are situations that call for specialized hardware, such as GPUs or more memory or CPU cores than are
available locally. In those situations, Slurm can allocate a compute instance has the requisite hardware
or memory/CPU resources to run the user's notebook for a bounded time period.

This diagram illustrates the configuration you will create by following the tutorial steps:
![diagram](https://storage.googleapis.com/gcp-community/tutorials/using-slurm-to-host-jupyter-notebooks-review/slurm_notebook_illustration.png)

[![button](http://gstatic.com/cloudssh/images/open-btn.png)](https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/community&page=editor&tutorial=tutorials/using-slurm-to-host-jupyter-notebooks-review/index.md)

## (OPTIONAL) Create a project with a billing account attached 
**(You can also use an existing project and skip to the next step.)**

Edit [env.sh](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/using-slurm-to-host-jupyter-notebooks-review/env.sh) and replace the following:

- **`[YOUR_ORG]`**: the name of the [organization](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#cloud_platform_resource_hierarchy_and_iam_policy_hierarchy) that will own your project
- **`[YOUR_BILLING_ACCOUNT_NAME]`**: the name of the account responsible for any costs incurred by your project
- **`[NAME FOR THE PROJECT YOU WILL CREATE]`**: the name of your project
- **`[COMPUTE ZONE YOU WANT TO USE]`**: the name of the Google Cloud compute zone that will contain your project

```bash
source ./env.sh
```
```bash
gcloud projects create $PROJECT --organization=$ORG
```
```bash
gcloud beta billing projects link $PROJECT --billing-account=$(gcloud beta billing accounts list | grep $BILLING_ACCOUNT | awk '{print $1}')
```
```bash
gcloud config configurations create --activate $PROJECT
```
```bash
gcloud config set compute/zone $ZONE
```

## Enable the required Google APIs

```bash
gcloud services enable compute.googleapis.com
```

## Create a Slurm cluster

1. Clone the Slurm for Google Cloud Git repository
```bash
git clone https://github.com/schedmd/slurm-gcp.git
```
```bash
cd slurm-gcp
```

2. Modify `slurm-cluster.yaml` for your environment

You need to customize the `slurm-cluster.yaml` file for your environment before you deploy your cluster.

* Uncomment the `login_node_count` line.
* If you want more than one login node—for example, if you need to handle a large number of users—modify the value of `login_node_count` accordingly.
* Add a comma-separated list of the user IDs authorized to use your cluster on the `default user` line. Each entry should be just the user ID. For example, for `alice@example.com` the correct entry would be `alice`. If you are running the tutorial from Cloud Shell, the correct user ID is the full account name with the `@` and dot (`.`) characters replaced by an underscore (`_`); for example, for `alice@example.com` the correct entry would be `alice_example_com`.

You may also want to make one or more optional changes:

* Deploy your cluster to a different region and/or zone by modifying the values `region` and `zone`.
* Use a different machine type by changing the `compute_machine_type` value if you need, for example, more CPU cores or memory than are available with the default choice of `n1-standard-2`.
* Use an existing `vpc_net` and `vpc_subnet` combination. The network/subnet requirements are described in the file `slurm.jinja.scheme`. If you don't specify values, a new network/subnet will be created for your cluster.
* Specify a different version of Slurm for your cluster by modifying `slurm_version`. By default, the latest stable version (17.11.8 at the time of this writing) will be deployed. If you are an experienced Slurm user and need a different version, specify it here.

3. Patch the Slurm startup-script

You need to patch the script that is run on each cluster node at startup. The changes in the patch setup the symbolic links
and directories to support the installation of software packages shared across nodes and the [environment modules](http://modules.sourceforge.net) used
to access those packages.

```bash
patch scripts/startup-script.py ../startup-script.patch
```

4. Deploy Slurm using Deployment Manager

Use Deployment Manager to deploy your cluster.
```bash
gcloud deployment-manager deployments --project="$(gcloud config get-value core/project)" create slurm --config slurm-cluster.yaml
```

5. Verify that your cluster is operational

It will take five to ten minutes after the deployment completes for your cluster's configuration
to complete. Wait ten minutes and then use the following commands to verify that your cluster is operational.

Check that the cluster is ready by logging in to the login node.

```bash
gcloud compute ssh google1-login1
```

You should see a "splash screen" that looks like this.

```
                                 SSSSSS
                                SSSSSSSSS
                                SSSSSSSSS
                                SSSSSSSSS
                        SSSS     SSSSSSS     SSSS
                       SSSSSS               SSSSSS
                       SSSSSS    SSSSSSS    SSSSSS
                        SSSS    SSSSSSSSS    SSSS
                SSS             SSSSSSSSS             SSS
               SSSSS    SSSS    SSSSSSSSS    SSSS    SSSSS
                SSS    SSSSSS   SSSSSSSSS   SSSSSS    SSS
                       SSSSSS    SSSSSSS    SSSSSS
                SSS    SSSSSS               SSSSSS    SSS
               SSSSS    SSSS     SSSSSSS     SSSS    SSSSS
          S     SSS             SSSSSSSSS             SSS     S
         SSS            SSSS    SSSSSSSSS    SSSS            SSS
          S     SSS    SSSSSS   SSSSSSSSS   SSSSSS    SSS     S
               SSSSS   SSSSSS   SSSSSSSSS   SSSSSS   SSSSS
          S    SSSSS    SSSS     SSSSSSS     SSSS    SSSSS    S
    S    SSS    SSS                                   SSS    SSS    S
    S     S                                                   S     S
                SSS
                SSS
                SSS
                SSS
 SSSSSSSSSSSS   SSS   SSSS       SSSS    SSSSSSSSS   SSSSSSSSSSSSSSSSSSSS
SSSSSSSSSSSSS   SSS   SSSS       SSSS   SSSSSSSSSS  SSSSSSSSSSSSSSSSSSSSSS
SSSS            SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
SSSS            SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
SSSSSSSSSSSS    SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
 SSSSSSSSSSSS   SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
         SSSS   SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
         SSSS   SSS   SSSS       SSSS   SSSS        SSSS     SSSS     SSSS
SSSSSSSSSSSSS   SSS   SSSSSSSSSSSSSSS   SSSS        SSSS     SSSS     SSSS
SSSSSSSSSSSS    SSS    SSSSSSSSSSSSS    SSSS        SSSS     SSSS     SSSS
[alice_example_com@google1-login1 ~]$ 
```

When the cluster is ready, schedule a simple job to verify that it is working correctly:

```bash
gcloud compute ssh google1-login1 --command 'sbatch -N2 --wrap="srun hostname"'
```

```bash
gcloud compute ssh google1-login1 --command 'cat slurm-*.out'
```

You should see output that looks like this:

```
google1-compute1
google1-compute2
```

## Set up an Anaconda environment module

Environment modules update your environment variables, such as `PATH`, `MANPATH`, and `LD_LIBRARY_LOAD` to include 
information necessary to access specific software components. In this step, you install the
[Anaconda](https://www.anaconda.com) package for Python 3.x and create an environment module for it.

1. Install the Anaconda3 package

Download the Anaconda3 (version 5.3.1) package:

```bash
gcloud compute ssh google1-controller --command 'sudo wget --directory-prefix=/tmp https://repo.anaconda.com/archive/Anaconda3-5.3.1-Linux-x86_64.sh'
```

Install Anaconda3 (version 5.3.1) in the /apps directory so that each of the Slurm compute nodes can access it:

```bash
gcloud compute ssh google1-controller --command 'sudo chmod a+x /tmp/Anaconda3-5.3.1-Linux-x86_64.sh; sudo /tmp/Anaconda3-5.3.1-Linux-x86_64.sh -b -p /apps/anaconda3/5.3.1 -f'
```

2. Create a modulefile for your Anaconda3 installation

Create an anaconda3 directory in the `/apps/modulefiles` directory. Each installed version of Anaconda3 will have a separate
appropriately named modulefile.

```bash
gcloud compute ssh google1-controller --command 'sudo mkdir -p /apps/modulefiles/anaconda3'
```

Copy the modulefile for Anaconda3 (version 5.3.1) to the controller node:

```bash
cd ..
```

```bash
gcloud compute scp anaconda3-5.3.1-modulefile google1-controller:/tmp
```

Move the Anaconda3 (version 5.3.1) modulefile into the `/apps/modulefiles/anaconda3` directory:

```bash
gcloud compute ssh google1-controller --command 'sudo mv /tmp/anaconda3-5.3.1-modulefile /apps/modulefiles/anaconda3/5.3.1'
```

3. Verify that the anaconda3/5.3.1 module is available

```bash
gcloud compute ssh google1-login1 --command 'module avail'
```

You should see output that looks like this:

```
------------------------ /usr/share/Modules/modulefiles ------------------------
dot         module-git  module-info modules     null        use.own
------------------------------- /etc/modulefiles -------------------------------
mpi/openmpi-x86_64
------------------------------ /apps/modulefiles -------------------------------
anaconda3/5.3.1
```

## Run a Jupyter Notebook as a Slurm batch job

You run a Jupyter Notebook as a batch job by submitting the `notebook.batch` file to 
slurm via the `sbatch` command.

1. Copy the `notebook.batch` file to your cluster's login node.

All of the `sbatch` directives for the notebook job are at the top of the `notebook.batch`
file: 

```
#SBATCH --partition debug
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --mem-per-cpu 2G
#SBATCH --time 1-0:00:00
#SBATCH --job-name jupyter-notebook
#SBATCH --output jupyter-notebook-%J.log
```

If you need to modify them—for example, to have more memory per CPU or a different
lifetime for your notebook—do so before you copy it to your cluster's login node.

Use the `scp` command to copy `notebook.batch` to your cluster's login node:

```bash
gcloud compute scp notebook.batch google1-login1:~
```

2. Submit the notebook job using the `sbatch` command.

```bash
gcloud compute ssh google1-login1 --command 'sbatch notebook.batch'
```

You should see output that looks like this, where `[NN]` is the job number for your notebook:

```
Submitted batch job [NN]
```

3. Verify that your Jupyter Notebook started up properly.

Substitute your notebook's job number for `[NN]` in this command to verify that your
notebook job started up properly.

```bash
gcloud compute ssh google1-login1 --command 'cat jupyter-notebook-[NN].log'
```

You should see output that looks like this:

```
CloudShell port forward command for WebPreview
gcloud compute ssh google1-compute2 -- -A -t -l wkh_google_com -L 8080:10.10.0.4:8080

[I 18:41:52.465 NotebookApp] JupyterLab extension loaded from /apps/anaconda3/5.3.1/lib/python3.7/site-packages/jupyterlab
[I 18:41:52.468 NotebookApp] JupyterLab application directory is /apps/anaconda3/5.3.1/share/jupyter/lab
[I 18:41:52.480 NotebookApp] Serving notebooks from local directory: /home/wkh_google_com
[I 18:41:52.483 NotebookApp] The Jupyter Notebook is running at:
[I 18:41:52.486 NotebookApp] http://google1-compute2:8080/?token=5f8bc1a29d0bfd6f3cbdbd29186359bc47f04054b9f7cf86
[I 18:41:52.488 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
[C 18:41:52.494 NotebookApp]

    Copy/paste this URL into your browser when you connect for the first time,
    to login with a token:
        http://google1-compute2:8080/?token=5f8bc1a29d0bfd6f3cbdbd29186359bc47f04054b9f7cf86
[I 18:43:57.756 NotebookApp] 302 GET /?authuser=0 (10.10.0.4) 0.82ms
[I 18:43:57.830 NotebookApp] 302 GET /tree?authuser=0 (10.10.0.4) 1.00ms
[W 18:44:02.879 NotebookApp] 401 POST /login?next=%2Ftree%3Fauthuser%3D0 (10.10.0.4) 1.73ms referer=https://8080-dot-3011042-dot-devshell.appspot.com/login?next=%2Ftree%3Fauthuser%3D0
[W 18:44:54.375 NotebookApp] 401 POST /login?next=%2Ftree%3Fauthuser%3D0 (10.10.0.4) 4.27ms referer=https://8080-dot-3011042-dot-devshell.appspot.com/login?next=%2Ftree%3Fauthuser%3D0
[W 18:45:09.963 NotebookApp] 401 POST /login?next=%2Ftree%3Fauthuser%3D0 (10.10.0.4) 4.88ms referer=https://8080-dot-3011042-dot-devshell.appspot.com/login?next=%2Ftree%3Fauthuser%3D0
[I 18:46:29.529 NotebookApp] 302 GET /?authuser=0 (10.10.0.4) 0.70ms
[I 18:46:29.671 NotebookApp] 302 GET /tree?authuser=0 (10.10.0.4) 0.88ms
[I 18:46:33.473 NotebookApp] 302 POST /login?next=%2Ftree%3Fauthuser%3D0 (10.10.0.4) 1.14ms
[I 18:48:36.214 NotebookApp] 302 GET /?authuser=0 (10.10.0.4) 0.74ms
[I 18:49:14.889 NotebookApp] 302 GET /?authuser=0 (10.10.0.4) 0.72ms
[I 18:50:41.854 NotebookApp] 302 GET /?authuser=0 (10.10.0.4) 0.63ms
```

## Set up an SSH tunnel to your Notebook

You can access your notebook from the Cloud Shell using the Web Preview tool.

1. Get the login token for your notebook

Substitute your notebook's job number for `[NN]` in this command to get the login token for your notebook.

```
gcloud compute ssh google1-login1 --command 'cat jupyter-notebook-[NN].log' 2> /dev/null | egrep '^\[' | grep '?token' | awk -F'=' '{print $2}'
```

Save this value, because you will need it to log in to your notebook.

2. Create an SSH tunnel to your notebook

Your `jupyter-notebook-[NN].log` file contains the gcloud command you run to create an SSH
tunnel to your notebook. You can run it with this command.

Substitute your notebook's job number for `[NN]` in this command to create an SSH tunnel to your notebook.

```
$(gcloud compute ssh google1-login1 --command 'cat jupyter-notebook-[NN].log' 2> /dev/null | egrep '^gcloud')
```

## Connect to your Notebook

Click the **Web preview** button in the upper-right corner of the Cloud Shell pane, and choose **Preview on port 8080**
to connect to your notebook. 

This opens a new browser window that connects to your notebook using the SSH tunnel that you set up in the previous step. 

![Jupyter Login Screen](https://storage.googleapis.com/gcp-community/tutorials/using-slurm-to-host-jupyter-notebooks-review/jupyter_login.png)

Log in by entering the token you saved in the previous step in the **Password or token** field and then pressing the login button.

## Clean up

Delete your Slurm cluster deployment:

```bash
gcloud deployment-manager deployments --project="$(gcloud config get-value core/project)" delete slurm 
```
