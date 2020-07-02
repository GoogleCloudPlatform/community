---
title: CI/CD with Spinnaker and Binary Authorization
description: Creating attestations by integrating Cloud Build, Spinnaker, Cloud KMS, and Binary Authorization to securely deploy Kubernetes applications.
author: damadei-google
tags: Kubernetes, Spinnaker, continuous integration, continuous delivery, DevOps, Binary Authorization, Cloud KMS, Cloud Build
date_published: 2020-07-01
---

Daniel Amadei | Customer Engineer | Google

This document demonstrates how to perform continuous integration and continuous delivery to a Kubernetes cluster using Cloud Build for building images, 
Spinnaker for continuous deployment, and Binary Authorization with keys hosted in Cloud Key Management Service (Cloud KMS) for protecting and attesting the
provenance of images being deployed to Kubernetes.

## Setup

Binary Authorization is handled using separate projects to hold the attestor and the keys, so you can keep controls and authorization separate.

In this section, you create the projects and resources used throughout this document.

### Create a deployer project

The deployer project is the project where your Kubernetes cluster will be created and where Spinnaker will be installed.

### Create a Kubernetes cluster

Create a Kubernetes cluster where you will deploy the application. There are no special needs for the cluster creation; you can follow the
standard [instructions to create a cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-regional-cluster).

### Install Spinnaker

