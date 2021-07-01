---
title: Deploy Prestashop on Google Kubernetes Engine
description: Deploy Prestashop on Google Kubernetes Engine (GKE) with Cloud SQL and NFS, and scale it horizontally.
author: gabihodoroaga
tags: kubernetes, gke
date_published: 2021-06-29
---

Gabriel Hodoroaga | Software developer | hodo.dev

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

[Prestashop](https://www.prestashop.com/en) is a popular open-source platform for ecommerce.

This tutorial shows you how to deploy Prestashop on Google Kubernetes Engine (GKE) so that it can scale up during peaks and scale down when needed to save 
resources.

This entire tutorial can be completed in the Cloud Shell in the Cloud Console.

The following diagram illustrates the components and interactions that are part of this tutorial:

![Prestashop on GKE](https://storage.googleapis.com/gcp-community/tutorials/prestashop-gke/prestashop-gke.png)

## Objectives

* Create a custom Prestashop Docker image.
* Create a Cloud SQL instance.
* Create a GKE cluster.
* Deploy an NFS server.
* Deploy and scale Prestashop on GKE.
* Use load balancing and Cloud CDN to manage traffic.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Compute Engine](https://cloud.google.com/compute)
*   [Cloud SQL](https://cloud.google.com/sql)
*   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
*   [Cloud Load Balancing](https://cloud.google.com/load-balancing)
*   [Cloud CDN](https://cloud.google.com/cdn) 

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

1.  In the Cloud Console, on the project selector page,
    [select or create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).

    **Note**: If you don't plan to keep the resources that you create in this procedure, create a project instead of selecting
    an existing project. After you finish these steps, you can delete the project, removing all resources associated with 
    the project.

1.  Make sure that billing is enabled for your Google Cloud project.
    [Learn how to confirm that billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project).

1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

1.  Enable the APIs for the services:

        gcloud services enable container.googleapis.com
        gcloud services enable containerregistry.googleapis.com
        gcloud services enable sqladmin.googleapis.com

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community
        
1.  Go to the directory for this tutorial:

        cd community/tutorials/prestashop-gke/

1.  Set environment variables:

        MYSQL_NAME=demo-ps-mysql-2
        MYSQL_ROOT_PASS=admin
        REGION=us-central1
        ZONE=us-central1-a
        CLUSTER_NAME=demo-ps-cluster
        PROJECT_ID=$(gcloud config list project --format='value(core.project)')

## Prepare the Prestashop image

Prestashop uses the file system to make user information like product images and attachments persistent. Prestashop also uses cached templates. These files need
to be shared across all instances.

In this section, you temporarily deploy the official Prestashop Docker image so that you can extract the required files.

### Deploy Prestashop in the Cloud Shell VM

1.  Create a Docker network:
    
        docker network create prestashop-net

1.  Deploy MySQL:

        docker run -ti -p 3307:3306 --network prestashop-net \
          --name some-mysql -e MYSQL_ROOT_PASSWORD=admin -d mysql \
          --character-set-server=utf8 \
          --default-authentication-plugin=mysql_native_password \
          --sql-mode=ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION

    This deployment may take a few seconds to complete.

1.  Create a database:

        docker exec -it some-mysql mysql -u root -p$MYSQL_ROOT_PASS \
          -e "CREATE DATABASE prestashop"
       
1.  Deploy Prestashop:

        docker run -ti --name some-prestashop --network prestashop-net \
          -e DB_SERVER=some-mysql \
          -e PS_DOMAIN=ps.example.com \
          -e PS_INSTALL_AUTO=1 \
          -p 8080:80 -d prestashop/prestashop:latest

### Extract information from the running Docker containers

1.  Back up the database:

        mkdir database
        docker exec some-mysql mysqldump -u root -p$MYSQL_ROOT_PASS \
          prestashop > database/prestashop.sql

1.  Extract the files from the Docker image:

        docker cp some-prestashop:/var/www/html prestashop/
        mv prestashop/html/admin prestashop/html/admin942
        chmod a+rw -R prestashop/html/var 
        mkdir prestashop/nfs
        mv prestashop/html/img prestashop/nfs
        mv prestashop/html/download prestashop/nfs
        mv prestashop/html/cache prestashop/nfs
        mkdir -p prestashop/nfs/themes/classic/cache
        mkdir -p prestashop/nfs/themes/classic/assets/cache
        mkdir -p prestashop/nfs/var/log 
        mkdir prestashop/nfs/config
        mv prestashop/html/config/xml prestashop/nfs/config
        chmod a+rw -R prestashop/nfs

### Create a new Prestashop image

1.  Create a base image for php:7.3-fpm-alpine with Nginx:

        docker build -t php-nginx:7.3-fpm-alpine php-nginx/7.3-fpm-alpine/

1.  Build the new Prestashop image:

        docker build -t mypresta prestashop/

1.  Tag the image:

        docker tag mypresta gcr.io/$PROJECT_ID/mypresta:1.0.1

1.  Push the image to Container Registry:

        docker push gcr.io/$PROJECT_ID/mypresta:1.0.1

## Prepare the database

1.  Create the Cloud SQL instance:

        gcloud sql instances create $MYSQL_NAME  --database-version=MYSQL_8_0 \
          --tier=db-g1-small  --region=$REGION --root-password=admin \
          --database-flags=^+^character-set-server=utf8+default-authentication-plugin=mysql_native_password+sql-mode=ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION

1.  Connect to the Cloud SQL instance using [Cloud SQL Auth proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy):

        cloud_sql_proxy -instances=$PROJECT_ID:$REGION:$MYSQL_NAME=tcp:3306

1.  In a separate Cloud Shell terminal, run the following commands create the database:

        MYSQL_ROOT_PASS=admin

        cd gke-prestashop-deployment

        mysql -u root -p$MYSQL_ROOT_PASS -h 127.0.0.1 \
          -e "CREATE DATABASE prestashop;"

        mysql -u root -p$MYSQL_ROOT_PASS -h 127.0.0.1 \
          prestashop < database/prestashop.sql

1.  Return to initial the Cloud Shell terminal and press `Ctrl+C` to stop the `cloud_sql_proxy` process.

## Create the GKE cluster

1.  Create the cluster:

        gcloud container clusters create $CLUSTER_NAME \
          --zone $ZONE --machine-type "e2-medium" \
          --enable-ip-alias \
          --num-nodes=3 --scopes=gke-default,sql-admin
 
    To allow access from the Compute Engine VM to the Cloud SQL API, this command adds a special scope, `sql-admin`.

## Deploy the NFS server and copy files

1.  Deploy the NFS server for persistent user data and cached templates:

    1.  Create a persistent disk:

            gcloud compute disks create nfs-pv-disk --size=10GB \
              --type=pd-ssd --zone=$ZONE

    1.  Create a persistent volume:

            kubectl apply -f gke/nfs/nfs-persistent-volume.yaml

    1.  Create a persistent volume claim:

            kubectl apply -f gke/nfs/nfs-persistent-volume-claim.yaml

    1.  Create the deployment:

            kubectl apply -f gke/nfs/nfs-deployment.yaml

    1.  Expose the deployment service:

            kubectl apply -f gke/nfs/nfs-service.yaml

1.  Set up the NFS volume, mount it to the Cloud Shell VM, and copy the files:

    1.  Set variables with configuration information:

            NFS_NODE_PORT=$(kubectl get service service-nfs \
              -o jsonpath='{.spec.ports[?(@.name=="nfs")].nodePort}')
            NFS_NODE_ADDRESS=$(kubectl get nodes \
              -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
            GKE_NETWORK_TAG=$(gcloud compute instances describe $(kubectl get nodes \
              -o jsonpath='{.items[0].metadata.name}') --zone=$ZONE \
              --format="value(tags.items[0])")
            SHELL_IP_ADDRESS=$(curl http://ifconfig.me)
        
    1.  Update the firewall to temporarily allow access for the copying of the files:

            gcloud compute firewall-rules create ps-demo-nfs \
              --direction=INGRESS --priority=1000 --network=default \
              --action=ALLOW --rules=tcp:$NFS_NODE_PORT \
              --source-ranges=$SHELL_IP_ADDRESS \
              --target-tags=$GKE_NETWORK_TAG

    1.  Set up the directories and mount the volume:

            sudo mkdir -p /mnt/nfs/ps
            sudo chmod a+rw /mnt/nfs/ps
            sudo apt-get -y install nfs-common
            sudo mount -t nfs4 -o port=$NFS_NODE_PORT $NFS_NODE_ADDRESS:/ /mnt/nfs/ps
            sudo mkdir /mnt/nfs/ps/psdata
            
    1.  Copy the files and set permissions for them:

            sudo cp -r prestashop/nfs/* /mnt/nfs/ps/psdata
            sudo chmod a+rw -R /mnt/nfs/ps/psdata

1.  Unmount the volume and remove the temporary firewall rules:

        sudo umount /mnt/nfs/ps

        gcloud -q compute firewall-rules delete ps-demo-nfs

## Create the service account and Kubernetes secrets

To connect from GKE to Cloud SQL, you use Cloud SQL Auth proxy deployed as a sidecar to your Prestashop deployment.

The steps in this section are based on [Connecting from Google Kubernetes Engine](https://cloud.google.com/sql/docs/mysql/connect-kubernetes-engine).

1.  Create the service account:

        gcloud iam service-accounts create ps-mysql-user-2 \
          --description="A service account to access mysql" \
          --display-name="ps-mysql-user-2"

1.  Get the service account email address:

        SQL_SERVICE_ACCOUNT=$(gcloud iam service-accounts list --format="value(email)" --filter="displayName=ps-mysql-user-2")

1.  Add the required roles:

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
          --member=serviceAccount:${SQL_SERVICE_ACCOUNT} \
          --role=roles/cloudsql.client

1.  Create the service account key:

        gcloud iam service-accounts keys create gke/presta/key.json \
          --iam-account ${SQL_SERVICE_ACCOUNT}

1.  Save the key as a Kubernetes secret:

        kubectl create secret generic ps-mysql-credentials \
          --from-file=service_account.json=gke/presta/key.json

1.  Save the root password as a Kubernetes secret:

        kubectl create secret generic mysql-pass \
          --from-literal=password=$MYSQL_ROOT_PASS

## Deploy the Prestashop application

In this section, you create the persistent volume and the persistent volume claim that connects to the NFS server, and you use it to map folders inside the 
Prestashop container. The backend configuration is required here in order to enable Cloud CDN.

1.  Create the persistent volume:

        kubectl apply -f gke/presta/ps-persistent-volume.yaml

1.  Create the persistent volume claim:

        kubectl apply -f gke/presta/ps-persistent-volume-claim.yaml

1.  Export the instance name and project ID as environment variables:

        export INSTANCE_CONNECTION_NAME=$PROJECT_ID:$REGION:$MYSQL_NAME
        export PROJECT_ID=$PROJECT_ID

1.  Create the deployment:

        cat gke/presta/ps-deployment.yaml | envsubst | kubectl apply -f -

1.  Create the service and the backend configuration:

        kubectl apply -f gke/presta/ps-backend-config.yaml
        kubectl apply -f gke/presta/ps-service.yaml

## Create and test the GKE Ingress controller

In GKE, the Ingress object defines rules for routing HTTP(S) traffic to applications running in a cluster. For details, see
[GKE Ingress for HTTP(S) Load Balancing](https://cloud.google.com/kubernetes-engine/docs/concepts/ingress).

1.  Create the GKE Ingress controller:

        kubectl apply -f gke/ingress/ps-ingress.yaml

    It might take a few minutes for the controller to create the backend services and the load balancer.

1.  Get the external IP address of the GKE Ingress controller:

        IP_ADDRESS=$(kubectl get ingress ingress-psweb \
          -o jsonpath='{.status.loadBalancer.ingress[0].ip}') \
          && echo $IP_ADDRESS

1.  Test it using `curl`:

        curl --head http://ps.example.com/ \
          --resolve ps.example.com:80:$IP_ADDRESS

    The output should be similar to the following:

        HTTP/1.1 200 OK
        Server: nginx
        Date: Tue, 25 May 2021 12:36:49 GMT
        Content-Type: text/html; charset=utf-8
        Vary: Accept-Encoding
        X-Powered-By: PHP/7.3.28
        Expires: Thu, 19 Nov 1981 08:52:00 GMT
        Cache-Control: no-store, no-cache, must-revalidate
        Pragma: no-cache
        X-Backend-Server: server-psweb-79df96f6f5-abc
        Via: 1.1 google
        Transfer-Encoding: chunked

    If you run the command multiple times, you should be able to see that the header value `X-Backend-Server` changes, which means that multiple backends are 
    serving the request.

If you set up your `/etc/hosts` file to point to `ps.example.com`, you can view the online shop in your browser. For the admin page, you must access
`ps.example.com/admin942`, and the user is `demo@prestashop.com` with password `prestashop_demo`.


## Cleaning up

1.  To remove all of the resources, you can either delete the project or run these cleanup commands:

    ```bash
    # delete the cluster 
    gcloud -q container clusters delete $CLUSTER_NAME --zone=$ZONE

    # delete the SQL instance
    gcloud -q sql instances delete $MYSQL_NAME

    # delete the service account
    gcloud -q iam service-accounts delete $SQL_SERVICE_ACCOUNT

    # delete the disk
    gcloud -q compute disks delete nfs-pv-disk --zone=$ZONE

    # delete Container Registry images
    gcloud -q container images delete gcr.io/$PROJECT_ID/mypresta:1.0.1
    ```

## What's next

- Learn more about [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine).
- Learn more about [Cloud SQL](https://cloud.google.com/sql).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
