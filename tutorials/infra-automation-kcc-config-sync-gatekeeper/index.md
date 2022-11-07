---
title: Infrastructure automation with Config Connector, Config Sync, and OPA Gatekeeper
description: An end-to-end workflow for provisioning and managing Google Cloud resources using Config Connector, Config Sync, and Gatekeeper.
author: nardosm
tags: kubernetes, kcc, gitops
date_published: 2021-07-21
---

Nardos Megersa | Strategic Cloud Engineer | Google 

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial walks you through a GitOps end-to-end workflow for provisioning and managing Google Cloud resources using the following tools:

* [**Config Connector**](https://cloud.google.com/config-connector/docs/overview) to manage Google Cloud infrastructure
* [**Config Sync**](https://cloud.google.com/kubernetes-engine/docs/add-on/config-sync/config-sync-overview) to synchronize declarative Config Connector 
  infrastructure configurations from a Git repository
* [**OPA Gatekeeper**](https://github.com/open-policy-agent/gatekeeper) to create and enforce constraint policies for Google Cloud

## Before you begin

This tutorial assumes that you already have a [Google Cloud account](https://console.cloud.google.com/freetrial). 

1. Make sure that your [`gcloud` components are up to date](https://cloud.google.com/sdk/docs/components#updating_components).

1. Create three Google Cloud projects:

    * Host project to contain the Google Kubernetes Engine cluster
    * Development (dev) project to contain Google Cloud resources
    * Production (prod) project to contain Google Cloud resources

1. Ensure that [billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project) for all three projects. 

## Objectives

* Deploy a Google Kubernetes Engine cluster that runs Config Connector, Config Sync, and Gatekeeper.
* Use a source code repository to deploy Google Cloud resources to multiple environments through Kubernetes manifest files.
* Enforce constraint policies on Google Cloud resources using Gatekeeper.

## Config Connector

Config Connector is an addon for Kubernetes that you can use to manage Google Cloud infrastructure such as Cloud Storage, Pub/Sub, and Cloud SQL through 
Kubernetes-style declarative APIs. 

We recommend that you install Config Connector in a separate cluster in a separate Google Cloud project, the _host project_. The other projects, where Google
Cloud resources are managed, are known as _managed projects_. 

1.  Define environment variables for the projects, the cluster name, and the Google Cloud zone:

        export HOST_PROJECT_ID=[YOUR_HOST_PROJECT_ID]
        export DEV_PROJECT_ID=[YOUR_DEVELOPMENT_PROJECT_ID]
        export PROD_PROJECT_ID=[YOUR_PRODUCTION_PROJECT_ID]
        export CLUSTER_NAME=cc-host-cluster
        export ZONE=us-east4-a

1.  Enable the Kubernetes Engine API:

        gcloud services enable container.googleapis.com --project $HOST_PROJECT_ID

1.  Create a Google Kubernetes Engine cluster in the host project that will serve as a host cluster for provisioning Google Cloud resources:

        gcloud beta container clusters create ${CLUSTER_NAME} --project=$HOST_PROJECT_ID --zone=${ZONE} --machine-type=e2-standard-4 \
          --workload-pool=${HOST_PROJECT_ID}.svc.id.goog

1.  Get cluster credentials:

        gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $HOST_PROJECT_ID

1.  Download the Config Connector operator file:

        gsutil cp gs://configconnector-operator/latest/release-bundle.tar.gz release-bundle.tar.gz

1.  Extract the contents of the file:

        tar zxvf release-bundle.tar.gz

1.  Install the operator:

        kubectl apply -f operator-system/configconnector-operator.yaml

1.  Create a Config Connector configuration to run in namespaced mode:

        #configconnector.yaml

        apiVersion: core.cnrm.cloud.google.com/v1beta1
        kind: ConfigConnector
        metadata:
          name: configconnector.core.cnrm.cloud.google.com
        spec:
         mode: namespaced

1.  Apply the configuration:

        kubectl apply -f configconnector.yaml

1.  Create a dedicated Kubernetes namespace for each environment that will contain resources:

        kubectl create namespace cc-tutorial-dev

        kubectl create namespace cc-tutorial-prod

1.  Annotate the namespaces so that resources are created in the correct Google Cloud projects:

        kubectl annotate namespace cc-tutorial-dev cnrm.cloud.google.com/project-id=$DEV_PROJECT_ID

        kubectl annotate namespace cc-tutorial-prod cnrm.cloud.google.com/project-id=$PROD_PROJECT_ID

1.  Create a dedicated IAM service account for each environment in the host project for Workload Identity to be able to create resources in Google Cloud:

        gcloud iam service-accounts create cc-tutorial-dev --project=$HOST_PROJECT_ID

        gcloud iam service-accounts create cc-tutorial-prod --project=$HOST_PROJECT_ID

1.  Give the service accounts elevated permissions in their respective projects to be able to manage resources:

        gcloud projects add-iam-policy-binding $DEV_PROJECT_ID \
          --member="serviceAccount:cc-tutorial-dev@${HOST_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/editor" 

        gcloud projects add-iam-policy-binding $PROD_PROJECT_ID \
          --member="serviceAccount:cc-tutorial-prod@${HOST_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/editor"

1.  Create binding between Google Cloud service accounts and Kubernetes service accounts through Workload Identity for the dev and prod Kubernetes service 
    accounts:

        gcloud iam service-accounts add-iam-policy-binding cc-tutorial-dev@${HOST_PROJECT_ID}.iam.gserviceaccount.com \
          --member="serviceAccount:${HOST_PROJECT_ID}.svc.id.goog[cnrm-system/cnrm-controller-manager-cc-tutorial-dev]" \
          --role="roles/iam.workloadIdentityUser" \
          --project=$HOST_PROJECT_ID

        gcloud iam service-accounts add-iam-policy-binding cc-tutorial-prod@${HOST_PROJECT_ID}.iam.gserviceaccount.com \
          --member="serviceAccount:${HOST_PROJECT_ID}.svc.id.goog[cnrm-system/cnrm-controller-manager-cc-tutorial-prod]" \
          --role="roles/iam.workloadIdentityUser" \
          --project=${HOST_PROJECT_ID}

1.  Give IAM service accounts permission to publish Prometheus metrics to Google Cloud:

        gcloud projects add-iam-policy-binding $HOST_PROJECT_ID \
          --member="serviceAccount:cc-tutorial-dev@${HOST_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/monitoring.metricWriter"

        gcloud projects add-iam-policy-binding $HOST_PROJECT_ID \
          --member="serviceAccount:cc-tutorial-prod@${HOST_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/monitoring.metricWriter"

1.  Create Config Connector context for both dev and prod namespaces to configure Config Connector to watch the namespaces where resources are being deployed:

        cat <<EOF > configconnectorcontext.yaml

        apiVersion: core.cnrm.cloud.google.com/v1beta1
        kind: ConfigConnectorContext
        metadata:
          name: configconnectorcontext.core.cnrm.cloud.google.com
          namespace: cc-tutorial-dev
        spec:
          googleServiceAccount: "cc-tutorial-dev@${HOST_PROJECT_ID}.iam.gserviceaccount.com"

        ---

        apiVersion: core.cnrm.cloud.google.com/v1beta1
        kind: ConfigConnectorContext
        metadata:
          name: configconnectorcontext.core.cnrm.cloud.google.com
          namespace: cc-tutorial-prod
        spec:
          googleServiceAccount: "cc-tutorial-prod@${HOST_PROJECT_ID}.iam.gserviceaccount.com"

        EOF

1.  Apply the configuration:

        kubectl apply -f configconnectorcontext.yaml

1.  Verify that Config Connector pods are running:

        kubectl wait -n cnrm-system --for=condition=Ready pod --all

    Optionally, you can verify that Config Connector is set up correctly by
    [deploying a Google Cloud resource](https://cloud.google.com/config-connector/docs/reference/overview), such as Cloud Storage.

## Config Sync

In this section, you install the Config Sync operator.  

Config Sync is a Kubernetes operator that allows managing Kubernetes resources in a GitOps workflow, in which the configurations are stored in the Git
repository and automatically pulled by the operator to be applied. 

1.  Download the Config Sync operator YAML file:

        gsutil cp gs://config-management-release/released/latest/config-sync-operator.yaml config-sync-operator.yaml

1.  Install the operator on the Config Sync cluster:

        kubectl apply -f config-sync-operator.yaml

1.  [Create an SSH key pair](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
    and copy the file path to the private key.

1.  Create a Kubernetes secret to store the private key for the repository:

        kubectl create secret generic git-creds \
          --namespace=config-management-system \
          --from-file=ssh=[/PATH/TO/KEYPAIR_PRIVATE_KEY_FILENAME]

    Replace `[/PATH/TO/KEYPAIR_PRIVATE_KEY_FILENAME]` with the path to the private key.

    After the Kubernetes secret is created, make sure to delete the private key from the local disk or store it in a safe location.

1.  Add the SSH public key to the version control system that you’re using. The process depends on the version control system, such as
    [GitLab](https://docs.gitlab.com/ee/ssh/#add-an-ssh-key-to-your-gitlab-account) or
    [GitHub](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).

1.  On your local machine, install the
    [`nomos` command-line tool](https://cloud.google.com/kubernetes-engine/docs/add-on/config-sync/how-to/nomos-command#installing),
    which you can use to interact with the Config Sync operator to check syntax, initialize the directory structure, and debug problems with the operator or
    cluster.  

1.  Initialize a new Config Sync repository directory structure:

        nomos init

    The generated directory structure should look like the following:

        ├── cluster/
        ├── namespaces/
        ├── README.md
        └── system/
            └── repo.yaml

1.  In the `namespaces` directory, create two sub-directories, `cc-tutorial-dev` and `cc-tutorial-prod`. These directory names must match the namespaces that
    you created in the Config Connector setup.

1.  Create configuration files for namespaces in `cc-tutorial-dev` and `cc-tutorial-prod`:

        #namespaces/cc-tutorial-dev/namespace.yaml

        apiVersion: v1
        kind: Namespace
        metadata:
          name: cc-tutorial-dev

        #cc-tutorial-prod/namespace.yaml

        apiVersion: v1
        kind: Namespace
        metadata:
          name: cc-tutorial-prod

    Even though the namespaces were already created during the Config Connector setup, creating the namespace configuration in these directories tells Config 
    Sync that this is a namespace directory, as opposed to an
    [abstract namespace directory](https://cloud.google.com/anthos-config-management/docs/concepts/namespace-inheritance#inheritance).

1.  Create a Git repository in a version control system such as GitHub or GitLab.

1.  Configure the operator:

        # config-management.yaml

        apiVersion: configmanagement.gke.io/v1
        kind: ConfigManagement
        metadata:
          name: config-management
        spec:
          clusterName: cc-host-cluster
          git:
            syncRepo: [GIT_REPOSITORY_URL]
            syncBranch: [BRANCH_NAME]
            secretType: ssh
            policyDir: [DIRECTORY_NAME]

    Replace `[GIT_REPOSITORY_URL]`, `[BRANCH_NAME]`, and `[DIRECTORY_NAME]` with the values for your repository.

1.  Apply the configuration:

        kubectl apply -f config-management.yaml

1.  Create Google Cloud resources in the corresponding environment to test the configuration. For this example, you create a Cloud Storage bucket in the
    dev workspace. Create a file with the following content in the `namespaces/cc-tutorial-dev` directory. Make sure that `metadata.name` has a globally 
    unique value, as required by Cloud Storage.

        # namespaces/cc-tutorial-dev/storagebucket.yaml

        apiVersion: storage.cnrm.cloud.google.com/v1beta1
        kind: StorageBucket
        metadata:
          annotations:
            cnrm.cloud.google.com/force-destroy: "false"
          name: cc-tutorial-bucket-dev
        spec:
          bucketPolicyOnly: true
          lifecycleRule:
            - action:
                type: Delete
              condition:
                age: 7
          versioning:
            enabled: true

1.  Commit and push the code to the repository.

    This triggers the Config Sync operator to pick up the changes and create the Kubernetes objects in the
    `cc-tutorial-dev` namespace. Config Connector then uses the configuration to create a Cloud Storage bucket in your Google Cloud dev project. 

    It may take some time for Config Sync to synchronize changes from the repository.

## Policy enforcement

 You can use Gatekeeper to create and enforce policies for Google Cloud resources. 

1.  Deploy a released version of Gatekeeper to your Kubernetes cluster:

        kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.3/deploy/gatekeeper.yaml

1.  Verify that the Gatekeeper service is running:

        kubectl -n gatekeeper-system describe svc gatekeeper-webhook-service

1.  Create a Gatekeeper constraint template and an instantiation of the template that requires all labels described by the constraint to be present for the 
    Pub/Sub topic. This file should be placed in the cluster directory because the configurations should apply to the entire cluster.

        apiVersion: templates.gatekeeper.sh/v1beta1
        kind: ConstraintTemplate
        metadata:
          name: pubsubrequiredlabels
        spec:
          crd:
            spec:
              names:
                kind: PubSubRequiredLabels
              validation:
                openAPIV3Schema:
                  properties:
                    labels:
                      type: array
                      items: 
                        type: string
          targets:
            - target: admission.k8s.gatekeeper.sh
              rego: |
                package pubsubrequiredlabels

                violation[{"msg": msg, "details": {"missing_labels": missing}}] {
                  provided := {label | input.review.object.metadata.labels[label]}
                  required := {label | label := input.parameters.labels[_]}
                  apiVersion := input.review.object.apiVersion
                  isKccType := contains(apiVersion, "cnrm.cloud.google.com")
                  missing := required - provided
                  isKccType; count(missing) > 0
                  msg := sprintf("you must provide labels: %v", [missing])
                }

        ---

        apiVersion: constraints.gatekeeper.sh/v1beta1
        kind: PubSubRequiredLabels
        metadata:
          name: must-contains-labels
        spec:
          match:
            kinds:
            - apiGroups: ["pubsub.cnrm.cloud.google.com"]
              kinds: ["PubSubTopic"]
          parameters:
            labels: ["env", "owner", "location"]

1.  Apply the changes by committing and pushing the code to the repository.

1.  Create a manifest file for a Pub/Sub topic resource in the `cc-tutorial-prod` directory:

        # namespaces/cc-tutorial-prod/pubsub.yaml

        apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
        kind: PubSubTopic
        metadata:
          labels:
            env: prod
            location: us-east4
          name: pubsubtopic-sample

    In a production scenario, this is where a workflow for code review is recommended before applying changes to the prod environment.
    
1.  Commit and push the code to the repository.

    This process will fail because of the constraint that you introduced to the cluster.

1.  View the error message by running this command in the root directory:

        nomos status
        
    The error message should look something like this:

        KNV2010: unable to apply resource: admission webhook "validation.gatekeeper.sh"
         denied the request: [must-contains-labels] you must provide labels: {"owner"}

1.  Make the necessary changes to add the owner label to the resource:

        apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
        kind: PubSubTopic
        metadata:
          labels:
            env: prod
            location: us-east4
            owner: john-doe
          name: pubsubtopic-sample

1.  Commit and push the code to the repository. The Pub/Sub topic should be created successfully in the prod Google Cloud project.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the projects.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
