---
title: Creating a CI/CD environment for serverless containers on Cloud Run with GitHub Actions
description: Learn how to use GitHub Actions to test and deploy Docker containers on Cloud Run.
author: leozz37
tags: Cloud Run, Golang, GitHub, Docker, cicd, devops
date_published: 2020-10-30
---

Leonardo Lima

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this article, you set up an environment for automated building, testing, and deployment, using Docker and Cloud Run.

For Docker, the language that you're using isn't important, but this tutorial uses the Go programming language. This tutorial doesn't go into a deep explanation
of the sample code and its Dockerfile.

![cover](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/cover.png)

## Objectives

*   Create a simple REST API with Go.
*   Write a unit test for your code.
*   Create a Dockerfile.
*   Create a GitHub Action workflow file to deploy your code on Cloud Run.
*   Make the code accessible for anyone.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Run](https://cloud.google.com/run)
*   [Cloud Storage](https://cloud.google.com/storage)

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the
[pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Prerequisites

This tutorial assumes that you're using a Unix-like operating system.

This tutorial uses the [Cloud SDK command-line interface](https://cloud.google.com/sdk/install) to set up the environment, but you can also use the
[Cloud Console](https://console.cloud.google.com).

## Architecture overview

First, take a look at the infrastructure used in this tutorial:

![architecture](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/architecture.png)

Every time you push to your GitHub repository, it triggers a GitHub Actions workflow that builds and tests your code. If it builds and every test passes, your
container is deployed to Cloud Run, making it accessible to everyone.

The author of this tutorial created a [GitHub repository](https://github.com/leozz37/cloud-run-actions-example) with all of the code used here, which you can 
check out.

This is what the work tree will look like:

    |_.github/
      |_workflows/
        |_GCP-Deploy.yml
    |_Dockerfile
    |_go.mod
    |_server_test.go
    |_server.go

It's time to get your hands dirty!

## Go code

Begin with a simple Go program and test. Because the application's functionality doesn’t matter for this tutorial, this tutorial uses a simple example that 
returns a JSON response with "Hello, world".

    package main

    import (
	    "encoding/json"
        "log"
        "net/http"
        "os"

        "github.com/gorilla/mux"
    )

    type Phrase struct {
        Text string `json:"phrase"`
    }

    func HelloWorld() Phrase {
        return Phrase{
                Text: "Hello, world",
        }
    }

    func GetPhrase(w http.ResponseWriter, r *http.Request) {
        json.NewEncoder(w).Encode(HelloWorld())
    }

    func main() {
        router := mux.NewRouter()
        router.HandleFunc("/", GetPhrase).Methods("GET")

        port := os.Getenv("PORT")
        log.Print("Started API on port: " + port)
        log.Fatal(http.ListenAndServe(":"+port, router))
    }

Here is a unit test for the `HelloWorld` function that verifies whether the function returns a `“Hello, world”` string:

    package main

    import (
        "testing"
    )

    func TestHelloWorld(t *testing.T) {
        var expected Phrase

        expected.Text = "Hello, world"
        result := HelloWorld()

        if expected.Text != result.Text {
                t.Errorf("Phrase was incorrect. Got: %s, want: %s.", result.Text, expected.Text)
        }
    }

Go needs a module file that tells all of the code dependencies. Create a GitHub repository (but don't push your code yet), copy its URL, and run the following
command:

    go mod init $"YOUR_GITHUB_URL"

For example, the command should look something like this:

    go mod init github.com/leozz37/cicd-actions-cloud-run

## Dockerfile code

    FROM golang:alpine
    ENV CGO_ENABLED=0

    WORKDIR /app
    COPY . .

    RUN go mod download
    RUN go build -o main .

    EXPOSE $PORT

    CMD [ "./main" ]

Cloud Run sets an environment variable for the port, and it's recommended that you get that port from the environment. But you can set a custom port if you need
it.

## Cloud Run

1.  To make your life easier, export these environment variables so that you can copy and paste the commands used here. Choose whatever name you want, but the 
    `$PROJECT_ID` has to be a unique name, because project IDs can't be reused in Google Cloud.

        export PROJECT_ID=
        export ACCOUNT_NAME=

    For example, your commands should look something like this:

        export PROJECT_ID=project-example
        export ACCOUNT_NAME=account-example

1.  Log in with your Google account:

        gcloud auth login

1.  Create a project and select that project:

        gcloud projects create $PROJECT_ID
        gcloud config set project $PROJECT_ID

1.  Enable billing for your project, and create a billing profile if you don’t have one:

        open "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"

1.  Enable the necessary services:

        gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com

1.  Create a service account:

        gcloud iam service-accounts create $ACCOUNT_NAME \
          --description="Cloud Run deploy account" \
          --display-name="Cloud-Run-Deploy"
      
1.  Give the service account Cloud Run Admin, Storage Admin, and Service Account User roles. You can’t set all of them at once, so you have
    to run separate commands:

        gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member=serviceAccount:$ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
          --role=roles/run.admin

        gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member=serviceAccount:$ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
          --role=roles/storage.admin
  
        gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member=serviceAccount:$ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
          --role=roles/iam.serviceAccountUser

1.  Generate a `key.json` file with your credentials, so your GitHub workflow can authenticate with Google Cloud:

        gcloud iam service-accounts keys create key.json \
            --iam-account $ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com

## GitHub

In GitHub, you need to set up a secrets environment in your repository, with the following values:

-   `GCP_PROJECT_ID` is your `$PROJECT_ID`.
-   `GCP_APP_NAME` is your app name.
-   `GCP_EMAIL` is the email from the service account you created, which should look like this:
    `$ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com`
-   `GCP_CREDENTIALS` is the content from the `key.json` file that you just created.

For example, your settings should look something like this:

    GCP_PROJECT_ID = project-example
    GCP_APP_NAME = app-name
    GCP_EMAIL = account-name@project-example.iam.gserviceaccount.com

Cat the `key.json` content and paste it into the `GCP_CREDENTIALS` secret value.

![secret-json](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/img1.png)

Your secrets should look like this:

![secrets](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/img2.png)

Now you just need to create a YAML file telling which commands your workflow should run. In your project directory, create a folder called `.github` and create
another one inside it called `workflows`.

Create a `GCP-Deploy.yml` file and copy this content into it:

{% verbatim %}

    name: Docker

    on:
      push:
        branches: [ master ]
      pull_request:
        branches: [ master ]

    jobs:

        deploy:

            name: Setup Gcloud Account
            runs-on: ubuntu-latest
            env:
              IMAGE_NAME: gcr.io/${{ secrets.GCP_PROJECT_ID }}/${{ secrets.GCP_APP_NAME }}
            steps:

            - name: Login
              uses: google-github-actions/setup-gcloud@v0
              with:
                project_id: ${{ secrets.GCP_PROJECT_ID }}
                service_account_email: ${{ secrets.GCP_EMAIL }}
                service_account_key: ${{ secrets.GCP_CREDENTIALS }}

            - name: Configure Docker
              run: gcloud auth configure-docker --quiet

            - name: Checkout repository
              uses: actions/checkout@v2

            - name: Build Docker image
              run: docker build . -t $IMAGE_NAME

            - name: Test Docker image
              run: docker run $IMAGE_NAME sh -c "go test -v"

            - name: Push Docker image
              run: docker push $IMAGE_NAME

            - name: Deploy Docker image
              run: gcloud run deploy ${{ secrets.GCP_PROJECT_ID }} --image $IMAGE_NAME --region us-central1 --platform managed

{% endverbatim %}

You work tree should look like this:

    |_.github/
      |_workflows/
        |_GCP-Deploy.yml

Now commit all of your changes and push them to GitHub, and then go to your repository home page. While your build is running, you should see a yellow circle
over your file list:

![files](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/img3.png)

If you go into your Actions (click the yellow ball), you can see in real time your steps being executed:

![build](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/img4.png)

You can list your service, get its link, and access it in your browser:

    gcloud run services list

![result](https://storage.googleapis.com/gcp-community/tutorials/cicd-cloud-run-github-actions/img5.png)

And that’s it! Each time you push a change to the default branch, GitHub builds, tests, and deploys it automatically.

### Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

### What's next

- Learn more about [Google Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
