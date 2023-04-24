---
title: Set up CI/CD with Spinnaker and Binary Authorization
description: Creating attestations by integrating Cloud Build, Spinnaker, Cloud KMS, and Binary Authorization to securely deploy Kubernetes applications.
author: damadei-google
tags: Kubernetes, Spinnaker, continuous integration, continuous delivery, DevOps, Binary Authorization, Cloud KMS, Cloud Build
date_published: 2020-07-01
---

Daniel Amadei | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This document demonstrates how to perform continuous integration and continuous delivery to a Kubernetes cluster using Cloud Build for building images, 
Spinnaker for continuous deployment, and Binary Authorization with keys hosted in Cloud Key Management Service (Cloud KMS) for protecting and attesting the
provenance of images being deployed to Kubernetes.

Choosing whether to attest an image during build or deployment depends on your CI/CD architecture. The goal of this document is to show you how to 
do so during the deployment phase.

## Setup

Binary Authorization is handled using separate projects to hold the attestor and the keys, so you can keep controls and authorization separate.

In this section, you create the projects and resources used throughout this document.

### Create a deployer project

The deployer project is the project where your Kubernetes cluster will be created and where Spinnaker will be installed.

### Create a Kubernetes cluster

Create a Kubernetes cluster where you will deploy the application, using the standard
[instructions to create a cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-regional-cluster).

### Install Spinnaker

