![](https://github.com/googleinterns/cloud-monitoring-notification-delivery-integration-sample-code/workflows/Continuous%20Integration/badge.svg)

# Sample Code for the Cloud Monitoring Notification Delivery Integration Guide

**This is not an officially supported Google product.**

Complete sample code to accompany the Google Cloud Monitoring Notification
Delivery Integration solutions guide.

This repository provides an example of how a Google Cloud user can forward
**[notifications](https://cloud.google.com/monitoring/alerts#how_does_alerting_work)**
to third-party integrations not officially supported at
**[notification options](https://cloud.google.com/monitoring/support/notification-options)**.

## Source Code Headers

Every file containing source code must include copyright and license
information. This includes any JS/CSS files that you might be serving out to
browsers. (This is to help well-intentioned people avoid accidental copying that
doesn't comply with the license.)

Apache header:

    Copyright 2020 Google LLC

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.


## Terraform Setup

Terraform configurations are used to create the infrastructure needed for this integration, such as Pub/Sub topics and subscriptions and Cloud Run instances. The `dev` and `prod` environments each have their own Terraform configurations, which can be found in the ```environments/``` directory. Terraform modules can be found in the ```modules/``` directory. The configs store state remotely in a Cloud Storage bucket so that anyone running the configs has a consistent version of the Terraform state.

Deployment with Terraform will be automated through source code changes in GitHub. To test the deployment manually, first create a Cloud Storage bucket in Cloud Shell that Terraform will use to store state:
```
PROJECT_ID=$(gcloud config get-value project)
gsutil mb gs://${PROJECT_ID}-tfstate
```
Note that you only need to create the bucket once. Trying to do create a duplicate bucket will display an error. 

You may optionally enable Object Versioning to keep the history of your deployments:
```
gsutil versioning set on gs://${PROJECT_ID}-tfstate
```
Enabling Object Versioning increases storage costs, which you can mitigate by configuring Object Lifestyle Management to delete old state versions.

Now, navigate to the desired environment folder (`environments/dev` or `environments/prod`) and run the following:

Initialize a working directory containing Terraform configuration files:
```
terraform init -backend-config "bucket=$PROJECT_ID-tfstate"
```
Refresh the current Terraform state:
```
terraform refresh
```
When prompted for `var.project`, enter the GCP project ID.

To see what changes will be made without applying them yet:
```
terraform plan
``` 

Apply configuration changes:
```
terraform apply
```
When prompted, type `yes` to confirm changes. Once finished, information about the created resources should appear in the output.
