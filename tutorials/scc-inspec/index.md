---
title: Integrating Chef InSpec and Security Command Center
description: Learn how to programmatically add InSpec test results to Security Command Center.
author: jtangney
tags: SCC
date_published: 2021-03-19
---

Jeremy Tangney | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to automatically add [Chef InSpec](https://www.chef.io/products/chef-inspec) test results to
[Security Command Center](https://cloud.google.com/security-command-center). 

InSpec is an open source infrastructure testing framework for specifying compliance, security, and policy requirements. Using InSpec, you can define compliance
requirements as code, and test your cloud infrastructure against those requirements. InSpec works across different cloud providers, so you can use InSpec to test
your Google Cloud infrastructure in the same way that you test your infrastructure in other clouds. For more information about InSpec and Google Cloud, read the
[InSpec article on the Google Open Source blog](https://opensource.googleblog.com/2020/08/assess-security-of-cloud-deployments.html).

Security Command Center is the canonical security and risk database for Google Cloud. Security Command Center provides centralized visibility of all of your 
Google Cloud resources and automatically analyzes your cloud resources for known vulnerabilities. Security Command Center integrates with several
[third-party security sources](https://cloud.google.com/security-command-center/docs/how-to-security-sources#third-party-source). It also provides an
[API](https://cloud.google.com/security-command-center/docs/how-to-programmatic-access) so that you can add and manage additional sources. This way, you can use
Security Command Center as a single interface for all of your security and compliance findings.

## Objectives

-  Create a Security Command Center source.
-  Create and configure project resources using Terraform.
-  Execute InSpec tests using Cloud Build.
-  Export the InSpec test report to a Cloud Storage bucket.
-  Trigger a Cloud Function that analyzes the report and adds findings to Security Command Center to highlight any failed InSpec tests.

The following diagram describes the architecture:

![image](https://storage.googleapis.com/gcp-community/tutorials/scc-inspec/architecture.png)

## Costs

This tutorial uses the following billable components of Google Cloud:

-  [Cloud Build](https://cloud.google.com/cloud-build/pricing)
-  [Cloud Storage](https://cloud.google.com/storage/pricing)
-  [Cloud Functions](https://cloud.google.com/functions/pricing)
-  [Security Command Center](https://cloud.google.com/security-command-center/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Prerequisites

To complete this tutorial you require the following:

-  Security Command Center. For details, see
   [Setting up Security Command Center](https://cloud.google.com/security-command-center/docs/quickstart-security-command-center).
-  Permissions to grant IAM roles at the organization level, such as the
   [Organization Admin](https://cloud.google.com/resource-manager/docs/access-control-org#using_predefined_roles) role.
-  Permissions to interact with Security Command Center. At a minimum, you require the Security Center
   [Findings Viewer](https://cloud.google.com/security-command-center/docs/access-control#security-command-center) IAM role so that you can view the findings 
   created in response to failed InSpec tests.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make cleanup
easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google Cloud project.
1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).
1.  Enable required APIs:

        gcloud services enable \
          cloudfunctions.googleapis.com \
          cloudbuild.googleapis.com \
          storage.googleapis.com \
          securitycenter.googleapis.com \
          iamcredentials.googleapis.com

## Setting up your environment

1.  In Cloud Shell, clone the source repository and go to the directory for this tutorial:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/scc-inspec/

1.  Set environment variables:

        export PROJECT_ID=$(gcloud config get-value core/project)
        export PROJECT_NUM=$(gcloud projects list --filter=$PROJECT_ID \
          --format="value(PROJECT_NUMBER)")
        export ORG_ID=$(gcloud projects get-ancestors $PROJECT_ID \
          --format json | jq -r '.[] | select (.type=="organization") | .id')

1.  Set an environment variable for your region, choosing one of the [locations](https://cloud.google.com/functions/docs/locations) where Cloud Functions is
    available:

        export REGION=us-central1

## Creating a Security Command Center source

In this section, you create a new Security Command Center source. You create findings in this source in response to failed InSpec tests. You must use a service 
account to create a new source.

### Configure IAM permissions

1.  Create a new service account:

        gcloud iam service-accounts create scc-sources-sa

1.  Grant the [Sources Editor](https://cloud.google.com/security-command-center/docs/access-control#security-command-center) role to the service account: 

        gcloud organizations add-iam-policy-binding $ORG_ID \
          --role roles/securitycenter.sourcesEditor \
          --member serviceAccount:scc-sources-sa@${PROJECT_ID}.iam.gserviceaccount.com

    This allows the service account to create new sources in Security Command Center.

1.  Grant the [Service Usage Consumer](https://cloud.google.com/iam/docs/understanding-roles#service-usage-roles) role to the service account at the organization
    level:

        gcloud organizations add-iam-policy-binding $ORG_ID \
          --role roles/serviceusage.serviceUsageConsumer \
          --member serviceAccount:scc-sources-sa@${PROJECT_ID}.iam.gserviceaccount.com
          
    This allows other identities to [impersonate](https://cloud.google.com/iam/docs/impersonating-service-accounts) the Google service account when using Google
    Cloud client libraries, as long as the other identities have the necessary permissions.

1.  Grant your user identity the [Service Account Token Creator](https://cloud.google.com/iam/docs/understanding-roles#service-accounts-roles) role for the 
    service account:

        gcloud iam service-accounts add-iam-policy-binding \
          scc-sources-sa@${PROJECT_ID}.iam.gserviceaccount.com \
          --role roles/iam.serviceAccountTokenCreator \
          --member "user:$(gcloud config get-value account)"

    This allows your user identity to [impersonate](https://cloud.google.com/iam/docs/impersonating-service-accounts) the Google service account.

### Create the Security Command Center source

In this section, you create a new source using a Python script. You impersonate the service account created in the previous step.

1.  Go to the `scc` directory:

        cd scc

1.  Create and activate a new Python virtual environment:

        virtualenv -p python3 venv
        source venv/bin/activate

1.  Install the Security Command Center library:

        pip install google-cloud-securitycenter

1.  Execute the Python script:

        python create_source.py --org_id $ORG_ID \
          --serviceaccount scc-sources-sa@${PROJECT_ID}.iam.gserviceaccount.com
          
      The `create_source.py` script prints the numeric ID of the new source to the console.

1.  Copy the numeric ID of the new source, and set an environment variable with the new source ID (`[YOUR_NEW_SOURCE_ID]`):

        export SOURCE_ID=[YOUR_NEW_SOURCE_ID]

## Creating the infrastructure

In this section, you create and configure Google Cloud resources using Terraform. You create Cloud Storage buckets and deploy a Cloud Function. 

1.  Create a new service account:

        gcloud iam service-accounts create gcf-scc-sa
        
    This service account is used as the Cloud Functions
    [runtime service account](https://cloud.google.com/functions/docs/securing/function-identity#runtime_service_account).

1.  Grant the [Findings Editor](https://cloud.google.com/security-command-center/docs/access-control#security-command-center) role to the service account: 

        gcloud organizations add-iam-policy-binding $ORG_ID \
          --role roles/securitycenter.findingsEditor \
          --member serviceAccount:gcf-scc-sa@${PROJECT_ID}.iam.gserviceaccount.com

    This allows the service account to create new findings in Security Command Center.

1.  Go to the `terraform` directory and substitute the environment variables into your Terraform variables configuration:

        cd ../terraform
        envsubst < terraform.tfvars.template > terraform.tfvars 

1.  Initialize Terraform, and create the infrastructure:

        terraform init
        terraform apply -auto-approve

## Executing InSpec tests using Cloud Build

In this section, you execute simple InSpec tests against your Google Cloud project. You use Cloud Build to execute the InSpec tests. The tests validate that the 
Cloud Storage buckets in your project adhere to an example policy with the following characteristics:

-  Buckets use the `STANDARD` storage class.
-  Buckets are located in particular regions.

The snippet below shows the InSpec control that implements the policy:

```ruby
control 'policy_bucket_config' do
  title 'Cloud Storage bucket configuration policy'
  desc 'Compliance policy checks for Cloud Storage buckets'
  impact 'medium'
  tag scc_category: 'BUCKET_CONFIG'
  tag resource_type: 'bucket'
  tag project_id: project_id

  google_storage_buckets(project: project_id).bucket_names.each do |bucket|
    describe "[#{bucket}][#{project_id}] GCS Bucket" do
      before do
        skip if bucket.match?(bucket_ignore_pattern)
      end
      subject { google_storage_bucket(name: bucket) }
      its('storage_class') { should eq 'STANDARD' }
      its('location') { should be_in ['US-CENTRAL1', 'US'] }
    end
  end
end
```

Executing the InSpec tests generates a report. The build exports the report to a Cloud Storage bucket that you created earlier. This in turn triggers a Cloud 
Function that analyzes the report and adds findings to Security Command Center. The tags and other metadata defined in the control are used to create a 
corresponding Security Command Center finding.

1.  Go back to the main directory:

        cd ..

1.  Submit the Cloud Build to execute the InSpec tests:

        gcloud builds submit --config cloudbuild.yaml \
          --substitutions=_REPORTS_BUCKET=inspec-reports_${PROJECT_NUM}	

1.  Verify that an InSpec test report has been generated in the Cloud Storage bucket:

        gsutil ls gs://inspec-reports_${PROJECT_NUM}

1.  Wait a few moments, and check the Cloud Functions logs:

        gcloud functions logs read inspec-scc --limit 10 --region $REGION

1.  Verify that no findings have been added to the source:

        gcloud scc findings list $ORG_ID --source $SOURCE_ID

## Adding a non-compliant bucket

In this section, you create a new Cloud Storage bucket that does not conform to the policy. You run the InSpec tests again, and this time a new finding is added 
to the Security Command Center source to capture the non-compliant bucket

1.  Create a new bucket with NEARLINE storage class:

        gsutil mb -c NEARLINE -l $REGION gs://bad_bucket_${PROJECT_NUM}

1.  Submit the Cloud Build again:

        gcloud builds submit --config cloudbuild.yaml \
          --substitutions=_REPORTS_BUCKET=inspec-reports_${PROJECT_NUM}
          
    The InSpec output indicates a failed test.

1.  Verify that another InSpec report has been generated in the Cloud Storage bucket:

        gsutil ls gs://inspec-reports_${PROJECT_NUM}

1.  Wait a few moments, and check the Cloud Functions logs:

        gcloud functions logs read inspec-scc --limit 10 --region $REGION

1.  Verify that a finding has been added to the source.

        gcloud scc findings list $ORG_ID --source $SOURCE_ID

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, perform the following actions:

1.  In Cloud Shell, destroy the resources that you created in your project, such as the Cloud Storage buckets and Cloud Function:

        cd terraform
        terraform destroy -auto-approve 

1.  If you no longer require the project, delete it:

        gcloud projects delete $PROJECT_ID

1.  To hide the findings in Security Command Center, you can mark them as inactive. For more information, see
    [Using Security Command Center dashboard](https://cloud.google.com/security-command-center/docs/how-to-use-security-command-center#findings).

## What's next

-  Read the [Google Cloud Security Foundations](https://services.google.com/fh/files/misc/google-cloud-security-foundations-guide.pdf) guide.
-  Explore the InSpec tests in the [Google Cloud CIS benchmark InSpec profile](https://github.com/GoogleCloudPlatform/inspec-gcp-cis-benchmark).
