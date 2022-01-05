---
title: Deploy Yolo model to K3 with Cloud Build and ACM
description: Learn how to deploy cloud trained AI models to edge servers.
author: kalschi
tags: AI, artificial intelligence, Edge AI, K3s
date_published: 2021-01-03
---

Michael Chi | Cloud Solution Architect | Google

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using Cloud Build to deploy inferencing models from Google Cloud Platform to edge servers running K3s. It is intended for developers and IT administrators who require cloud computing for training and evaluating machine learning models and need to run predictions on-premises.

In this tutorial, you learn how to trigger [Cloud Build](https://cloud.google.com/build) pipeline to build container images and leverage [Anthos Configuration Management](https://cloud.google.com/anthos/config-management) and Cloud Build to deploy the container image to an edge server running the lightweight open-source Kubernetes distribution [K3s](https://k3s.io/). To simulate an edge server, you create a GCE VM in GCP project.

This tutorial is based on the [YOLOv5 sample](https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch) created by [mikel-brostrom](https://github.com/mikel-brostrom), and [Deep Source Pytorch](https://github.com/ZQPei/deep_sort_pytorch.git) created by [ZQPei](https://github.com/ZQPei) as the application to be deployed. To permit running in containerized environments without displays, a new [track\_container.py](./yolov5-python/track_container.py) was created based on the original [track.py](https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch/blob/master/track.py).


### 
**Objectives**



*   Create a GCE VM and set up K3s
*   Enable and register K3s to Anthos
*   Set up Source Repo and push codes
*   Set up Cloud Build Pipeline
*   Set up Anthos ACM
*   Trigger automated deployment

### 
**Costs**


This tutorial uses billable components of Google Cloud, including the following:



*   [Anthos](https://cloud.google.com/anthos/pricing)
*   [Compute Engine](https://cloud.google.com/compute/all-pricing)
*   [Source Repository](https://cloud.google.com/source-repositories/pricing)
*   [Cloud Build](https://cloud.google.com/build/pricing)
*   [Artifact Registry](https://cloud.google.com/artifact-registry/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.


### 
**Before you begin**

This tutorial has the prerequisites below.



*   A billing enabled Google Cloud account, see this [document](https://cloud.google.com/billing/docs/how-to/modify-project) for detailed instructions.
*   Docker must be install in your environment or cloud shell, see this [instruction](https://docs.docker.com/engine/install/ubuntu/) for details

### 
**Architecture**


![Architecture](architecture-diagram.png "Architecture")



### 
**Tutorial**


#### 
Logging into Cloud Shell and create a new GCP project 


```
export PROJECT_ID=<YOUR PROJECT ID>
gcloud projects create $PROJECT_ID

gcloud config set project $PROJECT_ID
```



#### 
Create Service Account

Create a service account for K3s to interact with Google Cloud Platform


```
export SERVICE_ACCT_NAME=edge-demo
gcloud iam service-accounts create $SERVICE_ACCT_NAME
```



#### Grant yourself permission to impersonate the service account.


```
    export USER=<YOUR GOOGLE ACCOUNT>

    gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
    --member=user:$USER --role=roles/iam.serviceAccountUser
```


To use a specific service account for Cloud Build, you need to specify where to store build logs. In this tutorial, you will use Cloud Logging. To allow sending logs to Cloud Logging, grant the Logs Writer (`roles/logging.logWriter`) role to the service account


```
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member=serviceAccount:$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
          --role=roles/logging.logWriter
```



#### 
Enable required services

List available billing accounts and enable billing for the project.


```
gcloud beta billing accounts list
gcloud beta billing projects link $GOOGLE_CLOUD_PROJECT --billing-account <BILLING ACCOUNT ID>
```


Run the commands below in Cloud Shell.


```
 gcloud services enable --project=$GOOGLE_CLOUD_PROJECT  \
                connectgateway.googleapis.com \
                anthos.googleapis.com \
                gkeconnect.googleapis.com \
                gkehub.googleapis.com \
                cloudresourcemanager.googleapis.com \
                anthosconfigmanagement.googleapis.com \
                sourcerepo.googleapis.com \
                cloudbuild.googleapis.com \
                artifactregistry.googleapis.com
```



#### Create a Source Repository and Artifacts Repository


```
 	export REPO_NAME=edge-demo
	export ARTIFACTS_REPO_NAME=edge-deployment-demo

gcloud source repos create $REPO_NAME
  	gcloud artifacts repositories create $ARTIFACTS_REPO_NAME --repository-format=docker \
        --location=us-central1 
```


`  `Grant service account permissions to read/write artifacts to Artifacts Repository and permissions to read/push codes to Source Repository.


```
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

	export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
        --role=roles/source.reader

  	gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
        --role=roles/source.writer

  	gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
        --role=roles/artifactregistry.reader

  	gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
        --role=roles/artifactregistry.writer
```



#### 
**Create GCE Instance to act as edge server**

Run the commands below in Cloud Shell to create a GCE virtual machine in the zone `us-central1-a`:


```
   export ZONE=us-central1-a
```


List available Ubuntu images 


```
gcloud compute images list --filter=ubuntu --format="value(NAME)"
```


Replace {image} with a current Ubuntu image name.


```
    	export OS_IMAGE=<Ubuntu Image Name>
gcloud compute instances create edge-server-k3s --project=$GOOGLE_CLOUD_PROJECT \
--zone=$ZONE --machine-type=e2-standard-4 \
--network-interface=network-tier=PREMIUM,subnet=default \
--scopes=https://www.googleapis.com/auth/cloud-platform \
--create-disk=auto-delete=no,boot=yes,device-name=k3s,image=projects/ubuntu-os-cloud/global/images/$OS_IMAGE,size=100
```


SSH to the compute engine instance once it's up and running.


```
gcloud compute ssh edge-server-k3s --zone $ZONE
```



#### 
**Install K3s**

SSH to the newly created machine and follow the Rancher [instruction](https://rancher.com/docs/k3s/latest/en/installation/install-options/#options-for-installation-with-script)s to install K3s on the newly created machine.


```
   curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
```


Once k3s installation is complete, you will see the following output:.


```
[INFO]  systemd: Starting k3s
```



#### 
**Authenticate to Artifacts Registry**

Use Service Account Key to allow our edge server to pull images from Artifacts Registry.

In the GCE instance hosting k3s, run the commands below


```
 export SECRETNAME=ar-json-key
 export GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
 export SERVICE_ACCOUNT=edge-demo

 gcloud iam service-accounts keys create ar-key.json --iam-account $SERVICE_ACCOUNT@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com

  kubectl create secret docker-registry $SECRETNAME --docker-server=us-central1-docker.pkg.dev --docker-username=_json_key \
--docker-email=$SERVICE_ACCOUNT@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com --docker-password="$(cat ar-key.json)"
```



#### 
**Register attached K3s cluster to Anthos**

In GCE VM, run the commands below to register K3s to Anthos.


```
    export MEMBERSHIP_NAME=edge-server-k3s
    export KUBECONFIG_CONTEXT=$(sudo kubectl config current-context)
    export KUBECONFIG_PATH=/etc/rancher/k3s/k3s.yaml

    sudo gcloud container hub memberships register $MEMBERSHIP_NAME \
    --context=$KUBECONFIG_CONTEXT \
    --kubeconfig=$KUBECONFIG_PATH \
    --enable-workload-identity \
    --has-private-issuer
```


Note that there is a known bug that you get an error message at first time, the error goes away on retry. Please re-run the command when you see below error message.

ERROR: (gcloud.container.hub.memberships.register) Membership CRD creation failed to complete: error: unable to recognize "STDIN": no matches for kind "CustomResourceDefinition" in version "apiextensions.k8s.io/v1beta1”


#### 
**Set up Connect Gateway**

Go back to Cloud Shell and grant yourself required IAM roles so you can interact with connected cluster through the gateway.


```
export MEMBER=user:your-user-name@your-domain.com
export GATEWAY_ROLE=roles/gkehub.gatewayAdmin

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member $MEMBER \
--role $GATEWAY_ROLE

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member $MEMBER \
--role roles/gkehub.viewer

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member $MEMBER \
--role roles/container.viewer

export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
```


`export MEMBER=serviceAccount:$PROJECT_NUMBER`@cloudbuild.gserviceaccount.com


```
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member $MEMBER \
--role $GATEWAY_ROLE

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member $MEMBER \
--role roles/gkehub.viewer

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
--member $MEMBER \
--role roles/container.viewer
```


To authenticate requests to the cluster's Kubernetes API server initiated by specific Google Identity users coming from the gateway, SSH to K3s machine and update required RBAC policies in K3s cluster.



*   The impersonation policy authorizes the Connect agent to send requests to the Kubernetes API server on behalf of a user.
    *   Replace `$USER` with your user account.
    *   Replace `your-service-account@example-project.iam.gserviceaccount.com` with the service account created earlier.
    *   Cloud build uses GCP managed Service Account `project-number@cloudbuild.gserviceaccount.com`.


```
gcloud compute ssh edge-server-k3s --zone $ZONE
export USER=<USER-NAME@YOUR-DOMAIN>
export SERVICE_ACCT_NAME=edge-demo
export GOOGLE_PROJECT_ID=<YOUR PROJECT ID>
export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_PROJECT_ID --format="value(projectNumber)")

cat <<EOF > /tmp/impersonate.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gateway-impersonate
rules:
- apiGroups:
  - ""
  resourceNames:
  - $USER
  - $SERVICE_ACCT_NAME@$GOOGLE_PROJECT_ID.iam.gserviceaccount.com
  - $PROJECT_NUMBER@cloudbuild.gserviceaccount.com
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


The policy that specifies which permissions the user has on the cluster.


```
export USER=<USER-NAME@YOUR-DOMAIN>
export SERVICE_ACCT_NAME=edge-demo
export GOOGLE_PROJECT_ID=<YOUR PROJECT ID>
export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_PROJECT_ID --format="value(projectNumber)")

cat <<EOF > /tmp/admin-permission.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-cluster-admin
subjects:
- kind: User
  name: $USER
- kind: User
  name: $SERVICE_ACCT_NAME@$GOOGLE_PROJECT_ID.iam.gserviceaccount.com
- kind: User
  name: $PROJECT_NUMBER@cloudbuild.gserviceaccount.com
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
EOF
kubectl apply -f /tmp/admin-permission.yaml
```


Now browse to the Anthos Cluster console at https://console.cloud.google.com/anthos/clusters, select the `edge-server-k3s` and click `Login` button then choose `Use your Google identity to log-in`.


#### 
**Verify connection to K3s**

Once registered, you'll see a new entry shown in Anthos console, however, to access the registered cluster, you'll need to [log in and authenticate to the cluster](https://cloud.google.com/anthos/multicluster-management/console/logging-in). Per best practice, you will use Google Cloud Identity to login to the cluster.

Exit the VM and return to Cloud Shell.  Connect to remote K3s cluster from GCP by running the command below:


```
 gcloud container hub memberships get-credentials edge-server-k3s
```


This generates kubeconfig entry for K3s cluster and set as default context.  Verify the connectivity:


```
 kubectl get nodes
```


The node name should be `edge-server-k3s` as specified earlier


```
 NAME              STATUS   ROLES                  AGE    VERSION
  edge-server-k3s   Ready    control-plane,master   112m   v1.21.7+k3s1
```


The required infrastructure is now ready and you can start to deploy applications.


#### 
**Create Dockerfile**

Clone git repository.


```
	git clone https://github.com/GoogleCloudPlatform/community.git
	cd ./community/tutorials/k3s-anthos-edge-ai/yolov5-python
```


The repo contains [Dockerfile](yolov5-python/Dockerfile) ,[go.sh](yolov5-python/go.sh), [cloudbuild.yaml](yolov5-python/cloudbuild.yaml), [track\_container.py](yolov5-python/track_container.py) and [Dockerfile.](yolov5-python/Dockerfile)

The Dockerfile clones the Yolo git repository, installs required dependencies and runs [go.sh](./yolov5-python/go.sh) to launch the application.

The application takes a RTSPrtsp video stream as inputs and writes the results to a local folder. You create a volume claim to store these results in [Deployment-k3s.yaml](http://./yolov5-python/Deployment-k3s.yaml)

The Deployment-k3s.yaml has #PROJECT\_ID# and #BUILD# as placeholders for actual project IDid and build IDid, whichthey are filled in by the Cloud Build pipelines.


```
…

    spec:
      volumes:
      - name: output
        hostPath:
          path: /tmp
      containers:
      - name: yolo
        image: us-central1-docker.pkg.dev/#PROJECT_ID#/edge-deployment-demo/edge-ai:#BUILD#
        env:
        - name: SOURCE
          value: rtsp://<YOUR RTSP SOURCE>
        - name: OUTPUT
          value: "/app/output/"          
        volumeMounts:
        - name: output
          mountPath: /app/output
      imagePullSecrets:
      - name: ar-json-key
```


`I`n the cloudbuild.yaml, we replace placeholders #BUILD# and #PROJECT\_ID# with actual project id and build id.

Run the commands below to create a Cloud Build trigger


```
gcloud beta builds triggers create cloud-source-repositories --name="edge-deployment-trigger" \
    --service-account="projects/$GOOGLE_CLOUD_PROJECT/serviceAccounts/$SERVICE_ACCT_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --repo=edge-demo --branch-pattern=".*" --inline-config="cloudbuild.yaml"
```



#### 
**Trigger deployment**

To trigger automatic deployment, you can submit the job to Cloud Build


```
gcloud builds submit --config cloudbuild.yaml
Wait till the build succeeds, go to Cloud Shell and run commands below to verify if the container is up and running.
gcloud container hub memberships get-credentials edge-server-k3s
kubectl get pods

You may see errors saying Pull Image failed, wait several minutes for the container to retry then check logs.
kubectl logs <POD ID>

You should see something similar.
    No detections
    0: 448x640 1 sheep, 1 orange, Done. YOLO:(80.475s), DeepSort:(0.039s)
    0: 448x640 1 sheep, 1 orange, Done. YOLO:(81.111s), DeepSort:(0.039s)
```


Wait till the build is completed successfully, now you can push codes to Source Repository.

To access to Source Repository, first generate a SSH key and [add the SSH key to the repository](https://source.cloud.google.com/user/ssh_keys?register=true), then commit and push codes


```
    git init
    git remote add google ssh://$USER@source.developers.google.com:2022/p/$PROJECT_ID/r/$REPO_NAME
    git add .
    git commit -m "init"
    git push --all google
```


Wait till the build succeeds, go to Cloud Shell and run commands below to verify if the container is up and running.


```
gcloud container hub memberships get-credentials edge-server-k3s
kubectl get pods
```


You may see errors saying Pull Image failed, wait several minutes for the container to retry then check logs.


```
kubectl logs <POD ID>
```


You should see something similar.


```
    No detections
    0: 448x640 1 sheep, 1 orange, Done. YOLO:(80.475s), DeepSort:(0.039s)
    0: 448x640 1 sheep, 1 orange, Done. YOLO:(81.111s), DeepSort:(0.039s)
```



### 
**Cleaning up**

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:



*   If you used an existing project, you'll also delete any other work that you've done in the project.
*   You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an `appspot.com` URL, remain available.

To delete a project, do the following:



1. In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2. In the project list, select the project you want to delete and click Delete.
3. In the dialog, type the project ID, and then click Shut down to delete the project.

### 
**What's next**

*   [Introduction to Anthos Config Management](https://cloud.google.com/anthos/config-management)
*   [Introduction to Cloud Build](https://cloud.google.com/build)
*   [Cloud Build configuration file schema](https://cloud.google.com/build/docs/build-config-file-schema)