---
title: Mirroring an Azure DevOps repository to Cloud Source Repositories
description: Learn how to set up mirroring from an Azure DevOps repository to Cloud Source Repositories.
author: manokhina
tags: Repositories
date_published: 2021-03-05
---

Anastasiia Manokhina | Strategic Cloud Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to set up mirroring from an Azure DevOps repository to Cloud Source Repositories.

## Costs

This tutorial uses billable components of Google Cloud, including Cloud Source Repositories. (Check the
[free usage limits](https://cloud.google.com/source-repositories/pricing).)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.  

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new one, or select a project that you have already created.

1.  Create a Google Cloud project.
1.  Enable billing for the project.
1.  Enable the [Cloud Source Repositories API](https://cloud.google.com/source-repositories/docs/apis).

On the Azure side, you need to have an Azure DevOps account and an [Azure DevOps project](https://azure.microsoft.com/en-gb/features/devops-projects/).

## Initial setup

1.  Install the [Mirror Git Repository extension](https://marketplace.visualstudio.com/items?itemName=swellaby.mirror-git-repository) for your Azure
    organization.
1.  In the Google Cloud Console, [open Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell#starting_a_new_session).
1.  In Cloud Shell, create the Git repository in Cloud Source Repositories that will be the mirror of the Azure repository:  

        gcloud source repos create azure-csr-mirror

## Generating static credentials

In order for Azure Repos to push to your Git repository to Cloud Source Repositories, you must complete an OAuth 2.0 authorization flow to generate static
credentials for Cloud Source Repositories.

**Important**: The generated credentials are tied to the Google Account used to create them. Mirroring stops working if the Google Account is closed or loses 
access rights to the Git repository in Cloud Source Repositories.

1.  In Cloud Source Repositories, go to the [All Repositories](https://source.cloud.google.com/repos) page.
1.  Click the name of your repository.
1.  On the **Add code to your repository** page, under **Select your preferred authentication method**, select **Manually generated credentials**, and then click
    **Generate and store your Git credentials**.
    
    ![image](https://storage.googleapis.com/gcp-community/tutorials/azure-mirroring-tutorial/add_code.png)
    
    The Cloud Source Repositories site (`https://source.developers.google.com`), which identifies itself as **Google Cloud Development**, requests the 
    credentials on your behalf.
    
1.  Choose your Google Account in the **Sign in with Google** dialog:
    
    ![image](https://storage.googleapis.com/gcp-community/tutorials/azure-mirroring-tutorial/choose_account.png)
    
    The following dialog appears, requesting permission to view and manage your data. 

    ![image](https://storage.googleapis.com/gcp-community/tutorials/azure-mirroring-tutorial/signin.png)

1.  If you agree to the request for access, click **Allow**.

1.  On the **Configure Git** page, note the `git-[USERNAME]` and the highlighted text area. This will be the token used in the next steps.  
    
    ![image](https://storage.googleapis.com/gcp-community/tutorials/azure-mirroring-tutorial/configure_git.png)

## Creating an Azure pipeline

1.  In the project containing the repository, select **Pipelines**.

1.  Select **Create pipeline**.

1.  Select **Use the classic editor** to create a pipeline without YAML.

1.  Select **Azure Repos Git** as a source for code. Click **Continue**.

1.  At the top of the page, select **Empty job** as a template. 

1.  Rename the pipeline to **Clone to Cloud Source Repo**.

1.  Click **+** Next to **Agent job 1** to add the task. Find the **Mirror Git Repository** task and add it to the pipeline.

1.  Click the task in the left pane. Change its display name if needed.

1.  In the **Source Git Repository** field, paste the link to your Azure repository: 
    `https://dev.azure.com/[YOUR_ORGANIZATION]/[PROJECT_NAME]/_git/[PROJECT_NAME]`

1.  A personal access token (PAT) is used as an alternative password to authenticate into Azure DevOps. In the **Source Repository - Personal Access Token** 
    field, paste the token created using the procedure in the 
    [Use personal access tokens](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=preview-page#create-personal-access-tokens-to-authenticate-access)
    article.

1.  In the **Destination Git Repository** field, paste the URL of your repository in Cloud Source Repositories:
    `https://source.developers.google.com/p/[PROJECT_ID]/r/[REPOSITORY_NAME]`

1.  Get the username and the token generated in the **Configure Git** section in Cloud Source Repositories and insert it to the
    **Destination personal access token** field as follows:
    
        git-[USERNAME]:[TOKEN]
        
    In the token, replace the slash signs with its encoded variant, `%2F`. So if your username is `user` and your token starts with `1//...`, the token to
    be inserted is the following: `git-user:1%2F%2F...`
    
1.  Click **Save & Queue**.

1.  Optionally, add a comment.

1.  Click **Save & Run**.

1.  You are redirected to the pipeline page, where you can see your job running in the **Jobs** tab. When it finishes running, you will see the status 
    **Success** near the job name. 
1.  In Cloud Source Repositories, go to the [**All repositories** page](https://source.cloud.google.com/repos).
1.  Click the name of your repository, which in this example is `azure-csr-mirror`.
1.  Click to the `main` branch. The files and commit history from the original repository should appear.

   **Note**: If you want to do this regularly, note that service account keys expire after 30 days. Ensure that there is an established process of 
   maintaining and regular rotation of keys.

## Cleaning up

### Deleting the project

The easiest way to eliminate billing and avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete the project 
that you created for the tutorial:

1. In the Cloud Console, [go to the **Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project that you want to delete, and then click **Delete**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

### Revoking the credentials

If you want to revoke the generated credentials, go to the [Apps with access to your account](https://myaccount.google.com/permissions) page under your Google 
Account, select **Google Cloud Development**, and click **Remove access**.

## What's next

-  Learn how to
   [mirror a GitHub or Bitbucket repository to Cloud Source Repositories](https://cloud.google.com/source-repositories/docs/connecting-hosted-repositories).
-  Read [Cloud Source Repositories how-to guides](https://cloud.google.com/source-repositories/docs/how-to).
-  Explore [Cloud Source Repositories quickstarts](https://cloud.google.com/source-repositories/docs/quickstarts).
-  Learn how to
   [mirror a GitLab repository to Cloud Source Repositories](https://cloud.google.com/solutions/mirroring-gitlab-repositories-to-cloud-source-repositories).
-  Learn how to [create a CI/CD pipeline with Azure Pipelines and Compute Engine](https://cloud.google.com/solutions/creating-cicd-pipeline-vsts-compute-engine). 
