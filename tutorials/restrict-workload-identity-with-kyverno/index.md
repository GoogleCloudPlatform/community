---
title: Restrict Google Kubernetes Engine Workload Identity with Kyverno
description: Learn how to configure Workload Identity on Google Kubernetes Engine (GKE) and how to use Kyverno to enforce identity security with policies.
author: soeirosantos
tags: gcp, gke, google kubernetes engine, workload identity, cloud-native security, policy management, policy engine, kyverno
date_published: 2021-04-21
---

Romulo Santos

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you create a Google Kubernetes Engine (GKE) cluster and configure Workload Identity to access Google Cloud services from applications running 
in the cluster. You use Kyverno, a Kubernetes policy engine, to enforce admission policies, which improves security and prevents configuration errors.

[Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) is the recommended way to access Google Cloud services from 
applications running within GKE due to its improved security properties and manageability. With Workload Identity, you can configure a Kubernetes service account 
to act as a Google service account. Pod resources running as the Kubernetes service account will automatically authenticate as the Google service account when 
accessing Google Cloud APIs.

Kyverno is a policy engine designed for Kubernetes. It runs as a
[dynamic admission controller](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) in a Kubernetes cluster, validating and
mutating admission webhook HTTP callbacks from the
[Kubernetes API server](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/). Kyverno applies matching policies to return results 
that enforce admission policies or reject requests. In this tutorial, you apply a cluster-wide policy to ensure that your Kubernetes service account can only be
used by a specific application in a specific namespace. For more information, see the [Kyverno documentation](https://kyverno.io/docs/).

## Before you begin

For this tutorial, you need a [Google Cloud project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new one, or select a project that you have already created.

1.  Create a [Google Cloud project](https://console.cloud.google.com/cloud-resource-manager).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for your project.
1.  For the commands in this tutorial, you use the `gcloud` command-line interface. To install the Cloud SDK, which includes the `gcloud` tool, follow
    [these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
*   [Cloud Storage](https://cloud.google.com/storage)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Preparing the GKE cluster

In this section, you create the basic resources, including a fictitious application with read access to a Cloud Storage bucket.

1.  Set some variables that are used throughout the tutorial (changing the values for your environment) and configure the Google Cloud project:

        gcp_project=[YOUR_PROJECT_NAME]
        cluster_name=[YOUR_CLUSTER_NAME]
        cluster_region=us-east1
        gcs_bucket_name="$gcp_project"_app-storage # appends the project name to prevent collision
        gsa_name=gcs-viewer-staging # the Google service account
        ksa_name=gcs-viewer # the Kubernetes service account

        gcloud config set project $gcp_project

    The Google service account is environment-aware and has limited access to the resources necessary for the application, ensuring the principle of least 
    privilege.

1.  Create the GKE cluster:

        gcloud beta container clusters create "$cluster_name" \
          --release-channel regular \
          --enable-ip-alias \
          --region "$cluster_region" \
          --workload-pool="${gcp_project}".svc.id.goog

1.  Check the Kubernetes configuration (kubeconfig):

        kubectl config current-context

1.  If your current context doesn't match the cluster that you just created, use the `get-credentials` command to configure your local access to the cluster:

        gcloud container clusters get-credentials "$cluster_name" --region "$cluster_region"

1.  Create the Google service account:

        gcloud iam service-accounts create "$gsa_name"

1.  Create the Cloud Storage bucket and write a file to it:

        gsutil mb -p $gcp_project gs://"$gcs_bucket_name"
        echo hello > my_application_file
        gsutil cp my_application_file gs://"$gcs_bucket_name"

1.  Grant the `objectViewer` role to the Google service account at the bucket level:

        gsutil iam ch serviceAccount:"$gsa_name"@"$gcp_project".iam.gserviceaccount.com:objectViewer gs://"$gcs_bucket_name"

    Alternatively, you could grant the role at the project level, but it's recommended to make the permission more constrained, according to the principle of
    least privilege.
    
    For more information, see [IAM roles for Cloud Storage](https://cloud.google.com/storage/docs/access-control/iam-roles).

## Configure and validate Workload Identity

In this section, you work on the Kubernetes cluster to configure and validate Workload Identity.

With the GKE Workload Identity feature, all Kubernetes service accounts that share a name, namespace, and workload identity pool resolve to the same
[IAM member](https://cloud.google.com/iam/docs/overview#concepts_related_identity) name, and therefore share access to Google Cloud resources.

1.  Create a namespace named `staging`:

        kubectl create namespace staging
        
    This simulates a staging environment.

1.  Create the Kubernetes service account:

        kubectl create serviceaccount "$ksa_name" -n staging

1.  Annotate your Kubernetes service account with the Google service account:

        kubectl annotate serviceaccount \
          "$ksa_name" \
          iam.gke.io/gcp-service-account="$gsa_name"@$gcp_project.iam.gserviceaccount.com \
          -n staging

1.  Allow the Kubernetes service account to impersonate the Google service account by creating an IAM policy binding between the two:

        gcloud iam service-accounts add-iam-policy-binding \
          --role roles/iam.workloadIdentityUser \
          --member "serviceAccount:${gcp_project}.svc.id.goog[staging/${ksa_name}]" \
          "$gsa_name"@"$gcp_project".iam.gserviceaccount.com
          
    This binding allows the Kubernetes service account to act as the Google service account.

1.  To test the configuration, create a Pod using the Kubernetes service account previously defined:

        kubectl run -it --rm --image google/cloud-sdk:slim bb8 \
          --serviceaccount "$ksa_name" \
          --env gcs_bucket_name="$gcs_bucket_name" \
          -n staging \
          --restart=Never
            
    This command creates a standalone Pod running the `google/cloud-sdk:slim` image to validate your configuration. In the real world, this would be your
    application image deployed through a [Kubernetes Workload Controller](https://kubernetes.io/docs/concepts/architecture/controller/) such as a
    [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/).

1.  From inside the container, run the following commands:

        gsutil cp gs://$gcs_bucket_name/my_application_file .
        cat my_application_file
        exit

    You should see the content that you wrote to Cloud Storage in a previous step, `hello`.

## Use Kyverno to restrict the workload identity

In this section, you use a Kyverno policy to restrict the usage of the Kubernetes service account in this namespace to a specific application. This tutorial
uses the `google/cloud-sdk:slim` image, but in practice you would replace this with your application's image.

1.  Install Kyverno in the GKE cluster:

        kubectl create -f https://raw.githubusercontent.com/kyverno/kyverno/main/definitions/release/install.yaml

    This tutorial uses the simplest way to install Kyverno to get it up and running quickly. For more information about installing, configuring, and customizing
    Kyverno, see the [Kyverno documentation](https://kyverno.io/docs/installation/).

1.  Create the Kyverno policy:

        kubectl create -f- << EOF
        apiVersion: kyverno.io/v1
        kind: ClusterPolicy
        metadata:
          name: staging-restrict-gcs-viewer-sa
          annotations:
            policies.kyverno.io/title: Restrict Cloud Storage Viewer service account in Staging
            policies.kyverno.io/category: Pod Security
            policies.kyverno.io/description: >-
              Restrict Pod resources in staging to use a known service account.
        spec:
          validationFailureAction: enforce
          rules:
          - name: require-service-account
            match:
              resources:
                kinds:
                - Pod
                namespaces:
                - staging
            validate:
              message: "Service account required"
              pattern:
                spec:
                  serviceAccountName: "?*"
                  containers:
                  # in a real world scenario this would be your app's image
                  - =(image): "google/cloud-sdk:slim"
          - name: validate-service-account
            match:
              resources:
                kinds:
                - Pod
                namespaces:
                - staging
            validate:
              message: "Invalid service account"
              pattern:
                spec:
                  =(serviceAccountName): "$ksa_name"
                  containers:
                  # in a real world scenario this would be your app's image
                  - =(image): "google/cloud-sdk:slim"
        EOF

    This policy validates that all Pod resources created in the `staging` namespace and using the `google/cloud-sdk:slim` image have a service account explicitly
    configured, and this service account should match the name of your Kubernetes service account. It also prevents Pod resources using other images from using
    this service account.

1.  Try to launch a Pod with a different image and your Kubernetes service account:

        kubectl run -it --rm --image alpine bb8 \
          --serviceaccount "$ksa_name" \
          --env gcs_bucket_name="$gcs_bucket_name" \
          -n staging \
          --restart=Never
          
    You should see the following output:

        Error from server: admission webhook "validate.kyverno.svc" denied the request:

        resource Pod/staging/bb8 was blocked due to the following policies

        staging-restrict-gcs-viewer-sa:
          require-service-account: 'validation error: Service account required. Rule require-service-account failed at path /spec/containers/0/image/'
          validate-service-account: 'validation error: Invalid service account. Rule validate-service-account failed at path /spec/containers/0/image/''

1.  Try to create a Pod with the default service account:

        kubectl run -it --rm --image google/cloud-sdk:slim bb8 \
          --env gcs_bucket_name="$gcs_bucket_name" \
          -n staging \
          --restart=Never
          
    You should see the following output:

        Error from server: admission webhook "validate.kyverno.svc" denied the request:

        resource Pod/staging/bb8 was blocked due to the following policies

        staging-restrict-gcs-viewer-sa:
          validate-service-account: 'validation error: Invalid service account. Rule validate-service-account failed at path /spec/serviceAccountName/'

1.  Run the original command to verify that the admission controller allows the Pod creation:

        kubectl run -it --rm --image google/cloud-sdk:slim bb8 \
          --serviceaccount "$ksa_name" \
          --env gcs_bucket_name="$gcs_bucket_name" \
          -n staging \
          --restart=Never

To learn more about how to adapt and extend this policy to match different criteria, see the
[Kyverno Write Policies documentation](https://kyverno.io/docs/writing-policies/).

## Optional: Restrict the Kubernetes service account annotation to the Google service account

In this section, you create a policy to restrict that the Kubernetes service account so that it can only be annotated with your Google service account. This
policy also prevents other Kubernetes service accounts in this namespace from being annotated with your Google service account.

1.  Remove the existing Kubernetes service account:

        kubectl delete sa $ksa_name -n staging

1.  Create the policy:

        kubectl create -f- << EOF
        apiVersion: kyverno.io/v1
        kind: ClusterPolicy
        metadata:
          name: staging-restrict-gcs-viewer-sa-annotation
          annotations:
            policies.kyverno.io/title: Restrict Workload Identity Annotation Staging
            policies.kyverno.io/category: Pod Security
            policies.kyverno.io/description: >-
              Restrict the Object Viewer service account to be annotated with the
              corresponding Google service account in Staging
        spec:
          validationFailureAction: enforce
          rules:
          - name: validate-annotation
            match:
              resources:
                kinds:
                - ServiceAccount
                namespaces:
                - staging
            validate:
              message: "Invalid workload identity annotation"
              pattern:
                metadata:
                  =(name): $ksa_name
                  annotations:
                    =(iam.gke.io/gcp-service-account): $gsa_name@$gcp_project.iam.gserviceaccount.com
        EOF

1.  Try to create the service account:

        kubectl create serviceaccount "$ksa_name" -n staging
        
    You should see the following output:

        Error from server: admission webhook "validate.kyverno.svc" denied the request:

        resource ServiceAccount/staging/gcs-viewer was blocked due to the following policies

        staging-restrict-gcs-viewer-sa-annotation:
          validate-annotation: 'validation error: Invalid workload identity annotation. Rule validate-annotation failed at path /metadata/annotations/'

    Using the initial approach (create then annotate) won't work because now the Kubernetes service account is required to have the
    `iam.gke.io/gcp-service-account` annotation with the specified value.

1.  Try to create the service account with a wrong value:

        kubectl create -f- << EOF
        apiVersion: v1
        kind: ServiceAccount
        metadata:
          name: "$ksa_name"
          namespace: staging
          annotations:
            iam.gke.io/gcp-service-account: foo@$gcp_project.iam.gserviceaccount.com
        EOF

    You should see the following output:

        Error from server: error when creating "STDIN": admission webhook "validate.kyverno.svc" denied the request:

        resource ServiceAccount/staging/gcs-viewer was blocked due to the following policies

        staging-restrict-gcs-viewer-sa-annotation:
          validate-annotation: 'validation error: Invalid workload identity annotation. Rule validate-annotation failed at path /metadata/annotations/iam.gke.io/gcp-service-account/'

1.  Create the service account with the proper annotation:

        kubectl create -f- << EOF
        apiVersion: v1
        kind: ServiceAccount
        metadata:
          name: "$ksa_name"
          namespace: staging
          annotations:
            iam.gke.io/gcp-service-account: $gsa_name@$gcp_project.iam.gserviceaccount.com
        EOF

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, remove the following resources:

1.  Delete the GKE cluster:

        gcloud container clusters delete "$cluster_name" --region "$cluster_region"

1.  Delete the Google service account:

        gcloud iam service-accounts delete "$gsa_name"@"$gcp_project".iam.gserviceaccount.com

1.  Delete the Cloud Storage bucket:

        gsutil rm  gs://"$gcs_bucket_name"/my_application_file
        gsutil rb gs://"$gcs_bucket_name"

If you created a project specifically for this tutorial, you can remove it in the [Resource Manager](https://console.cloud.google.com/cloud-resource-manager).
