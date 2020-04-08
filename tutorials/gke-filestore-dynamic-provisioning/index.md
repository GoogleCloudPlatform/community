---
title: Dynamically provision GKE storage from Cloud Filestore using the NFS-Client provisioner
description: Learn how to deploy the NFS-Client provisioner in a GKE cluster to dynamically provision storage from Cloud Filestore.
author: wardharold
tags: GKE, Filestore, Storage, NFS
date_published: 2018-09-26
---
This tutorial shows you how to [dynamically provision](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning) 
Kubernetes storage volumes in Google Kubernetes Engine 
from [Cloud Filestore](https://cloud.google.com/filestore/) using the 
[Kubernetes NFS-Client Provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs-client). Dynamic 
provisioning allows storage volumes to be created on demand in the NFS volume managed by a Cloud Filestore instance. Typical
use cases include running databases, *e.g.*, [PostgreSQL](https://www.postgresql.org/), or a content management system like [WordPress](https://wordpress.com/) in a Kubernetes cluster.

[![button](http://gstatic.com/cloudssh/images/open-btn.png)](https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/community&page=editor&tutorial=tutorials/gke-filestore-dynamic-provisioning/index.md)

## (OPTIONAL) Create a project with a billing account attached 
**(you can also use an existing project and skip to the next step)**

```sh
ORG=[YOUR_ORG]
BILLING_ACCOUNT=[YOUR_BILLING_ACCOUNT_NAME]
PROJECT=[NAME FOR THE PROJECT YOU WILL CREATE]
ZONE=[COMPUTE ZONE YOU WANT TO USE]
gcloud projects create $PROJECT --organization=$ORG
gcloud beta billing projects link $PROJECT --billing-account=$(gcloud beta billing accounts list | grep $BILLING_ACCOUNT | awk '{print $1}')
gcloud config configurations create -- activate $PROJECT
gcloud config set compute/zone $ZONE
```

## Enable the required Google APIs

```sh
gcloud services enable file.googleapis.com
```

## Create a Cloud Filestore volume

1. Create a Cloud Filestore instance with 1TB of storage capacity

    ```sh
    FS=[NAME FOR THE FILESTORE YOU WILL CREATE]
    gcloud beta filestore instances create ${FS} \
        --project=${PROJECT} \
        --zone=${ZONE} \
        --tier=STANDARD \
        --file-share=name="volumes",capacity=1TB \
        --network=name="default"
    ```

2. Retrieve the IP address of the Cloud Filestore instance

    ```sh
    FSADDR=$(gcloud beta filestore instances describe ${FS} \
         --project=${PROJECT} \
         --zone=${ZONE} \
         --format="value(networks.ipAddresses[0])")
    ```

## Create a Kubernetes Engine cluster

1. Create the cluster and get its credentials

    ```sh
    CLUSTER=[NAME OF THE KUBERNETES CLUSTER YOU WILL CREATE]
    gcloud container clusters create ${CLUSTER}
    gcloud container clusters get-credentials ${CLUSTER}
    ```

2. Grant yourself cluster-admin privileges

    ```sh
    ACCOUNT=$(gcloud config get-value core/account)
    kubectl create clusterrolebinding core-cluster-admin-binding \
        --user ${ACCOUNT} \
        --clusterrole cluster-admin
    ```

3. Install [Helm](https://github.com/helm/helm)

    Download the [desired version](https://github.com/helm/helm/releases) and unpack it.

        wget https://storage.googleapis.com/kubernetes-helm/helm-v2.11.0-linux-amd64.tar.gz
        tar xf helm-v2.11.0-linux-amd64.tar.gz

    Add the `helm` binary to `/usr/local/bin`.

        sudo ln -s $PWD/linux-amd64/helm /usr/local/bin/helm

    Create a file named `rbac-config.yaml` containing the following:

    ```yaml
    apiVersion: v1
    kind: ServiceAccount
    metadata:
            name: tiller
            namespace: kube-system
    ---
    apiVersion: rbac.authorization.k8s.io/v1beta1
    kind: ClusterRoleBinding
    metadata:
            name: tiller
    roleRef:
            apiGroup: rbac.authorization.k8s.io
            kind: ClusterRole
            name: cluster-admin
    subjects:
            - kind: ServiceAccount
            name: tiller
            namespace: kube-system
    ```

    Create the `tiller` service account and `cluster-admin` role binding.

        kubectl apply -f rbac-config.yaml

    Initialize Helm.

        helm init --service-account tiller

## Deploy the NFS-Client Provisioner

Create an instance of NFS-Client Provisioner connected to the Cloud Filestore instance you created earlier 
via its IP address (`${FSADDR}`). The NFS-Client Provisioner creates a new storage class: `nfs-client`. Persistent
volume claims against that storage class will be fulfilled by creating persistent volumes backed by directories
under the `/volumes` directory on the Cloud Filestore instance's managed storage.

    helm install stable/nfs-client-provisioner --name nfs-cp --set nfs.server=${FSADDR} --set nfs.path=/volumes
    watch kubectl get po -l app=nfs-client-provisioner

Press Ctrl-C when the provisioner pod's status changes to Running.

## Make a Persistent Volume Claim

While you can use any application that uses storage classes to do [dynamic provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/)
to test the NFS-Client Provisioner, in this tutorial you will deploy a [PostgreSQL](https://www.postgresql.org/) instance to verify
the configuration.

    helm install --name postgresql --set persistence.storageClass=nfs-client stable/postgresql
    watch kubectl get po -l app=postgresql

Press Ctrl-C when the database pod's status changes to Running.

The PostgreSQL Helm chart creates an 8GB persistent volume claim on Cloud Filestore and mounts it at
`/var/lib/postgresql/data/pgdata` in the database pod.

## Verify Cloud Filestore volume directory creation

To verify that the PostgreSQL database files were actually created on the Cloud Filestore managed storage you will
create a small Compute Engine instance, mount the Cloud Filestore volume on that instance, and inspect the directory
structure to see that the database files are present.

1. Create an `f1-micro` Compute Engine instance

        gcloud compute --project=${PROJECT} instances create check-nfs-provisioner \
            --zone=${ZONE} \
            --machine-type=f1-micro \
            --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
            --image=debian-9-stretch-v20180911 \
            --image-project=debian-cloud \
            --boot-disk-size=10GB \
            --boot-disk-type=pd-standard \
            --boot-disk-device-name=check-nfs-provisioner

2. Install the nfs-common package on check-nfs-provisioner

        gcloud compute ssh check-nfs-provisioner --command "sudo apt update -y && sudo apt install nfs-common -y"

3. Mount the Cloud Filestore volume on check-nfs-provisioner

        gcloud compute ssh check-nfs-provisioner --command "sudo mkdir /mnt/gke-volumes && sudo mount ${FSADDR}:/volumes /mnt/gke-volumes"

4. Display the PostgreSQL database directory structure

        gcloud compute ssh check-nfs-provisioner --command  "sudo find /mnt/gke-volumes -type d"

   You will see output like the following modulo the name of the PostgreSQL pod

        /mnt/gke-volumes
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_twophase
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_notify
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_clog
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_stat_tmp
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_stat
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_serial
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/global
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_commit_ts
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_dynshmem
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_snapshots
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_replslot
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_logical
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_logical/snapshots
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_logical/mappings
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_tblspc
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_subtrans
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/base
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/base/1
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/base/12406
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/base/12407
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_xlog
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_xlog/archive_status
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_multixact
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_multixact/offsets
        /mnt/gke-volumes/default-nfs-postgres-postgresql-pvc-f739e9a1-c032-11e8-9994-42010af00013/postgresql-db/pg_multixact/members


## Clean up

1. Delete the check-nfs-provisioner instance

        gcloud compute instances delete check-nfs-provisioner

2. Delete the Kubernetes Engine cluster

        helm destroy postgresql
        helm destroy nfs-cp
        gcloud container clusters delete ${CLUSTER}

3. Delete the Cloud Filestore instance

        gcloud beta filestore instances delete ${FS} --location ${ZONE}

