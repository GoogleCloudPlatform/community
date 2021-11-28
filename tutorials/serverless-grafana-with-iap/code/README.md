# How to deploy Grafana on Cloud Run with IAP using Terraform

This Terraform script deploys a basic setup for running Grafana serverless on Cloud Run and restricting access via Identoty-Aware Proxy.

You should have basic knowledge of Google Cloud Platform, Grafana and Terraform, own a domain, and can modify its A record.

![Serverless Grafana architecture](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-iap-architecture.png)


### Before you begin

You should have a Google Cloud Platform account and project setup, billing configured for your project, and Terraform installed and enabled.
  1. Know your GCP project ID. If you don’t know how to find the project ID, you can learn about it [here](https://support.google.com/googleapi/answer/7014113?hl=en).
  2. Choose a region to host your project in, ideally one that’s close to you. You can find an overview of available regions [here](https://cloud.google.com/compute/docs/regions-zones).
  3. Make sure you know the domain name where you want to host your Grafana dashboard and are able to edit the A record for this domain.
  4. *Run* `gcloud auth login` to authenticate against Google Cloud Platform. Ideally, you should be using a service account for this, as described [here](https://cloud.google.com/sdk/gcloud/reference/auth/activate-service-account).


### Configure the OAuth consent screen

Configure an OAuth consent screen for Identity-Aware Proxy. 
  1. Go to GCP Console > Security > Identity-Aware Proxy. 
  2. If you didn’t configure a consent screen before, there will be a red warning message prompting you to configure one. 
  ![Consent missing error message](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-consent-not-confgured.png)
  1. Click Configure Consent Screen, choose User Type Internal and click Create. Internal allows only users that are part of your organization to access your application. You can add additional users by logging into admin.google.com.
  ![Configure consent](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-configure-oauth.png)
  4. Enter the app name and user support email, then click Save and continue until the process is complete.


### Set up Terraform and Docker

Next, you’re going to set up the typical configuration for Terraform in order for the project to deploy.

  1. *Open* the Working Directory Examples > Serverless > Grafana in your favorite shell.
  2. *Run* `terraform init`
  3. *Set* required terraform variables, e.g., Linux:
  `export TF_VAR_project_id=[YOUR_GCP_PROJECT_ID]`
  `export TF_VAR_domain=[YOUR_DOMAIN]` This is the domain to host your Grafana dashboard.


### Execute the Terraform script to create your Grafana Dashboard

  1. *Run* `terraform plan` and confirm that all steps are correct.
  2. *Run* `terraform apply`.
  3. Confirm the command has been executed successfully.
  4. *Copy* the external_ip from the console Outputs. *Add* an A record redirect from your domain to this IP address.
  5. Wait around 5 - 10 minutes for GCP Load Balancer to perform certificate checks.


### Access your Grafana Dashboard
  1. Open an Incognito browser window. Go to admin.google.com and sign in with your GCP account owner. Create a new user (only users who are part of your domain can access the dashboard).
  2. Open the GCP Console and go to IAM > Add > enter your user’s email (e.g., user@your-domain.com) and select role IAP-secured Web App User.
  3. Open an incognito window, go to your-domain.com (the domain you used in step 6) and sign in using the newly created user (you will be prompted to change your password the first time you login).

### Troubleshooting

If you see the following error message while deploying, this means you have not configured the Consent Screen for your GCP project.

```
Error: Error creating Client: googleapi: Error 404: Requested entity was not found.
│ 
│   with google_iap_client.project_client,
│   on lb.tf line 62, in resource "google_iap_client" "project_client":
│   62: resource "google_iap_client" "project_client" {
│ 
```