Install [Spinnaker for Google Cloud](https://console.cloud.google.com/marketplace/details/google-cloud-platform/spinnaker) in the same project as the user 
cluster that you created, but in a different Kubernetes cluster dedicated to Spinnaker.

### Connect the GKE cluster to Spinnaker

After the user cluster is created, connect it to Spinnaker and push the configurations:

1.  In Cloud Shell, run the following command to get the credentials of the user cluster and store it locally:

        gcloud container clusters get-credentials <CLUSTER_NAME> [--zone <YOUR_ZONE> or --region <YOUR_REGION>] --project <PROJECT_ID>

1.  Go to the Spinnaker `manage` folder:

        cd ~/cloudshell_open/spinnaker-for-gcp/scripts/manage

1.  Run the script to add a GKE account to Spinnaker:

        ./add_gke_account.sh

    Provide the information requested by the script. It will ask for the context of the user cluster and will gather the required information to create a 
    connection from Spinnaker to the GKE cluster.

1.  Run the script to push the configurations to Spinnaker:

        ./apply_config.sh

### Configure variables and enable APIs

Export variables and enable APIs used throughout this procedure: 

    DEPLOYER_PROJECT_ID=<YOUR_DEPLOYER_PROJECT_ID>
    DEPLOYER_PROJECT_NUMBER=$(gcloud projects describe "${DEPLOYER_PROJECT_ID}" --format="value(projectNumber)")

    gcloud --project=${DEPLOYER_PROJECT_ID} \
        services enable \
        container.googleapis.com \
        binaryauthorization.googleapis.com

    DEPLOYER_SERVICE_ACCOUNT="service-${DEPLOYER_PROJECT_NUMBER}@gcp-sa-binaryauthorization.iam.gserviceaccount.com"

### Set up the attestor project

The setup for the attestor project is similar to the process described [here](https://cloud.google.com/binary-authorization/docs/multi-project-setup-cli), 
except that only one project will be used to hold the attestor, attestations, and keys in Cloud KMS. 

1.  Create the following environment variables:

        ATTESTOR_PROJECT_ID=<YOUR_ATTESTOR_PROJECT_ID>
        ATTESTOR_PROJECT_NUMBER=$(gcloud projects describe "${ATTESTOR_PROJECT_ID}" --format="value(projectNumber)")
        ATTESTOR_SERVICE_ACCOUNT="service-${ATTESTOR_PROJECT_NUMBER}@gcp-sa-binaryauthorization.iam.gserviceaccount.com"

1.  Run the following commands:

        gcloud config set project ${ATTESTOR_PROJECT_ID}
        gcloud services --project=${ATTESTOR_PROJECT_ID} \
            enable containeranalysis.googleapis.com \
            binaryauthorization.googleapis.com

### Create the Container Analysis note

Create the Container Analysis note, which is required by the attestor to create the attestations: 

1.  Export the variables.

        ATTESTOR_NAME=container-attestor
        NOTE_ID=container-attestor-note

1.  Create the note payload file:

            cat > /tmp/note_payload.json << EOM
            {
            "name": "projects/${ATTESTOR_PROJECT_ID}/notes/${NOTE_ID}",
            "attestation": {
                "hint": {
                "human_readable_name": "Attestor Note"
                }
            }
            }
            EOM

1.  Create the note by sending an HTTP request to the Container Analysis REST API:

        curl -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $(gcloud auth print-access-token)" \
            --data-binary @/tmp/note_payload.json  \
            "https://containeranalysis.googleapis.com/v1/projects/${ATTESTOR_PROJECT_ID}/notes/?noteId=${NOTE_ID}"

1.  Verify that the note was created:

        curl \
        -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        "https://containeranalysis.googleapis.com/v1/projects/${ATTESTOR_PROJECT_ID}/notes/${NOTE_ID}"


### Create the attestor

Create the attestor in the respective project with the ID represented by the exported `ATTESTOR_PROJECT_ID` variable.

1.  Create the attestor by running the following command:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestors create ${ATTESTOR_NAME} \
            --attestation-authority-note=${NOTE_ID} \
            --attestation-authority-note-project=${ATTESTOR_PROJECT_ID}

1.  Verify that the attestor was created:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestors list

1.  Add permission for the deployer service account to access the attestor:

        gcloud --project ${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestors add-iam-policy-binding \
            "projects/${ATTESTOR_PROJECT_ID}/attestors/${ATTESTOR_NAME}" \
            --member="serviceAccount:${DEPLOYER_SERVICE_ACCOUNT}" \
            --role=roles/binaryauthorization.attestorsVerifier
	    
     This command gives access to the deployer project Binary Authorization service account to access the attestor in the attestor project.

### Set permissions on the Container Analysis note

Set permissions on the Container Analysis note for the attestor service account:

    cat > /tmp/iam_request.json << EOM
    {
        'resource': 'projects/${ATTESTOR_PROJECT_ID}/notes/${NOTE_ID}',
        'policy': {
            'bindings': [
            {
                'role': 'roles/containeranalysis.notes.occurrences.viewer',
                'members': [
                'serviceAccount:${ATTESTOR_SERVICE_ACCOUNT}'
                ]
            }
            ]
        }
    }
    EOM

### Create KMS keys

In this section, you create the KMS keys that will be used by the attestor to sign and then verify the signature of the attestation.

1.  Create and export the variables that will be used to create the key:

        KMS_KEY_PROJECT_ID=${ATTESTOR_PROJECT_ID}
        KMS_KEYRING_NAME=my-binauthz-keyring
        KMS_KEY_NAME=my-binauthz-kms-key-name
        KMS_KEY_LOCATION=global
        KMS_KEY_PURPOSE=asymmetric-signing
        KMS_KEY_ALGORITHM=ec-sign-p256-sha256
        KMS_PROTECTION_LEVEL=software
        KMS_KEY_VERSION=1

     The values for the key ring name and key name are examples. You can change them to names that suit your needs.	

1.  Create a key ring:

        gcloud kms keyrings create ${KMS_KEYRING_NAME} \
        --location ${KMS_KEY_LOCATION} \
        --project ${KMS_KEY_PROJECT_ID}

1.  Create a key inside the key ring:

        gcloud kms keys create ${KMS_KEY_NAME} \
        --location ${KMS_KEY_LOCATION} \
        --keyring ${KMS_KEYRING_NAME}  \
        --purpose ${KMS_KEY_PURPOSE} \
        --default-algorithm ${KMS_KEY_ALGORITHM} \
        --protection-level ${KMS_PROTECTION_LEVEL} \
        --project ${KMS_KEY_PROJECT_ID}

4. Add the key to the attestor as a trusted key to sign the payloads of trusted images:

        gcloud --project="${ATTESTOR_PROJECT_ID}" \
            alpha container binauthz attestors public-keys add \
            --attestor="${ATTESTOR_NAME}" \
            --keyversion-project="${KMS_KEY_PROJECT_ID}" \
            --keyversion-location="${KMS_KEY_LOCATION}" \
            --keyversion-keyring="${KMS_KEYRING_NAME}" \
            --keyversion-key="${KMS_KEY_NAME}" \
            --keyversion="${KMS_KEY_VERSION}"

### Create and configure the policy

The policy is the configuration in the deployer project to only allow images to be deployed to GKE clusters in this project that have been attested by the
attestor from the attestor project.

1.  Configure the policy YAML file:

        cat > /tmp/policy.yaml << EOM
            globalPolicyEvaluationMode: true
            admissionWhitelistPatterns:
            - namePattern: gcr.io/google_containers/*
            - namePattern: gcr.io/google-containers/*
            - namePattern: k8s.gcr.io/*
            - namePattern: gcr.io/stackdriver-agents/*
            - namePattern: gcr.io/gke-release/asm/*
            defaultAdmissionRule:
            evaluationMode: REQUIRE_ATTESTATION
            enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
            requireAttestationsBy:
                - projects/${ATTESTOR_PROJECT_ID}/attestors/${ATTESTOR_NAME}
            name: projects/${DEPLOYER_PROJECT_ID}/policy
        EOM

1.  Create the policy in the deployer project to allow just images attested by this attestor be deployed to GKE clusters in this project:

        gcloud --project=${DEPLOYER_PROJECT_ID} \
            beta container binauthz policy import /tmp/policy.yaml

### Test the setup

To test the policy, create an attestation:

1.  Export the variables to test the policy:

        IMAGE_PATH="gcr.io/google-samples/hello-app"
        IMAGE_DIGEST="sha256:c62ead5b8c15c231f9e786250b07909daf6c266d0fcddd93fea882eb722c3be4"

1.  Create the signature payload:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz create-signature-payload \
            --artifact-url=${IMAGE_PATH}@${IMAGE_DIGEST} > /tmp/generated_payload.json

1.  Sign the `generated_payload.json` file created in the previous step using the keys hosted in Cloud KMS:

        gcloud kms asymmetric-sign \
            --location=${KMS_KEY_LOCATION} \
            --keyring=${KMS_KEYRING_NAME} \
            --key=${KMS_KEY_NAME} \
            --version=${KMS_KEY_VERSION} \
            --digest-algorithm=sha256 \
            --input-file=/tmp/generated_payload.json \
            --signature-file=/tmp/ec_signature \
            --project ${KMS_KEY_PROJECT_ID}

1.  Generate the attestation using the signed file created in the previous step:

        PUBLIC_KEY_ID=$(gcloud container binauthz attestors describe ${ATTESTOR_NAME} \
        --format='value(userOwnedGrafeasNote.publicKeys[0].id)' --project ${ATTESTOR_PROJECT})

        IMAGE_TO_ATTEST=${IMAGE_PATH}@${IMAGE_DIGEST}

        gcloud container binauthz attestations create \
            --project="${ATTESTOR_PROJECT_ID}" \
            --artifact-url="${IMAGE_TO_ATTEST}" \
            --attestor="projects/${ATTESTOR_PROJECT_ID}/attestors/${ATTESTOR_NAME}" \
            --signature-file=/tmp/ec_signature \
            --public-key-id="${PUBLIC_KEY_ID}"

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestations list \
            --attestor=$ATTESTOR_NAME \
            --attestor-project=$ATTESTOR_PROJECT_ID

1.  Check whether the attestation was created successfully:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestations list \
            --attestor=$ATTESTOR_NAME \
            --attestor-project=$ATTESTOR_PROJECT_ID

1.  Run a Pod based on an image that was attested:

        kubectl run hello-server --image ${IMAGE_PATH}@${IMAGE_DIGEST} --port 8080

1.  Check whether the Pod was created:

        kubectl get pods

1.  If the test succeeded, delete the deployment:

        kubectl delete deployment hello-server

The manual steps in this testing section are only to test the setup. The attestation later in this procedure is not manually created as you did here, but 
is created by Spinnaker as part of the continuous delivery process.

## Building the application

You host your application in a Cloud Source Repository in the `DEPLOYER` project, the project that contains your clusters and Spinnaker.

### Set up a Cloud Source Repositories repository

1.  Clone the sample application:

        git clone https://github.com/damadei-google/products-api

1.  Create a repository with Cloud Source Repositories that will hold the source for this project:

        gcloud source repos create products-api \
        --project=${DEPLOYER_PROJECT_ID}

1.  Configure Cloud Source Repositories authentication by following instructions in
    [Authenticate by using SSH](https://cloud.google.com/source-repositories/docs/authentication#ssh).

1.  Change the remote origin of the local repository and push source code to the new repository in Cloud Source Repositories:

        cd products-api
        git remote remove origin
        git remote add origin ssh://<YOUR USER'S EMAIL>@source.developers.google.com:2022/p/${DEPLOYER_PROJECT_ID}/r/products-api
        git push --set-upstream origin master

### Configure automatic builds in Cloud Build

In this section, you configure Cloud Build to automatically trigger a build process when a new push is made to the master branch of your source repository. This
allows you to automatically deploy the application whenever a change is made to the source code and pushed to the repository.

1.  In Cloud Build, click **Triggers**, and then connect Cloud Source Repository to it and find the `products-api` repository.
1.  At the right side of the entry for the repository, click the button with three dots stacked vertically, and select **Add Trigger**.
1.  Configure the trigger:
    1. Name the trigger `products-api-trigger`.
    1. Select **Push to a branch**. 
    1. Enter `^master$` as the branch regular expression. 
    1. In the **Build configuration** section, select **Cloud Build configuration file (yaml or json)** and leave the default filename, `/cloudbuild.yaml`.
    1. Click **Add Variable** and add a substitution variable named `_VERSION` with value `1.0` and keep it as **User-defined**.
1.  Click **Create**.

The `cloudbuild.yaml` file contains the following:

    steps:
    - name: 'gcr.io/cloud-builders/docker'
    args: [ 'build', '-t', 'gcr.io/$PROJECT_ID/products-api:${_VERSION}', '.' ]
    images:
    - 'gcr.io/$PROJECT_ID/products-api:${_VERSION}'

This file instructs Cloud Build to build a Docker image using the Dockerfile in the repository and then to push the generated Docker image to Container
Registry when done. This happens when a new push is made to the repository in the master branch.

To test this part of the system, push a change to the repository and check whether the build is started automatically, as shown here:

![Build history](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/01-build-history.png)

After the build is successful, check whether the image is placed in Container Registry:

![GCR](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/02-gcr.png)

## Configuring Spinnaker

When you install Spinnaker for Google Cloud, Spinnaker comes pre-configured with a connection to a Cloud Build Pub/Sub topic in the same project that it's
installed in (and another one for the Google Container Registry topic). This is sufficient for the demonstration here. In real-world scenarios, you can add 
connections to different projects, since Spinnaker will probably be in a different project from your user cluster.

For GKE, a connection was created after installing Spinnaker in the beginning of this document.

### Create an application in Spinnaker

To create an application in Spinnaker, do the following in the Spinnaker console:

1.  Click **Actions**.
1.  Click **Create Application**.
1.  Name the application `products-api`.
1.  Enter your email address for **Owner Email**.

![New Application](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/03-new-app.png)


### Create a pipeline in Spinnaker

1.  Click **Configure**.
1.  Name the pipeline `products-api-pipeline`.
1.  Click **Create**.

### Create a trigger

In this section, you create a trigger that starts the continuous delivery pipeline. 

1.  In the **Automated Triggers** section, click **Add Trigger**.

    ![New Trigger](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/04-trigger.png)

1.  For **Type**, select **Pub/Sub**.
1.  Set **Pub/Sub System Type** to `google`.
1.  For **Subscription Name**, enter `gcb-account`.
1.  In the **Payload Constraints** section, enter `status` for **Key** and `SUCCESS` for **Value**. This will filter messages to process builds 
    only when they are finished and successful.
1.  Click **Save Changes**.

![Configuring Trigger](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/05-new-trigger.png)

### Test the trigger

1. Go to the [**Triggers** page](https://console.cloud.google.com/cloud-build/triggers) in the Cloud Console.
1. Click **Run trigger**.

After the build is complete and successful, go back to Spinnaker and check whether it shows that the pipeline has executed. There should be an execution, 
showing that the trigger is working, as in the following screenshot:

![First execution](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/06-first-run.png)

### Extract details from the built image

In this section, you get the image name and image digest from the created image. These details are used to create an image URL, which is used for signature and
attestation creation, as well as for deployment. 

1.  Add a new stage to the pipeline.
1.  Change the type to **Evaluate Variables**.
1.  Name the stage `Get Image Details`.

    ![Get Image details](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/07-get-img-details.png)

1.  Create a variable named `imageName` and point it to `${trigger.payload.results.images[0].name}`.
1.  Create a variable named `imageDigest` and point it to `${trigger.payload.results.images[0].digest}`.

    ![Variables](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/08-vars.png)

1.  Save the changes.
1.  Test the pipeline by running the trigger on Cloud Build. 
1.  Check whether variables were correctly extracted.

    ![Variable extraction](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/09-var-extract.png)

1.  Add a variable named `imageAndHash` with the following content:

        ${trigger.payload.results.images[0].name.substring(0, trigger.payload.results.images[0].name.indexOf(":")) + "@" + trigger.payload.results.images[0].digest}

    The result should look like this:

    ![Image and Hash Variable](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/10-image-and-hash.png)

1.  Click **Save Changes**.

## Creating the attestation

An [attestation](https://cloud.google.com/binary-authorization/docs/key-concepts#attestations) is a digitally signed document, made by a signer, that certifies 
that a required process in your pipeline was completed and that the resulting container image is authorized for deployment in GKE. The attestation itself 
contains the full path to the version of the container image as stored in your container image registry, as well as a signature created by signing the globally 
unique digest that identifies a specific container image build.

Because Spinnaker can't run a script itself to create the attestation, you use a Kubernetes Job running on the Spinnaker Kubernetes cluster. This job has a 
script that creates the attestation along with the signature of the payload required by Binary Authorization.

Run the script with the Spinnaker service account. This service account needs permission in the project hosting the Binary Authorization artifacts. This ensures
that Spinnaker is only party with permissions to create the attestation.

### Create the Binary Authorization Job Docker container image

In this section, you create a Docker container based on the Google Cloud SDK base image and place that on Google Cloud Registry to be accessed by the Spinnaker 
Kubernetes cluster.

1.  In a new directory containing the code for creating the attestation, create a script named `attest_image.sh` with the following content:

        #!/bin/bash
        echo "Image to attest: ${IMAGE_TO_ATTEST}"

        attestation_list_result=$(gcloud container binauthz attestations list \
        --project="${ATTESTOR_PROJECT_ID}" \
        --attestor="projects/${ATTESTOR_PROJECT_ID}/attestors/${ATTESTOR_NAME}" \
        --artifact-url="${IMAGE_TO_ATTEST}")

        echo "Attestation list: ${attestation_list_result}"

        if [ -z "$attestation_list_result" ]
        then
        gcloud container binauthz create-signature-payload \
            --project=${ATTESTOR_PROJECT_ID} \
            --artifact-url="${IMAGE_TO_ATTEST}" > /tmp/generated_payload.json

        gcloud kms asymmetric-sign \
                --location=${KMS_KEY_LOCATION} \
                --keyring=${KMS_KEYRING_NAME} \
                --key=${KMS_KEY_NAME} \
                --version=${KMS_KEY_VERSION} \
                --digest-algorithm=sha256 \
                --input-file=/tmp/generated_payload.json \
                --signature-file=/tmp/ec_signature \
                --project ${KMS_KEY_PROJECT_ID}

        PUBLIC_KEY_ID=$(gcloud container binauthz attestors describe ${ATTESTOR_NAME} \
                    --format='value(userOwnedGrafeasNote.publicKeys[0].id)' \
                    --project ${ATTESTOR_PROJECT_ID})

        gcloud container binauthz attestations create \
            --project="${ATTESTOR_PROJECT_ID}" \
            --artifact-url="${IMAGE_TO_ATTEST}" \
            --attestor="projects/${ATTESTOR_PROJECT_ID}/attestors/${ATTESTOR_NAME}" \
            --signature-file=/tmp/ec_signature \
            --public-key-id="${PUBLIC_KEY_ID}"

        echo "Attestation created"

        else
            echo "Attestation already created for image ${IMAGE_TO_ATTEST}"
        fi

        exit 0

1.  In the same directory, create a Dockerfile with the following code:

        FROM google/cloud-sdk:latest

        ADD attest_image.sh /opt/google/bin-authz/attest_image.sh

        RUN chmod +x /opt/google/bin-authz/attest_image.sh

1.  Build the container image and push it to Container Registry by running these commands:

        cd [DIRECTORY WHERE YOU HOSTED THE FILES]
        docker build . -t gcr.io/<PROJECT ID>/bin-authz-job
        docker push gcr.io/<PROJECT ID>/bin-authz-job
	
    The project ID is the ID of the project where Spinnaker is installed and where you will host this Docker image.

### Run the job in Spinnaker

1.  Go back to Spinnaker and add a new stage with type **Run Job (Manifest)**, and name it `Create Attestation`.

    ![Create Attestation Job](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/11-create-attestation.png)

1.  For **Account**, enter `spinnaker-install-account`. This is the Kubernetes account for the cluster where Spinnaker is installed, which comes pre-defined with
    Spinnaker for Google Cloud.

    ![Run Job Configuration](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/12-run-job.png)

1.  Add the following text as the manifest text, making the necessary changes to point to your project and replacing the other environment variables.

        apiVersion: batch/v1
        kind: Job
        metadata:
        name: attest-image
        namespace: jobs
        spec:
        backoffLimit: 4
        template:
            spec:
            containers:
                - command:
                    - /opt/google/bin-authz/attest_image.sh
                env:
                    - name: IMAGE_TO_ATTEST
                    value: '${imageAndHash}'
                    - name: DEPLOYER_PROJECT_ID
                    value: <DEPLOYER PROJECT ID>
                    - name: ATTESTOR_PROJECT_ID
                    value: <ATTESTOR PROJECT ID>
                    - name: ATTESTOR_NAME
                    value: <ATTESTOR NAME>
                    - name: KMS_KEY_PROJECT_ID
                    value: <ATTESTOR PROJECT ID>
                    - name: KMS_KEY_LOCATION
                    Value: <KMS KEY LOCATION>
                    - name: KMS_KEYRING_NAME
                    value: <KMS KEYRING NAME>
                    - name: KMS_KEY_NAME
                    value: <KMS KEY NAME>
                    - name: KMS_KEY_VERSION
                    value: <KMS KEY VERSION>
                image: 'gcr.io/<SPINNAKER PROJECT ID>/bin-authz-job:latest'
                name: attest-image
            restartPolicy: Never

The jobs will be hosted in the jobs namespace. You should connect manually to the Spinnaker Kubernetes cluster and create this namespace previously.

### Test the build

Test the build by triggering the Cloud Build trigger manually in Cloud Console. After that, check whether the Spinnaker pipeline was triggered.

The build should succeed and you should see two green steps:

![Success running job](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/13-run-job-steps.png)

Look at the console output for the Create Attestation phase, for which you should see the following:

    Image to attest: gcr.io/<PROJECT ID>/products-api@<IMAGE HASH>
    Listed 0 items.
    Attestation list: 
    Attestation created

### Add permissions to access attestation resources

The service account used by Spinnaker needs permissions to access the attestor resources like Cloud KMS keys and to create the attestation. Because they are in
different projects, you must add the service account from Spinnaker's project to the attestor project and give it the proper roles.

In this section, you get the name of the Spinnaker service account and then add permissions to the service account in the attestor project, which holds the 
Binary Authorization attestor and also the Cloud KMS keys for signing the attestation

1.  Go to the Spinnaker GKE cluster in Cloud Console and click **Permissions**.

    The service account name is shown in the following form:

        <account name>@<project id>.iam.gserviceaccount.com

1.  In the Cloud Console, go to the attestor project.
1.  In the navigation menu click **IAM & Admin** > **IAM**.
1.  Click the **Add** button to add an IAM permission.
1.  Enter the email address of the Spinnaker service account and add the following roles:
    * **Binary Authorization Attestor Editor**
    * **Binary Authorization Attestor Viewer**
    * **Binary Authorization Service Agent**
    * **Cloud KMS CryptoKey Signer/Verifier**
    * **Container Analysis Notes Editor**
    * **Container Analysis Occurrences Editor**
    * **Container Analysis Occurrences Viewer**

This allows the job deployed to the Spinnaker Kubernetes cluster to access the required resources and create the attestations in the attestor project.

## Deploy the application

In this section, you create a deployment manifest and deploy the application.

1.  Add a new stage of type **Deploy (Manifest)** and name it `Deploy Application`.

    ![Add stage for App Deployment](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/14-deploy-app-stage.png)

1.  Select the account you want to deploy to, which is the account that was connected to Spinnaker representing the deployment cluster.

    ![Stage Config](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/15-manifest-config.png)

1.  Enter the following as the deployment configuration manifest text to deploy the application:

        apiVersion: apps/v1
        kind: Deployment
        metadata:
        name: products-api
        labels:
            app: products-api
            version: v1
        spec:
        replicas: 1
        selector:
            matchLabels:
            app: products-api
            version: v1
        template:
            metadata:
            labels:
                app: products-api
                version: v1
            spec:
            containers:
                - name: products-api
                image: ${imageAndHash}
                ports:
                    - containerPort: 8080

1.  Test the deployment and check whether the deployment was created successfully in Kubernetes and if the Pods are running, indicating that Binary 
    Authorization is working properly. 

    ![Deployment Success](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/16-three-steps-success.png)

    ![Deployment Success](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/17-deployment-ok.png)

## Deploy a service

The last step is to deploy a service capable of exposing a business API.

1.  Add a parallel step to the `Deploy Application` step, with same type as the `Deploy Application` step, and name it `Deploy Service`.

    ![Service Deployment](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/18-svc-deployment.png)

1.  Configure the deployment text YAML as the following:

        apiVersion: v1
        kind: Service
        metadata:
          name: products-api
        spec:
          ports:
          - port: 80
            protocol: TCP
            targetPort: 8080
        selector:
          app: products-api
          sessionAffinity: None
        type: LoadBalancer

1. Test the deployment by triggering it from Cloud Build, and check whether the deployment of the service along with the application succeeded.

    ![Service Deployment Success](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/19-svc-deployment-ok.png)

1.  Get the load balancer IP address by running the following in the user cluster:

        kubectl get svc

1.  In your browser, go to the following URL: `http://<LOAD_BALANCER_IP_ADDRESS>/products`

    You should get a list of products, returned by your application.

## Summary

In this tutorial, you've followed a full cycle of continuous integration and continuous deployment: from source code triggering a build automatically with a 
Cloud Build trigger, through building the Docker image, to starting a Spinnaker pipeline capable of providing an image attestation to be deployed to a cluster 
with a Binary Authorization policy enabled.
