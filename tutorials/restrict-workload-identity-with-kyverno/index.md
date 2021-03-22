---
title: Restricting GKE Workload Identity with Kyverno
description: Learn how to configure Workload Identity on GKE and how to use Kyverno to enforce identity security with policies.
author: soeirosantos
tags: gcp, gke, google kubernetes engine, workload identity, cloud-native security, policy management, policy engine, kyverno
date_published: 2021-03-21
---

Romulo Santos

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, we are going to create a GKE cluster and configure [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) to access Google Cloud services from applications running within the cluster. Then we will use Kyverno, a Kubernetes policy engine, to enforce the workload identity, which will improve security and prevent configuration errors.

## Workload Identity

From the [GKE documentation](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity):

> Workload Identity is the recommended way to access Google Cloud services from applications running within GKE due to its improved security properties and manageability. [...] With Workload Identity, you can configure a Kubernetes service account to act as a Google service account. Pod resources running as the Kubernetes service account will automatically authenticate as the Google service account when accessing Google Cloud APIs.

## Kyverno

Kyverno is a policy engine designed for Kubernetes. It runs as a [dynamic admission controller](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) in a Kubernetes cluster validating and mutating admission webhook HTTP callbacks from the kube-apiserver. Kyverno applies matching policies to return results that enforce admission policies or reject requests. In this tutorial, we are going to apply a cluster-wide policy to ensure that our Kubernetes Service Account can only be used by a specific application in a particular namespace. For more details about Kyverno, check the [official docs](https://kyverno.io/docs/).

## Before you begin

For this tutorial, you need a [Google Cloud project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a new one, or select a project that you have already created.

1.  Create a [Google Cloud project](https://console.cloud.google.com/cloud-resource-manager).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for your project.
1.  For the commands in this tutorial, you will use the `gcloud` command-line interface. To install the Cloud SDK, which includes the `gcloud` tool, follow [these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
*   [Cloud Storage](https://cloud.google.com/storage)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Preparing the GKE cluster

Let's get started creating the basic resources needed.

1. Set some variables that will be used throughout the tutorial (change the values accordingly) and configure the GCP project.

        gcp_project=your-project
        cluster_name=your-cluster
        cluster_region=us-east1
        gcs_bucket_name="$gcp_project"_app-storage # append the project name to prevent collision
        gsa_name=gcs-viewer-staging # the Google Service Account
        ksa_name=gcs-viewer # the Kubernetes Service Account

        gcloud config set project $gcp_project

    Notice that the Google Service Account (GSA) is environment aware and will have limited access only to the resources necessary to the application, ensuring the principle of least privilege.

1. Create the GKE cluster.

        gcloud beta container clusters create "$cluster_name" \
            --release-channel regular \
            --enable-ip-alias \
            --region "$cluster_region" \
            --workload-pool="${gcp_project}".svc.id.goog

1. You shoud have your kubeconfig configured. Check with:

        kubectl config current-context

1. If your current context doesn't match the cluster you just created use the `get-credentials` command to configure your local access to the cluster.

        gcloud container clusters get-credentials "$cluster_name" --region "$cluster_region"

1. Create the Google Service Account.

        gcloud iam service-accounts create "$gsa_name"

1. In our example we are going to consider a fictitious application that requires read access to a GCS bucket. So, let's create the bucket and write a file to it:

        gsutil mb -p $gcp_project gs://"$gcs_bucket_name"
        echo foo > my_application_file
        gsutil cp my_application_file gs://"$gcs_bucket_name"

1. Grant the `objectViewer` role to the Google Service Account at the bucket level. See the [Cloud Storage roles doc](https://cloud.google.com/storage/docs/access-control/iam-roles) for more details about IAM roles for Cloud Storage.

        gsutil iam ch serviceAccount:"$gsa_name"@"$gcp_project".iam.gserviceaccount.com:objectViewer gs://"$gcs_bucket_name"

    Notice that, alternatively, we could grant the role at the project level but remember that we want to keep the least privilege.

## Configure and validate the Workload Identity

Now we are going to work on the Kubernetes cluster to configure and validate the workload identity.

With the GKE Workload Identity feature, all Kubernetes service accounts that share a name, namespace name, and workload identity pool resolve to the same [IAM member](https://cloud.google.com/iam/docs/overview#concepts_related_identity) name, and therefore share access to Google Cloud resources. In the next steps we are going to configure the workload identity:

1. Create a namespace named `staging`. This simulates a staging environment.

        kubectl create namespace staging

1. Create the Kubernetes Service Account (KSA).

        kubectl create serviceaccount "$ksa_name" -n staging

1. Annotate your Kubernetes Service Account with the Google Service Account.

        kubectl annotate serviceaccount \
            "$ksa_name" \
            iam.gke.io/gcp-service-account="$gsa_name"@$gcp_project.iam.gserviceaccount.com \
            -n staging

1. Now we need to allow the Kubernetes service account to impersonate the Google service account by creating an IAM policy binding between the two. This binding allows the Kubernetes service account to act as the Google service account.

        gcloud iam service-accounts add-iam-policy-binding \
            --role roles/iam.workloadIdentityUser \
            --member "serviceAccount:${gcp_project}.svc.id.goog[staging/${ksa_name}]" \
            "$gsa_name"@"$gcp_project".iam.gserviceaccount.com

1. We are ready to test the configuration. Create a Pod using the KSA previously defined. For the purposes of this tutorial, we are going to use a standalone Pod running the `google/cloud-sdk:slim` image to validate our configuration. In the real world this would be your application image deployed through a [Kubernetes Workload Controller](https://kubernetes.io/docs/concepts/architecture/controller/) such as a [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/).

        kubectl run -it --rm --image google/cloud-sdk:slim bb8 \
            --serviceaccount "$ksa_name" \
            --env gcs_bucket_name="$gcs_bucket_name" \
            -n staging \
            --restart=Never

1. From inside the container run:

        root@bb8:/# gsutil cp gs://$gcs_bucket_name/my_application_file .
        root@bb8:/# cat my_application_file
        root@bb8:/# exit

    You should see the content we wrote to GCS in a previous step, "foo".

## Using Kyverno to restrict the workload identity

Now we are going to use a Kyverno policy to restrict the usage of the Kubernetes service account in this namespace to a specific application. Remember that for the purpose of this tutorial we are using the `google/cloud-sdk:slim` image but in a real situation, we would replace this with our application's image.

1. Start installing Kyverno in the GKE cluster.

        kubectl create -f https://raw.githubusercontent.com/kyverno/kyverno/main/definitions/release/install.yaml

    In this tutorial we are using the simplest way to install Kyverno to get it up and running quickly. Check the [Kyverno Installation docs] for more details about how to install, configure and customize Kyverno.

1. Create the Kyverno policy.

        kubectl create -f- << EOF
        apiVersion: kyverno.io/v1
        kind: ClusterPolicy
        metadata:
          name: staging-restrict-gcs-viewer-sa
          annotations:
            policies.kyverno.io/title: Restrict GCS Viewer Service Account in Staging
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

    This policy validates that all Pod resources created in the `staging` namespace and using the `google/cloud-sdk:slim` image will have a service account explicitly configured and this service account should match the name of our KSA. It also prevents that Pod resources using other images use this service account.

1. Let's start trying to launch a Pod with a different image and our Kubernetes service account.

        kubectl run -it --rm --image alpine bb8 \
            --serviceaccount "$ksa_name" \
            --env gcs_bucket_name="$gcs_bucket_name" \
            -n staging \
            --restart=Never

        Error from server: admission webhook "validate.kyverno.svc" denied the request:

        resource Pod/staging/bb8 was blocked due to the following policies

        staging-restrict-gcs-viewer-sa:
          require-service-account: 'validation error: Service account required. Rule require-service-account failed at path /spec/containers/0/image/'
          validate-service-account: 'validation error: Invalid service account. Rule validate-service-account failed at path /spec/containers/0/image/''

1. Now let's try to create a Pod with the default service account.

        kubectl run -it --rm --image google/cloud-sdk:slim bb8 \
            --env gcs_bucket_name="$gcs_bucket_name" \
            -n staging \
            --restart=Never

        Error from server: admission webhook "validate.kyverno.svc" denied the request:

        resource Pod/staging/bb8 was blocked due to the following policies

        staging-restrict-gcs-viewer-sa:
          validate-service-account: 'validation error: Invalid service account. Rule validate-service-account failed at path /spec/serviceAccountName/'

1. Finally, run our original command to verify that the admission controller will allow the Pod creation.

        kubectl run -it --rm --image google/cloud-sdk:slim bb8 \
            --serviceaccount "$ksa_name" \
            --env gcs_bucket_name="$gcs_bucket_name" \
            -n staging \
            --restart=Never

    To learn more about how we can adapt and extend this policy to match different criteria check the [Kyverno Write Policies documentation](https://kyverno.io/docs/writing-policies/).

## Bonus: Restrict the Kubernetes service account annotation to the Google service account

Let's create a policy to restrict that the Kubernetes service account could be created/annotated with a different Google service account.

1. Remove the existing KSA.

        kubectl delete sa $ksa_name -n staging

1. Create the policy.

        kubectl create -f- << EOF
        apiVersion: kyverno.io/v1
        kind: ClusterPolicy
        metadata:
          name: staging-restrict-gcs-viewer-sa-annotation
          annotations:
            policies.kyverno.io/title: Restrict Workload Identity Annotation Staging
            policies.kyverno.io/category: Pod Security
            policies.kyverno.io/description: >-
              Restrict the Object Viewer Service Account to be annotated with the
              corresponding Google Service Account in Staging
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
                name: "$ksa_name"
            validate:
              message: "Invalid workload identity annotation"
              pattern:
                metadata:
                  annotations:
                    =(iam.gke.io/gcp-service-account): $gsa_name@$gcp_project.iam.gserviceaccount.com
        EOF

1. Try to create the service account.

        kubectl create serviceaccount "$ksa_name" -n staging

        Error from server: admission webhook "validate.kyverno.svc" denied the request:

        resource ServiceAccount/staging/gcs-viewer was blocked due to the following policies

        staging-restrict-gcs-viewer-sa-annotation:
          validate-annotation: 'validation error: Invalid workload identity annotation. Rule validate-annotation failed at path /metadata/annotations/'

    Using our initial approach (create then annotate) won't work because now the KSA is required to have the `iam.gke.io/gcp-service-account` annotation with the specified value.

1. Try to create the service account with a wrong value.

        kubectl create -f- << EOF
        apiVersion: v1
        kind: ServiceAccount
        metadata:
          name: "$ksa_name"
          namespace: staging
          annotations:
            iam.gke.io/gcp-service-account: foo@$gcp_project.iam.gserviceaccount.com
        EOF

        Error from server: error when creating "STDIN": admission webhook "validate.kyverno.svc" denied the request:

        resource ServiceAccount/staging/gcs-viewer was blocked due to the following policies

        staging-restrict-gcs-viewer-sa-annotation:
          validate-annotation: 'validation error: Invalid workload identity annotation. Rule validate-annotation failed at path /metadata/annotations/iam.gke.io/gcp-service-account/'

1. Finally, create the service account with the proper annotation

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

1. Delete the GKE cluster

        gcloud container clusters delete "$cluster_name" --region "$cluster_region"

1. Delete the Google Service Account

        gcloud iam service-accounts delete "$gsa_name"@"$gcp_project".iam.gserviceaccount.com

1. Delete the Cloud Storage Bucket

        gsutil rm  gs://"$gcs_bucket_name"/my_application_file
        gsutil rb gs://"$gcs_bucket_name"

If you created a project specifically for this tutorial you can remove it by using the [Resource Manager](https://console.cloud.google.com/cloud-resource-manager).
