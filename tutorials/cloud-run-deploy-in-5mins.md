---
title: Deploy a container to Cloud Run in 5 minutes
description: Quickly build and deploy a containerized application and deploy it to Cloud Run.
author: timtech4u
tags: Cloud Run, Container Registry, Cloud Build
date_published: 2019-11-20
---

**[Cloud Run](https://cloud.google.com/run/) is now generally available.**

Learn more about Cloud Run on the
[Google website](https://cloud.google.com/blog/products/serverless/knative-based-cloud-run-services-are-ga), in
[this announcement](https://twitter.com/ahmetb/status/1195056373983145984), and in
[this video](https://youtu.be/gx8VTa1c8DA).

Software developers today can focus on building applications faster without having to bother about how their code runs in
other environments. This is because containerization takes care of bundling applications along with their configuration and
dependencies into an efficient way of running it across different environments.

Deploying containers (Docker or Kubernetes) can also be a headache when you have to take care of provisioning the 
underlying infrastructure. However, Google Cloud provides a way for you to deploy containerized applications to the cloud in
a serverless fashion using Cloud Run, which abstracts away the underlying infrastructure and runs and scales your stateless
application automatically.

## Objective

In this article, we’ll quickly build a containerized application and deploy it to Cloud Run.

## Before you begin

1. Set up a [Google Cloud account and project](https://cloud.google.com/gcp/getting-started/).

2. Start [Cloud Shell](https://cloud.google.com/shell/).

3. Clone your containerized application or copy 
[this example from the author of this tutorial](https://gist.github.com/Timtech4u/6639a92b4197ea831ba9b975c9b34a76).

## Get the sample code

Get the sample code from [GitHub Gist](https://gist.github.com/Timtech4u/6639a92b4197ea831ba9b975c9b34a76).

## Build and publish container images

[Cloud Build](https://cloud.google.com/cloud-build/) allows us to build Docker images in the cloud. We just need our
project files (which include a Dockerfile).

Run the following command in Cloud Shell to build our Docker image and push the image to
[Container Registry](https://cloud.google.com/container-registry/):

    gcloud builds submit --tag gcr.io/[PROJECT_ID]/demo-image .

Replace `[PROJECT_ID]` with your actual project ID value.

Note that if you’re building larger images, you can pass a timeout parameter such as `--timeout=600s` as part of this
command.

## Deploy to Cloud Run

Deploy our image from Cloud Shell using the following command:

    gcloud beta run deploy demo-app --image gcr.io/[PROJECT_ID]/demo-image --region us-central1 --platform managed --allow-unauthenticated --quiet

Boom! You have deployed the application container to Cloud Run.

## Next steps

Cloud Run is worth looking into by teams. It provides affordability, security, isolation, and flexibility by allowing
deployment to a Kubernetes cluster
([Cloud Run for Anthos](https://cloud.google.com/run/docs/quickstarts/prebuilt-deploy-gke)) and a lot more.

[This video](https://www.youtube.com/watch?v=5TvAp0yjZEQ) demonstrates how fast it is to deploy and access containers with 
Cloud Run.

[This video](https://youtu.be/14B2zdoBnIY) demonstrates deploying directly to Cloud Run from your Git repository using the
Cloud Run Button.

If you want to learn more about Cloud Run, check out the following resources:

- [Cloud Run product overview](https://cloud.google.com/run/)

- [Awesome Cloud Run](https://github.com/steren/awesome-cloudrun)

- [Cloud Run FAQ](https://github.com/ahmetb/cloud-run-faq)

Thanks for reading through! Let me know if I missed anything, if something didn’t work out quite right for you, or if this
guide was helpful.
