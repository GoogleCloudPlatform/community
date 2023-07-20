# Three-Tier Containerized Application on Google Cloud

[![Terraform Plan](https://github.com/McK-Internal/gcp-three-tier-ref-app/actions/workflows/tf-plan.yml/badge.svg)](https://github.com/McK-Internal/gcp-three-tier-ref-app/actions/workflows/tf-plan.yml)

[![Terraform Apply](https://github.com/McK-Internal/gcp-three-tier-ref-app/actions/workflows/tf-apply.yml/badge.svg)](https://github.com/McK-Internal/gcp-three-tier-ref-app/actions/workflows/tf-apply.yml)

This repository contains the source code and configuration files for a three-tier containerized application on Google Cloud. The application consists of a frontend developed using Angular, a backend developed using Flask, and a Firestore database. The infrastructure is managed using Terraform, and the continuous integration and deployment (CI/CD) pipeline is set up using GitHub Actions for infrastructure and Cloud Build for application code / containers.

## Architecture

The application follows a three-tier architecture, with separate layers for the frontend, backend, and database. Here's an overview of each component:

1. **Frontend**: The frontend is built using Angular, a popular web development framework. It runs on Cloud Run, a fully managed serverless platform on Google Cloud. Cloud Run provides automatic scaling and handles container orchestration.

2. **Backend**: The backend is developed using Flask, a lightweight Python web framework. It also runs on Cloud Run, allowing for easy scalability and management. The backend handles the business logic of the application and interacts with the Firestore database.

3. **Database**: The application uses Firestore, a NoSQL document database provided by Google Cloud. Firestore offers a flexible data model and automatic scalability. It is used to store and retrieve data required by the application.

## Getting Started

To get started with this application, follow these steps:

### Clone the GitHub Repository

To simplify and centralize, we use a single repository to hold all of the application, infrastructure, and pipeline code.

To get started, you can duplicate or fork this repository.

### Configure Terraform with Remote State and GitHub Actions

This application uses Terraform to manage infrastructure. We will store Terraform State in a remote backend, specifically a GCS bucket.

#### Step 1 - Access your project in the Google Cloud console

Projects are required to manage and organize resources in Google Cloud.

Navigate to the Google Cloud console and log in (or create an account), then select your project. If you do not already have a Google Cloud project, navigate to **Menu** > **IAM & Admin** > **Create a Project** then follow the prompts in the console.

#### Step 2 - Create a Cloud Storage bucket

The GCS Bucket will be used to store the Terraform State.

In the Google Cloud console, navigate to the Cloud Storage Buckets page > Create bucket.

- For **name**, create a globally unique name (e.g., `<random-prefix>-<app-name>-tfstate`)
- For **location type**, choose **Multi-Region, US**
- For **storage class**, choose **Standard**.
- For **access control**, check **Enforce public access prevention** on this bucket and select **Uniform access control**
- For **data protection**, select **Object versioning**
```
```
gcloud storage buckets create gs://BUCKET_NAME
```
```

Note: If you are especially savvy with Terraform, you may find it easier to create the bucket with Terraform local state, then migrate the state into the bucket. See the Google Cloud documentation for more details.

#### Step 3 – Configure Terraform to use the remote backend

Navigate back to your code repository. Under the `infra` directory, open `providers.tf` and replace the name of the backend bucket with your bucket’s name.

#### Step 4 – Create a Service Account with roles/editor permissions

In the Google Cloud console, navigate to the Service Accounts page and select "create service account."

- **Name** – recommend using a name similar to **cicd-service-account**
- **Role** – select **Basic**, then select **Owner**
```
gcloud iam service-accounts create SA_NAME \
    --description="" \
    --display-name=""
```
```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SA_NAME@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/owner"
```
#### Step 5 – Generate a Service Account Key

Select the Terraform Service Account in the console, then navigate to the Keys tab.

- Select **Add Key**, then select **Create new key**
- Select **JSON** as the **Key type** and click **Create**.

```
gcloud iam service-accounts keys create KEY_FILE \
    --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com
```

#### Step 6 – Add the Service Account Key as a secret in GitHub

Before using the key in GitHub, the key should be compacted. An easy way to do this is to use jq and run the following command:

`jq -c . <key-file-name>`

Copy this output and navigate back to your GitHub repository. Select **Settings** > **Secrets and variables** > **Actions** > **New Repository Secrets**. Name the secret **GCP_TF_CREDENTIALS** and paste in the key value.

#### Step 7 – Add the Service Account Name as a variable in GitHub
Note the full name (email) of your service account and navigate back to your GitHub repository. Select **Settings** > **Secrets and variables** > **Actions** > Select the **Variables** tab >**New Repository Variable**. Name the variable **GCP_TF_SA** and paste in the key value.

#### Step 8 - Run the inital-deploy GitHub Actions workflow
Ensure you have added your project to `terraform.tfvars`, your service account key as a github secret, your service account email as a github variable, and your bucket that will be used for remote state to `providers.tf`.
Then, from your GitHub repository navigate to Actions and start the `Initial Deploy Workflow`

#### Step 8 - Firebase Config
Navigate to `https://console.firebase.google.com` -> Add project -> select your GCP project from the dropdown -> Continue -> Confirm Plan -> Choose to enable Google Analytics or not -> Continue -> Add Firebase to your web app -> Register app with your chosen name

Copy the value for `const firebaseConfig` and paste the value into `app/frontend/src/environments/environments.ts`

##### Firebase Auth
Use the Google provider for Firebase auth
All projects -> Authentication -> Get Started -> Google -> Enable -> Add support email -> Save

#### Step 9 API GateWay Config
Run the following command to get the api-gateway config, and paste the output to `app/frontend/src/employee/services/firestore.service.ts` where you see the three urls.
```
gcloud api-gateway gateways describe employee-gateway --location LOCATION --project PROJECT_ID --format 'value(defaultHostname)'
```
The fields should look like
```
addEmployeeUrl = 'https://employee-gateway-88s1idnh.ue.gateway.dev/employee';
employeesUrl = 'https://employee-gateway-88s1idnh.ue.gateway.dev/employees';
deleteEmployeeUrl = 'https://employee-gateway-88s1idnh.ue.gateway.dev/employee';
```
Commit this to main and the frontend cloud build workflow will run

### Deploy Infrastructure using Terraform and GitHub Actions
Run the tf-apply workflow to deploy all exisitng Terraform resources