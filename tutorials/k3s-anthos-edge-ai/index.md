---
title: Edge AI with Anthos and K3S
description: Learn how to deploy cloud trained AI models to edge servers
author: kalschi
tags: AI, artificial intelligence, Edge AI, K3
date_published: 
---

Michael Chi | Cloud Solution Architect | Google

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using Cloud Build to deploy inferencing models from Google Cloud Platform to edge servers running K3s.

In this turtorial, you learn how to trigger Cloud Build pipeline to build contianer images and leverage Anthos Configuration Management service to deploy it to an edge server running K3s. To simulate edge server, you create a GCE VM in GCP project.

This turtrial uses a popular [YOLOv5 sample](https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch) created by [mikel-brostrom](https://github.com/mikel-brostrom) as the workload to be deployed. 


## Objectives

- Create a GCE VM and setup K3s
- Enable and register newly created K3s to Anthos
- Setup Source Repo and push sample codes
- Setup Cloud Build Pipeline
- Setup Anthos ACM
- Update codes and trigger automated deployment

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Anthos](https://cloud.google.com/anthos/pricing)
*   [Compute Engine](https://cloud.google.com/compute/all-pricing)
*   [Source Repository](https://cloud.google.com/source-repositories/pricing)
*   [Cloud Build](https://cloud.google.com/build/pricing)
*   [Artifact Registry](https://cloud.google.com/artifact-registry/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

This tutorial has below prerequisites 

- A billing enabled Google Cloud account, see this [document](https://cloud.google.com/billing/docs/how-to/modify-project) for detailed instructions.
- gcloud command line tool must be [installed]((https://cloud.google.com/anthos/multicluster-management/connect/prerequisites#install-cloud-sdk)) in your environment if not using Cloud shell.
- Docker must be install in your working environment or cloud shell, see this [instruction](https://docs.docker.com/engine/install/ubuntu/) for details

## Enable required ervices

Run below commands in cloud shell

      gcloud services enable --project=$GOOGLE_CLOUD_PROJECT  \
                    connectgateway.googleapis.com \
                    anthos.googleapis.com \
                    gkeconnect.googleapis.com \
                    gkehub.googleapis.com \
                    cloudresourcemanager.googleapis.com
      gcloud services enable anthosconfigmanagement.googleapis.com
      gcloud services enable sourcerepo.googleapis.com
      gcloud services enable cloudbuild.googleapis.com
      gcloud services enable artifactregistry.googleapis.com

      gcloud source repos create edge-demo
      gcloud artifacts repositories create edge-deployment-demo --repository-format=docker \
            --location=us-central1 

      gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
            --member=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
            --role=roles/source.reader

      gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
            --member=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
            --role=roles/source.writer

      gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
            --member=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
            --role=roles/artifactregistry.reader

      gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
            --member=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
            --role=roles/artifactregistry.writer

            

## Create Servive Account

In this tutorial we use a specifc service account for building images and deploying to edge servers.

    export SERVICE_ACCT_NAME=edge-demo
    gcloud iam service-accounts create $SERVICE_ACCT_NAME

We need grant user permission to impersonate the service account, first dump current configuration

    gcloud iam service-accounts get-iam-policy $SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
        --format=json > policy.json

Then, update the `policy.json` file to grant permission to principles 


            {
              "bindings": [
                {
                  "role": "roles/iam.serviceAccountUser",
                  "members": [
                    "user:your-account-name@your-domain-name.com"
                  ]
                },
              ],
              "etag": "BwUqLaVeua8=",
              "version": 1
            }

Save the file and set IAM policy

    gcloud iam service-accounts set-iam-policy $SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com ./policy.yaml


To use a service account to run Cloud Build, we also need to specify where to store build logs, in this tutorial we will be using Cloud Logging. To allow storing logs to Cloud Logging, Logs Writer (`roles/logging.logWriter`) role must be granted to the service account

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
          --member=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
          --role=roles/logging.logWriter

## Setup edge server

### Create GCE Instance

Run below command in Cloud Shell to create a GCE virtual machine in `us-central1-a` zone:
    

        export ZONE=us-central1-a

        gcloud compute instances create edge-server-k3s --project=$GOOGLE_CLOUD_PROJECT --zone=$ZONE \
            --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default \
            --scopes=https://www.googleapis.com/auth/cloud-platform \
            --create-disk=auto-delete=no,boot=yes,device-name=k3s,image=projects/debian-cloud/global/images/debian-10-buster-v20211105,size=100

Wait for the compute engine instance to be created and ssh to it.


### Install K3s

SSH to the newly creeated machine and follow the Rancher [instruction](https://rancher.com/docs/k3s/latest/en/installation/install-options/#options-for-installation-with-script) to install K3s on the newly created machine

        curl -sfL https://get.k3s.io | sh -

If everything goes well, you should see outputs stating K3s is starting.


```
[INFO]  systemd: Starting k3s
```

### Authenticate to Artifacts Registry

Use Service Account Key to allow our edge server to pull images from Artifacts Registry. 

In K3S, run below commands

      export SECRETNAME=ar-json-key
      export GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
      export SERVICE_ACCOUNT=edge-demo

      gcloud iam service-accounts keys create ar-key.json --iam-account $SERVICE_ACCOUNT@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com

      kubectl create secret docker-registry $SECRETNAME --docker-server=us-central1-docker.pkg.dev --docker-username=_json_key \
            --docker-email=$SERVICE_ACCOUNT@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com --docker-password="$(cat ar-key.json)"

Configure `imagePullSecret` to default service account, run

      sudo kubectl edit serviceaccount default --namespace default


Then edit the configuration file, add `imagePullSecret`

      apiVersion: v1
      kind: ServiceAccount
      metadata:
        name: default
        namespace: default
        ...
      secrets:
      - name: default-token-zd84v
      # The secret you created:
      imagePullSecrets:
      - name: ar-json-key

Press `:` then `wq`


## Register K3s cluster to Anthos

### Register attached K3s cluster to Anthos

Follow the [instruction](https://cloud.google.com/anthos/docs/setup/attached-clusters#register_your_cluster) to register K3s cluster to Anthos.

    export MEMBERSHIP_NAME=edge-server-k3s
    export KUBECONFIG_CONTEXT=$(sudo kubectl config current-context)
    export KUBECONFIG_PATH=/etc/rancher/k3s/k3s.yaml #Kubectl config file in K3s defaults to `/etc/rancher/k3s`

    sudo gcloud container hub memberships register $MEMBERSHIP_NAME \
    --context=$KUBECONFIG_CONTEXT \
    --kubeconfig=$KUBECONFIG_PATH \
    --enable-workload-identity \
    --has-private-issuer

Once registered, it appears in Anthos clusters console, however, to access to the registered cluster, you'll need to [log in and authenticate to the cluster](https://cloud.google.com/anthos/multicluster-management/console/logging-in). As the document recommended, we'll use Google Cloud Identity to login to the cluster.

### Setup Connect Gateway

Your platform admin must perform the necessary [setup](https://cloud.google.com/anthos/multicluster-management/gateway/setup) to let you use your Google Cloud identity to log in, including granting you all the necessary roles and RBAC permissions to view and authenticate to registered clusters.

Now we want to grant required IAM roles to users so they can interact with connected cluster through the gateway.

    export MEMBER=user:your-user-name@your-domain.com
    export GATEWAY_ROLE=roles/gkehub.gatewayAdmin   # or `roles/gkehub.gatewayReader`

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role $GATEWAY_ROLE

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role roles/gkehub.viewer

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role roles/container.viewer

    export MEMBER=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com
    export GATEWAY_ROLE=roles/gkehub.gatewayAdmin   # or `roles/gkehub.gatewayReader`

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role $GATEWAY_ROLE

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role roles/gkehub.viewer

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role roles/container.viewer


To authenticate requests to the cluster's Kubernetes API server initiated by specific Google Identity users coming from the gateway, SSH to K3s machine and update required RBAC policies in K3s cluster.

- The impersonation policy that authorizes the Connect agent to send requests to the Kubernetes API server on behalf of a user. 
    - Replace `your-user-name@your-domain.com` with your user account.
    - Replace `your-service-account@example-project.iam.gserviceaccount.com` with the service account created earlier. 
    - Cloud build uses GCP managed Service Account `project-number@@cloudbuild.gserviceaccount.com`. replace `project-number` with your project number

```bash
cat <<EOF > /tmp/impersonate.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gateway-impersonate
rules:
- apiGroups:
  - ""
  resourceNames:
  - your-user-name@your-domain.com
  - your-service-account@example-project.iam.gserviceaccount.com
  - project-number@@cloudbuild.gserviceaccount.com
  resources:
  - users
  verbs:
  - impersonate
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-impersonate
roleRef:
  kind: ClusterRole
  name: gateway-impersonate
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: connect-agent-sa
  namespace: gke-connect
EOF
kubectl apply -f /tmp/impersonate.yaml
```

- The policy that specifies which permissions the user has on the cluster. 
  - Replace `your-user-name@your-domain.com` with your user account
  - Replace `your-service-account@example-project.iam.gserviceaccount.com` with the service account created earlier. 
  - Cloud build uses GCP managed Service Account `project-number@@cloudbuild.gserviceaccount.com`. replace `project-number` with your project number

```bash
cat <<EOF > /tmp/admin-permission.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-cluster-admin
subjects:
- kind: User
  name: your-user-name@your-domain.com
- kind: User
  name: your-service-account@example-project.iam.gserviceaccount.com
- kind: User
  name: project-number@@cloudbuild.gserviceaccount.com
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
EOF
kubectl apply -f /tmp/admin-permission.yaml
```

Noq go to Anthos Cluster console, select the `edge-server-k3s` cluster then click `Login` button, when popup prompts, choose `Use your Google identity to log-in`



### Verify connection to K3s

Go to cloud shell, now we should be able to connect to remote K3s cluster from GCP by running below command

      gcloud container hub memberships get-credentials edge-server-k3s

This generates kubeconfig entry for K3s cluster and set as default context, you can verify this by:

      kubectl get nodes

The node name should be `edge-server-k3s` as we specified

      NAME              STATUS   ROLES                  AGE    VERSION
      edge-server-k3s   Ready    control-plane,master   112m   v1.21.7+k3s1



## Setup Cloud Build pipeline and trigger

At this point we have required infrastructure ready, now we want to get our applications ready to deploy

### Clone sample application and setup Source Repository

In cloud shell or your working environment of choice, clone the sample application from github

      git clone --recurse-submodules https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch.git
      cd Yolov5_DeepSort_Pytorch
      git remote add google ssh://you-user-name@source.developers.google.com:2022/p/$GOOGLE_CLOUD_PROJECT/r/edge-demo

To pudh codes to Source Repo, generate a SSH key and [add the SSH key to the repository](https://source.cloud.google.com/user/ssh_keys?register=true) then do a `git push --all google` to push codes for the first time.

The codes should work just fine in container environment, to make our workload more flexible for differnet requirements, we add a [go.sh](./yolov5-python/go.sh) which takes environment variables as arguments to run the python codes. Also we add a [Dockerfile](./yolov5-python/Dockerfile) to create container image.

Create a [cloudbuild.yaml](./cloudbuild/cloudbuild.yaml) and submit the job to Cloud Build

    gcloud builds submit --config cloudbuild.yaml


Note that since we will be running Cloud Build trigger under a service account, in the `cloudbuild.yaml`, we specify logging location to `CLOUD_LOGGING_ONLY`.

Also, you can change build timeout by specifying `timeout` in the yaml file.

      steps:
      - name: 'gcr.io/cloud-builders/docker'
        args: [ 'build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/edge-deployment-demo/edge-ai:001', '.' ]
      timeout: 1200s
      optios:
        logging: CLOUD_LOGGING_ONLY
      images:
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/edge-deployment-demo/edge-ai:001'

### Create a Source Repo trigger

Our pipeline monitors Source Repository pushes, when new codes are pushed to the repo, Cloud Build automatically fetch latest codes and start CI/CD flow.


    gcloud beta builds triggers create cloud-source-repositories --name="edge-deployment-trigger" \
        --service-account="projects/$GOOGLE_CLOUD_PROJECT/serviceAccounts/$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
        --repo=edge-demo --branch-pattern=".*" --inline-config="cloudbuild.yaml"



cloudbuild.yaml contains required steps to build docker image and push to edge server

      steps:
        - name: gcr.io/cloud-builders/docker
          args:
            - build
            - '-t'
            - >-
              us-central1-docker.pkg.dev/$PROJECT_ID/edge-deployment-demo/edge-ai:$BUILD_ID
            - .
          id: build.image
        - name: gcr.io/cloud-builders/gcloud
          args:
            - '-c'
            - |
              set -x
              gcloud container hub memberships get-credentials edge-server-k3s
              sed -i 's/#BUILD#/$BUILD_ID/g' Deployment-k3s.yaml
              sed -i 's/#PROJECT_ID#/$PROJECT_ID/g' Deployment-k3s.yaml
              kubectl apply -f Deployment-k3s.yaml
          entrypoint: /bin/sh
      timeout: 1200s
      images:
        - >-
          us-central1-docker.pkg.dev/$PROJECT_ID/edge-deployment-demo/edge-ai:$BUILD_ID
      options:
        logging: CLOUD_LOGGING_ONLY

## Cleaning up

Tell the reader how to shut down what they built to avoid incurring further costs.

### Example: Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

Tell the reader what they should read or watch next if they're interested in learning more.

### Example: What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).