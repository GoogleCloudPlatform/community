---
title: Use webhooks to trigger a central Cloud Build pipeline from multiple Git repositories
description: Learn how to trigger a centrally managed Cloud Build pipeline with a webhook.
author: gmogr,MrTrustor
tags: cloudbuild, cicd, webhooks
date_published: 2022-01-21
---

Grigory Movsesyan | Cloud Engineer | Google

Théo Chamley | Cloud Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you build a centrally managed Cloud Build pipeline step by step. Using webhook triggers, you also trigger builds from a source code repository,
which is not natively supported by Cloud Build. One example of why a setup like this is useful is a Terraform automation pipeline. Terraform typically uses 
powerful service accounts to apply changes to the infrastructure. In this scenario, you might want to control exactly which commands are executed in the 
pipeline, and therefore to keep the automation pipeline code separate from the Terraform code.

To achieve this result, you need a pipeline that follows these steps:

1. When a developer pushes a code change to the repository, it triggers the build pipeline with a webhook.
2. The build pipeline receives the Git repository URL from the webhook event.
3. The build pipeline clones the Git repository.
4. The build pipeline applies the code changes.

![pipeline_schema](https://storage.googleapis.com/gcp-community/tutorials/using-cloudbuild-with-webhooks/schema.png)

You use GitLab in this tutorial, but you can apply the same principles to other source code repositories.

## Costs

This tutorial uses the following billable components of Google Cloud:

*   Cloud Build
*   Cloud Storage
*   Secret Manager

To generate a cost estimate based on your projected usage, use the [pricing calculator](https://cloud.google.com/products/calculator).

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created. For details, see the "Cleaning up"
section at the end of this tutorial.

## Prerequisites

This tutorial uses a sample Git repository on GitLab. If you don’t already have an account on GitLab, you can
[create an account for free on GitLab](https://gitlab.com/users/sign_up).

## Before you begin

1.  Select or create a Google Cloud project.

    To select or create a project, go to the [Manage resources page](https://console.cloud.google.com/cloud-resource-manager) in the Google Cloud Console.
    
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

1.  Open [Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

1.  In Cloud Shell, set the working project with the following command:

        gcloud config set project [PROJECT_ID]
        
    Replace `[PROJECT_ID]` with your project ID.

1.  Enable the APIs needed for this tutorial:

        gcloud services enable \
          cloudbuild.googleapis.com \
          secretmanager.googleapis.com 

1.  [Sign in to GitLab.](https://gitlab.com/users/sign_in)

1.  In GitLab, fork the [sample repository](https://gitlab.com/mogr/cloudbuild-webhooks):

    1.  Click the **Fork** button.
    1.  Select your personal namespace in the **Project URL** field.
    1.  Select **Private** as the visibility level.
    1.  Click **Fork project**.

## Create a webhook Cloud Build trigger

1.  In the Cloud Console, go to the [Triggers page](https://console.cloud.google.com/cloud-build/triggers).

1.  Click **Create Trigger**.

1.  Enter `webhook-trigger` in the **Name** field.

1.  Choose **Webhook event** for the **Event** field.

1.  Choose **Create new** in the **Secret** field, and click **Create Secret**.

1.  Enter `webhook-trigger-secret` in the **Secret name** field, and click **Create Secret**.

1.  Click **Create**.

## Configure the GitLab repository webhook

1.  Go to the [Triggers](https://console.cloud.google.com/cloud-build/triggers) page.

1.  Click the `webhook-trigger` trigger.

1.  Click **Show URL preview** and copy the webhook URL.

1.  On GitLab, click **Settings** in your forked GitLab repository.

1.  Click **webhooks**.

1.  Insert the URL that you copied in step 3 in the **URL** field.

1.  Click **Add webhook**.

You can learn more about creating webhooks in the [GitLab documentation](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html).

## Test the webhook

1.  In your GitLab repository, click **settings**, and then click **webhooks**.

1.  At the bottom of the page, find the **Project Hooks** block with the new webhook.

1.  Next to your webhook, click **Test** and choose **Push events**.

    This triggers the Cloud Build job.

1.  Go to the [Cloud Build history page](https://console.cloud.google.com/cloud-build/builds) to see the Cloud Build job running.

1.  Find the build with `webhook-trigger` as **Trigger name** that is running or ran recently and click it. You should see `“hello world”` in the build log.

## Get the repository URL from the push event

To be able to fetch the source code from the repository, you first need to get the repository URL from the
[event payload](https://cloud.google.com/build/docs/configuring-builds/use-bash-and-bindings-in-substitutions#creating_substitutions_using_payload_bindings).

1.  Go to the [Triggers page](https://console.cloud.google.com/cloud-build/triggers) for your Google Cloud project.

1.  Click the `webhook-trigger` trigger.

1.  In the **Configuration** block, click **Open editor**.

1.  In the right panel, modify the inline build config like the following:

        steps:
          - name: ubuntu
            args:
              - echo
              - ${_GIT_REPO}
        substitutions:
          _GIT_REPO: $(body)

1.  Click **Done**, and then click **Save**.

1.  Trigger the test push event from the GitLab repository again.

1.  Go to the [Cloud Build history page](https://console.cloud.google.com/cloud-build/builds) to see your new job running.

1.  Click the new job.

    Instead of the `“hello world”` line, you should see a JSON object with the content of the event payload. There are two fields of particular interest: 
    `project.git\_http\_url` and `project.git\_ssh\_url`. This tutorial uses a token for the authorization, so it focuses on the `project.git\_http\_url` field.

1.  In the Cloud Build trigger configuration, modify the inline build config again to display only the necessary field from the event payload:

        steps: 
          - name: ubuntu 
            args: 
              - echo 
              - '${_GIT_REPO}' 
        substitutions: 
          _GIT_REPO: $(body.project.git_http_url)

1.  Trigger the test push event from GitLab again.

    On the [Cloud Build history page](https://console.cloud.google.com/cloud-build/builds), you should see the line with the GitLab HTTP URL.  

## Clone the GitLab repository

You can clone a GitLab repository using tokens or using an SSH key. In this tutorial, you clone the repository using a token. For details of the SSH option, see
[Building repositories from GitLab](https://cloud.google.com/build/docs/automating-builds/build-hosted-repos-gitlab).

To be able to clone the GitLab repository, you first need to create the GitLab deploy token.

1.  In GitLab, click **Settings** and choose **Repository**.
1.  Click **Expand** next to **Deploy tokens**.
1.  Enter `cloudbuild` in the **Name** field.
1.  Enter `gitlab-token` in the **Username** field.
1.  Select **read\_repository** in **Scopes**.
1.  Click **Create deploy token**.
1.  Copy the token value.

    For more information, see [Deploy tokens](https://docs.gitlab.com/ee/user/project/deploy_tokens/) in the GitLab documentation.

1.  Modify the Cloud Build trigger inline config again, replacing `[GITLAB_TOKEN]` with actual value of the token in the line with the `git clone` command.

        steps: 
          - name: gcr.io/cloud-builders/git 
            args: 
              - '-c' 
              - 'git clone https://gitlab-token:[GITLAB_TOKEN]@${_REPO_URL}'
            entrypoint: bash 
        substitutions: 
          _GIT_REPO: $(body.project.git_http_url) 
          _REPO_URL: '${_GIT_REPO##https://}'

    The parameter `project.git\_http\_url` from the event payload already contains the protocol: `https://<git\_url>`. You need to insert the token after the 
    protocol but before the actual URL. To achieve this, you remove the protocol from the string and then build the URL again using
    [bash parameter extension](https://cloud.google.com/build/docs/configuring-builds/use-bash-and-bindings-in-substitutions#bash_parameter_expansions).

1.  To test the new trigger config, trigger the test push event from GitLab.

    You should see the repository successfully cloned in the build logs on the Cloud Build history page.

## Move the GitLab token to Secret Manager

For security reasons, you should not store the GitLab token in plaintext in the inline Cloud Build config. In this section, you move the token to Google Cloud 
Secret Manager.

1.  Go to the [Secret Manager page](https://console.cloud.google.com/security/secret-manager).

1.  Click **Create secret**.

1.  Enter `gitlab-token` in the **Name** field.

1.  Copy the GitLab token into the **Secret value** field.

1.  Click **Create secret** to create the secret.

## Give the Cloud Build service account access to the secret value

To access the secret value, the Cloud Build service account needs the `secretmanager.versions.access` role.

1.  Go to the [IAM & Admin page](https://console.cloud.google.com/iam-admin/iam) in the Cloud Console.

1.  Find the Cloud Build service account with the name `<project\_number>@cloudbuild.gserviceaccount.com` and click **Edit member**.

1.  Click **Add another role**.

1.  Add the Secret Manager Secret Accessor role.

1.  Click **Save**.

1.  Modify the Cloud Build inline config to read the token value from Secret Manager:

        steps: 
          - name: gcr.io/cloud-builders/git 
            args: 
              - '-c' 
              - 'git clone https://gitlab-token:$$GITLAB_TOKEN@${_REPO_URL} repo'
            entrypoint: bash
            secretEnv:
             - GITLAB_TOKEN
        substitutions:
          _GIT_REPO: $(body.project.git_http_url)
          _REPO_URL: '${_GIT_REPO##https://}'
        availableSecrets:
          secretManager:
            - versionName: 'projects/${PROJECT_ID}/secrets/gitlab-token/versions/latest'
              env: GITLAB_TOKEN

1.  Test the new Cloud Build config by triggering a test push event from GitLab.

## Apply the Terraform config

In this section, you execute the Terraform code from the Git repository.

1.  Create a Cloud Storage bucket to store Terraform state:

    1.  Go to the [Cloud Storage page](https://console.cloud.google.com/storage/browser) in the Cloud Console.
    1.  Click **Create bucket**.
    1.  In the **Name your bucket** field enter `tf-state-[PROJECT_ID]`, replacing `[PROJECT_ID]` with your actual project ID.
    1.  Click **Create**.

1.  Modify the inline Cloud Build config as follows:

        steps:
          - name: gcr.io/cloud-builders/git
            args:
              - '-c'
              - 'git clone https://gitlab-token:$$GITLAB_TOKEN@${_REPO_URL} repo'
            entrypoint: bash
            secretEnv:
              - GITLAB_TOKEN
          - name: hashicorp/terraform
            args:
              - init
              - '-backend-config=bucket=${_TF_BACKEND_BUCKET}'
              - '-backend-config=prefix=${_TF_BACKEND_PREFIX}'
            dir: repo
          - name: hashicorp/terraform
            args:
              - plan
              - '-var=project=${PROJECT_ID}'
              - '-out=/workspace/tfplan-$BUILD_ID'
            dir: repo
          - name: hashicorp/terraform
            args:
              - apply
              - '-auto-approve'
              - /workspace/tfplan-$BUILD_ID
            dir: repo
        substitutions:
          _GIT_REPO: $(body.project.git_http_url)
          _REPO_URL: '${_GIT_REPO##https://}'
          _TF_BACKEND_BUCKET: 'tf-state-${PROJECT_ID}'
          _TF_BACKEND_PREFIX: tf-state-prefix
        availableSecrets:
          secretManager:
            - versionName: 'projects/${PROJECT_ID}/secrets/gitlab-token/versions/latest'
              env: GITLAB_TOKEN

1.  Trigger a test push event in your GitLab repository.

1.  Go to the [Cloud Storage page](https://console.cloud.google.com/storage/browser) and observe that there is a bucket called `test-bucket-[PROJECT_ID]`.

After you have followed these steps, whenever you push changes to the Terraform repository, you also trigger the Cloud Build pipeline, which deploys changes to
your project. If you decide to add another Terraform project to the same pipeline, you only need to add a webhook to the repository.

## Cleaning up

You can clean up all of the resources created in this tutorial by
[shutting down the project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#shutting_down_projects). However, if you used an existing
project that contains resources other than those created in this tutorial, you can remove the resources created in this tutorial instead:

1.  In Cloud Shell set the `PROJECT_ID` environment variable:

        export PROJECT_ID=$(gcloud config get-value project)

1.  Delete the Cloud Build trigger:

        gcloud beta builds triggers delete webhook-trigger

1.  Delete the secret and token from Secret Manager:

        gcloud secrets delete webhook-trigger-secret
        gcloud secrets delete gitlab-token

1.  Delete the IAM policy:

        gcloud projects remove-iam-policy-binding ${PROJECT_ID} \
          --member=serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com \
          --role=roles/secretmanager.secretAccessor

1.  Delete the Cloud Storage buckets:

        gsutil rm -r gs://test-bucket-${PROJECT_ID}
        gsutil rm -r gs://tf-state-${PROJECT_ID}

1.  Delete the deploy token key from your repository:

    1.  In GitLab, click **Settings** and choose **Repository**.
    1.  Click **Expand** next to **Deploy tokens**.
    1.  In the **Active deploy tokens** block, find the `cloudbuild` token and click **Revoke**.

1.  Delete the GitLab repository:

    1. In your GitLab repository, click **Settings**, and then click **General**.
    1. Click **Expand** next to **Advanced**.
    1. At the bottom of the page, click **Delete project**.
    1. Confirm deletion by typing the repository name and clicking **Yes, delete project**.