Install [Spinnaker for Google Cloud](https://console.cloud.google.com/marketplace/details/google-cloud-platform/spinnaker) in the same project as the user 
cluster that you created, but in a different Kubernetes cluster dedicated to Spinnaker.

### Connect the GKE cluster to Spinnaker

After the user cluster is created, connect it to Spinnaker and push the configurations.

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

### Attestor project

Setup should be based in [this](https://cloud.google.com/binary-authorization/docs/multi-project-setup-cli) document but only one project will be used to hold the attestor, attestations and keys in Cloud KMS so instructions will be provided as they are a little bit different from the referred link. 

Assuming `gcloud` is already authenticated, create the following environment vars:

    ATTESTOR_PROJECT_ID=<ATTESTOR PROJECT ID>
    ATTESTOR_PROJECT_NUMBER=$(gcloud projects describe "${ATTESTOR_PROJECT_ID}" --format="value(projectNumber)")
    ATTESTOR_SERVICE_ACCOUNT="service-${ATTESTOR_PROJECT_NUMBER}@gcp-sa-binaryauthorization.iam.gserviceaccount.com"

Now, run the following commands:

    gcloud config set project ${ATTESTOR_PROJECT_ID}
    gcloud services --project=${ATTESTOR_PROJECT_ID} \
        enable containeranalysis.googleapis.com \
        binaryauthorization.googleapis.com


### Creating the Container Analysis Note

Create the container analysis note which is required by the attestor to create the attestations. 

1. First, export the variables.

        ATTESTOR_NAME=container-attestor
        NOTE_ID=container-attestor-note

2. Create the note payload file:

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

3. Create the note by sending an HTTP request to the Container Analysis REST API:

        curl -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $(gcloud auth print-access-token)" \
            --data-binary @/tmp/note_payload.json  \
            "https://containeranalysis.googleapis.com/v1/projects/${ATTESTOR_PROJECT_ID}/notes/?noteId=${NOTE_ID}"

4. Verify that the note was created:

        curl \
        -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        "https://containeranalysis.googleapis.com/v1/projects/${ATTESTOR_PROJECT_ID}/notes/${NOTE_ID}"

5. It should have been created successfully.


### Creating the Attestor
Now it's time to create the attestor in the respective project with the id represented by the ATTESTOR_PROJECT_ID exported variable.

1. Create the attestor by running the following command:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestors create ${ATTESTOR_NAME} \
            --attestation-authority-note=${NOTE_ID} \
            --attestation-authority-note-project=${ATTESTOR_PROJECT_ID}

2. Verify the attestor was created:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestors list

3. Add permission for the deployer service account to access the attestor. This command gives access to the DEPLOYER project binary authorization service account to access the attestor in the ATTESTOR project:

        gcloud --project ${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestors add-iam-policy-binding \
            "projects/${ATTESTOR_PROJECT_ID}/attestors/${ATTESTOR_NAME}" \
            --member="serviceAccount:${DEPLOYER_SERVICE_ACCOUNT}" \
            --role=roles/binaryauthorization.attestorsVerifier

### Set permissions on the Container Analysis note
Permission should be set on the container analysis note to the attestor service account.

Set permission on the container analysis note:

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

### Creating KMS Keys
Create the KMS keys which will be used by the attestor to sign and then verify signature of the attestation.

1. First create and export the variables that will be used to create the key. These are sample names for the key ring and key name, feel free to change such samples to names that are better to your case:

        KMS_KEY_PROJECT_ID=${ATTESTOR_PROJECT_ID}
        KMS_KEYRING_NAME=my-binauthz-keyring
        KMS_KEY_NAME=my-binauthz-kms-key-name
        KMS_KEY_LOCATION=global
        KMS_KEY_PURPOSE=asymmetric-signing
        KMS_KEY_ALGORITHM=ec-sign-p256-sha256
        KMS_PROTECTION_LEVEL=software
        KMS_KEY_VERSION=1

2. Create a key ring:

        gcloud kms keyrings create ${KMS_KEYRING_NAME} \
        --location ${KMS_KEY_LOCATION} \
        --project ${KMS_KEY_PROJECT_ID}

3. Create a key inside the key ring:

        gcloud kms keys create ${KMS_KEY_NAME} \
        --location ${KMS_KEY_LOCATION} \
        --keyring ${KMS_KEYRING_NAME}  \
        --purpose ${KMS_KEY_PURPOSE} \
        --default-algorithm ${KMS_KEY_ALGORITHM} \
        --protection-level ${KMS_PROTECTION_LEVEL} \
        --project ${KMS_KEY_PROJECT_ID}

4. Finally, add the key to the attestor as trusted keys to sign the payloads of trusted images

        gcloud --project="${ATTESTOR_PROJECT_ID}" \
            alpha container binauthz attestors public-keys add \
            --attestor="${ATTESTOR_NAME}" \
            --keyversion-project="${KMS_KEY_PROJECT_ID}" \
            --keyversion-location="${KMS_KEY_LOCATION}" \
            --keyversion-keyring="${KMS_KEYRING_NAME}" \
            --keyversion-key="${KMS_KEY_NAME}" \
            --keyversion="${KMS_KEY_VERSION}"


### Configure the Policy
Now a policy should be created. This policy is the configuration in the `DEPLOYER` project to only allow images to be deployed to GKE clusters in this project that have been attested by the attestor from the `ATTESTOR` project.

For that, do the following:

1. Configure the policy YAML file:

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

2. Create the policy in the deployer project to allow just images attested by this attestor be deployed to GKE clusters in this project:

        gcloud --project=${DEPLOYER_PROJECT_ID} \
            beta container binauthz policy import /tmp/policy.yaml

### Testing all the setup we've done so far
Create an attestation to test the policy. For that, do the following:

1. Export the variables to test the policy:


       IMAGE_PATH="gcr.io/google-samples/hello-app"
        IMAGE_DIGEST="sha256:c62ead5b8c15c231f9e786250b07909daf6c266d0fcddd93fea882eb722c3be4"

2. Create the signature payload:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz create-signature-payload \
            --artifact-url=${IMAGE_PATH}@${IMAGE_DIGEST} > /tmp/generated_payload.json

3. Sign the `generated_payload.json` file created in the previous step using the keys hosted in Cloud KMS:

            gcloud kms asymmetric-sign \
                --location=${KMS_KEY_LOCATION} \
                --keyring=${KMS_KEYRING_NAME} \
                --key=${KMS_KEY_NAME} \
                --version=${KMS_KEY_VERSION} \
                --digest-algorithm=sha256 \
                --input-file=/tmp/generated_payload.json \
                --signature-file=/tmp/ec_signature \
                --project ${KMS_KEY_PROJECT_ID}

4. Generate the attestation using the signed file created in the previous step:

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

5. Now, check if the attestation was created successfully:

        gcloud --project=${ATTESTOR_PROJECT_ID} \
            beta container binauthz attestations list \
            --attestor=$ATTESTOR_NAME \
            --attestor-project=$ATTESTOR_PROJECT_ID

6. Try to run a POD based on an image that was attested:

        kubectl run hello-server --image ${IMAGE_PATH}@${IMAGE_DIGEST} --port 8080

7. Check if PODs were created, they should have been created, meaning everything is working fine:

        kubectl get pods

8. If everything is fine, delete the deployment. This was just to test all the setup as the attestation will not be manually created as we did here but will be created by Spinnaker as part of the continuous delivery process.

        kubectl delete deployment hello-server


## Building the Application

Now it's time to start working with the application. We will first host it in a Cloud Source Repository in the `DEPLOYER` project, the project that contains our clusters and also Spinnaker.

### Setting up a Cloud Source Repositories repository

First clone the sample application:

    git clone https://github.com/damadei-google/products-api

Now create a Cloud Source Repository which will hold the sources of this project that we will use for CI/CD exemplification.

    gcloud source repos create products-api \
    --project=${DEPLOYER_PROJECT_ID}

Configure Cloud Source Repositories authentication by following instructions here: https://cloud.google.com/source-repositories/docs/authentication. We assume you are going to use SSH authentication.

Change the remote origin of the local git repo and push source code to the new repo in CSR:

	cd products-api

    git remote remove origin

    git remote add origin ssh://<YOUR USER'S EMAIL>@source.developers.google.com:2022/p/${DEPLOYER_PROJECT_ID}/r/products-api

    git push --set-upstream origin master

### Configuring Automatic Build in Cloud Build

Now it's time to configure Cloud Build to automatically trigger a build process when a new push is made to the master branch of our source repository. This will allow you to automatically deploy the application whenever a change is made to the source code and pushed to the repo.

In Cloud Build, click on **Triggers**, then connect Cloud Source Repository to it and find the **products-api** repository. Click on the **three dots** button on the right and select **Add Trigger**.

Configure the trigger by following the steps below:

1. Name the trigger as **products-api-trigger**.
2. Keep the option **"Push to a branch"** selected. 
3. In branch enter **^master$** as the branch regular expression. 
4. On Build configuration select **Cloud Build configuration file (yaml or json)** and keep the file named as **/cloudbuild.yaml**.
5. Click on **Add Variable** and add a substitution variable named **_VERSION** with value **1.0** and keep it as **User-defined**.
6. Finally click on **Create**.

It's important now to inspect what is done in **cloudbuild.yaml**. The following are the file contents for **cloudbuild.yaml**:

    steps:
    - name: 'gcr.io/cloud-builders/docker'
    args: [ 'build', '-t', 'gcr.io/$PROJECT_ID/products-api:${_VERSION}', '.' ]
    images:
    - 'gcr.io/$PROJECT_ID/products-api:${_VERSION}'

This file instructs Cloud Build to build a docker image using the Dockerfile present in the repository and then to push the generated Docker image to the Google Container Registry when done. This will happen when a new push is made to the repository in the master branch.

Now, as next step, do a test on pushing a change to the repository and check if the build is started automatically like seen below:

![Build history](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/01-build-history.png)

After the build is successful, check if the image is placed into the container registry:

![GCR](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/02-gcr.png)

# Configuring Spinnaker

When you install Spinnaker for GCP, Spinnaker comes pre-configured with a connection to Google Cloud Build's Pub/Sub topic in the same project it's installed in (and another one for the Google Container Registry topic). This is sufficient for the demonstration here. In real world scenarios you can add connection to different projects as Spinnaker will probably reside in a different project from your user cluster.

For GKE, a connection was created after installing Spinnaker in the beginning of this solution.

## Creating the Application and the Pipeline

The first step is to create an application in Spinnaker. For that, in Spinnaker console:

1. Click on **Actions**
2. Then on **Create Application**
3. Name the application as **products-api**
4. Inform your email as **Owner Email**

![New Application](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/03-new-app.png)

Now click on **Configure** to create a new pipeline:

1. Name it **products-api-pipeline**
2. Click **Create**

Now it's time to a trigger responsible to start the Continuous Delivery pipeline. 

To create a trigger:

1. On **Automated Triggers**, click on **Add Trigger**.

![New Trigger](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/04-trigger.png)

2. Select type as **Pub/Sub**
3. **Pub/Sub System Type** as **google**
4. **Subscription** name as **gcb-account**
5. **Payload Constraints** add a **Key** as **status** and **value** as **SUCCESS**. This will filter messages to process builds only when they are finished and successful.
6. Click on **Save Changes**.

![Configuring Trigger](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/05-new-trigger.png)

Now, do the following to test:

1. Go back to the GCP Console.
2. Click on **Cloud Build**.
3. Click on **Triggers**.
4. Click on **Run trigger**.

After the build is complete and successful, go back to Spinnaker and check if it has an execution of the pipeline. There should be an execution, showing the trigger is working fine:

![First execution](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/06-first-run.png)

### Extract Details From The Built Image

Get the image name and image digest fron the created image. These details will later help with the creation of an image url with the name and digest that is going to be used for signature and attestation creation and also the deployment. 

For that, do the following:

1. Add a new stage to the pipeline.
2. Change the type to **Evaluate Variables**.
3. Name the stage as **Get Image Details**.

![Get Image details](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/07-get-img-details.png)

Create a variable named imageName and point it to `${trigger.payload.results.images[0].name}`

Create a new one named imageDigest and point it to `${trigger.payload.results.images[0].digest}`

![Variables](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/08-vars.png)

1. Save and retest the pipeline running the trigger on Cloud Build again. 
2. Checking if variables were correctly extracted.

![Variable extraction](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/09-var-extract.png)

3. Now add a new variable named imageAndHash with the following content:

    `${trigger.payload.results.images[0].name.substring(0, trigger.payload.results.images[0].name.indexOf(":")) + "@" +
    trigger.payload.results.images[0].digest}`

4. The following result will be seen:

![Image and Hash Variable](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/10-image-and-hash.png)

Click on **Save Changes**.


### Creating the Attestation

Now it's time to create the attestation. From the binary authorization docs on what the attestation is: _"An attestation is a digitally signed document, made by a signer, that certifies that a required process in your pipeline was completed and that the resulting container image is authorized for deployment in GKE. The attestation itself contains the full path to the version of the container image as stored in your container image registry, as well as a signature created by signing the globally unique digest that identifies a specific container image build"_.

As Spinnaker can't run a script by itself, to create the attestation, you should rely on a Kubernetes Job running on top of the Spinnaker Kubernetes cluster. 

This job will have a script that will create the attestation along with the signature of the payload required by Binary Authorization.

Run the script with the Spinnaker Service Account. For it to work this service account needs permission in the project hosting the binary authorization artifacts. This ensures that the only party with permissions to access create the attestation is Spinnaker.

### Creating the Binary Authorization Job Docker Container Image

For that, the first step is to create a docker container based on the Google Cloud SDK base image and place that on Google Cloud Registry to be accessed by the Spinnaker Kubernetes cluster.

In a new directory containing the code for creating the attestation, create a script named `attest_image.sh` with the following content:

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

1. In the same directory, create a Dockerfile with the following code:

        FROM google/cloud-sdk:latest

        ADD attest_image.sh /opt/google/bin-authz/attest_image.sh

        RUN chmod +x /opt/google/bin-authz/attest_image.sh

2. Build the container image and push it to GCR by running these commands. The project id is the id of the project where Spinnaker is installed and where we will host this docker image:

        cd [DIRECTORY WHERE YOU HOSTED THE FILES]

        docker build . -t gcr.io/<PROJECT ID>/bin-authz-job
        
        docker push gcr.io/<PROJECT ID>/bin-authz-job


## Running the Job in Spinnaker

Go back to Spinnaker and add a new stage. Select as type **Run Job (Manifest)** and name it as **Create Attestation**.

![Create Attestation Job](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/11-create-attestation.png)

Select the **Account** as **spinnaker-install-account**. This is the kubernetes account for the **cluster where spinnaker is installed and comes pre-defined with Spinnaker for GCP**.

![Run Job Configuration](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/12-run-job.png)

Add the following text as the **Manifest Text** making the necessary changes to point to your project and replacing the other environment variables.

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

**It's important to note that the jobs will be hosted in the jobs namespace. You should connect manually to the Spinnaker's Kubernetes cluster and create this namespace previously.**

### Testing
Test the build by triggering the Cloud Build trigger manually in Cloud Console. After that, check if the Spinnaker pipeline was triggered.

The build should succeed and we should see two green steps:

![Success running job](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/13-run-job-steps.png)

And if you look at the console output for the Create Attestation phase, you should see the following output:

    Image to attest: gcr.io/<PROJECT ID>/products-api@<IMAGE HASH>
    Listed 0 items.
    Attestation list: 
    Attestation created

### Adding Permissions to Access Attestation Resources
The Service Account used by Spinnaker needs permissions to access the Attestor resources like Cloud KMS keys and to create the attestation. As they are in different projects the service account from Spinnaker's project should be added to the Attestor project and given the proper roles.

The first step is to get the name of the Spinnaker service account. For that, go to the Spinnaker GKE cluster in Cloud Console and click on **Permissions**.

The service account name will be shown in the following form:

    <account name>@<project id>.iam.gserviceaccount.com

Take note of the service account name and add permissions to the service account in the `Attestor` project, where we hold the Binary Authorization Attestor and also the Cloud KMS keys for signing the attestations:

* In Cloud Console, go to the **Attestor Project**.
* In the navigation menu click on **IAM & Admin** > **IAM**.
* Click the **Add** button to add an IAM permission.
* Enter the email of the Spinnaker Service account and add the following roles:
    * **Binary Authorization Attestor Editor**
    * **Binary Authorization Attestor Viewer**
    * **Binary Authorization Service Agent**
    * **Cloud KMS CryptoKey Signer/Verifier**
    * **Container Analysis Notes Editor**
    * **Container Analysis Occurrences Editor**
    * **Container Analysis Occurrences Viewer**

This will allow the job deployed to the Spinnaker Kubernetes Cluster to access the required resources and create the attestations in the Attestor project.


# Deploying the Application
Now that the attestation is created, the last step is to deploy the application. Deploying the application will also be applying a Kubernetes manifest. 

For that:

1. Add a new stage of type **Deploy (Manifest)** and name it **Deploy Application**.

![Add stage for App Deployment](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/14-deploy-app-stage.png)

2. **Select the account** you want to deploy to, which will be the account that was connected to Spinnaker representing the deployment cluster.

![Stage Config](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/15-manifest-config.png)

3. Enter the following as the deployment configuration **Manifest text** to deploy the application:

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

4. Test the deployment and check if the deployment was created successfully in Kubernetes and if the PODs are running. This will indicate that the binary authorization is working properly. 

![Deployment Success](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/16-three-steps-success.png)

![Deployment Success](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/17-deployment-ok.png)


## Deploying a Service

Last step in this journey will be to deploy a service capable of exposing a business API and testing it.

For that:

1. Add a parallel step to the **Deploy Application**, same type as the Deploy Application one, name it **Deploy Service**.

![Service Deployment](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/18-svc-deployment.png)

2. Configure the deployment text YAML as the following:

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

3. Retest the deployment by triggering it from Cloud Build.

4. Deployment should succeed with the deployment now of the service along with the application.

![Service Deployment Success](https://storage.googleapis.com/gcp-community/tutorials/spinnaker-binary-auth/19-svc-deployment-ok.png)

5. Execute a `kubectl get svc` in the user cluster to get the Load Balancer IP

6. Access using the browser the URL `http://<LB IP>/products` and you should get a list of dummy products, returned by our application.

# Summary

With this you've finished a full cycle of CI/CD. From source code triggering automatically a build with a Cloud Build trigger building the docker image and starting a Spinnaker pipeline capable of providing an image attestation to be deployed to a cluster with a Binary Authorization policy enabled.

Choosing if you are going to attest an image during build or deployment depends on your CI/CD architecture and the idea of this article was to give you the option of doing so during the deployment phase.
