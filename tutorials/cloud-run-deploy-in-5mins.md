---
title: Deploying Containers to Cloud Run in 5mins
description: Quickly build and deploy a containerized application and deploy to Cloud Run.
author: timtech4u
tags: Cloud Run, Container Registry, Cloud Build
date_published: 2019-11-15
---

**Cloud Run is now Generally Available.**  [Read more here](https://cloud.google.com/blog/products/serverless/knative-based-cloud-run-services-are-ga) 

![EJWxb0mU8AUMFfP.jpg](https://cdn.hashnode.com/res/hashnode/image/upload/v1573812122798/SnCoa5jff.jpeg)


Software developers today can focus on building applications faster without having to bother about how their codes run on other environments, this is because containerization takes care of bundling applications along with their configuration and dependencies into an efficient way of running it across different environments.


Deploying Containers (Docker or Kubernetes) can also be a headache when you also have to take care of provisioning the underlying infrastructure, however, Google Cloud provides a way for you to deploy containerized applications to the cloud in a serverless fashion called [**Cloud Run**](https://cloud.google.com/run/), it abstracts away the underlying infrastructure, runs and auto-scales your stateless application automatically.


%[https://youtu.be/gx8VTa1c8DA]


## Objective

In this article, we’ll briefly build and deploy a containerized application and deploy to Cloud Run.


## Before you begin

1. Set up a [Google Cloud Account & Project](https://cloud.google.com/gcp/getting-started/)

2. Set up [Google Cloud Shell](https://cloud.google.com/shell/) or [Download its SDK](https://cloud.google.com/sdk/)

3. Clone your containerized application or [copy my example](https://gist.github.com/Timtech4u/6639a92b4197ea831ba9b975c9b34a76)


## Get the sample code

Get the sample code from [GitHub Gist](https://gist.github.com/Timtech4u/6639a92b4197ea831ba9b975c9b34a76).


# Build and Publish Container Images

[Cloud Build](https://cloud.google.com/cloud-build/) allows us to build Docker images on the Cloud, all we need is our project files (which includes a Dockerfile).

The following command runs on Cloud Shell to **build** our Docker image and **push** the image to [Container Registry](https://cloud.google.com/container-registry/).


```
gcloud builds submit --tag gcr.io/<PROJECT_ID>/demo-image .</span>
```


Replace `<PROJECT_ID>` with your actual project ID value.

Note that if you’re building larger images, you can pass a timeout parameter such as: `_--timeout=600s_`


# Deploy to Cloud Run

We would go-ahead to deploy our image from Cloud Shell using the following command:


```
gcloud beta run deploy demo-app --image gcr.io/<PROJECT_ID>/demo-image --region us-central1 --platform managed --allow-unauthenticated --quiet</span>
```

Boom! The application container has been deployed to Cloud Run.😀


Cloud Run is worth looking into by teams, it provides affordability, security, isolation, flexibility by allowing deployment to a Kubernetes cluster ([Cloud Run for Anthos](https://cloud.google.com/run/docs/quickstarts/prebuilt-deploy-gke)) and a lot more.


Here’s a short demo of how fast it is to deploy and access containers with Cloud Run.


%[https://youtu.be/5TvAp0yjZEQ?list=PL1Szsm9yZH_fGfktEvfqOq4uj3sPabEJe]


Another short demo of deploying directly to Cloud Run from your Git repository using the [Cloud Run Button.](https://www.youtube.com/watch?v=14B2zdoBnIY&list=PL1Szsm9yZH_fGfktEvfqOq4uj3sPabEJe&index=2)


%[https://youtu.be/14B2zdoBnIY?list=PL1Szsm9yZH_fGfktEvfqOq4uj3sPabEJe]


## Next steps

If you want to learn more about Cloud Run, check out the following resources:

- 📚 [Cloud Run Product Overview](https://cloud.google.com/run/)

- 💻 [Awesome Cloud Run](https://github.com/steren/awesome-cloudrun

- 🙋 [Cloud Run FAQ](https://github.com/ahmetb/cloud-run-faq)


> Thanks for reading through! Let me know if I missed any step, if something didn’t work out quite right for you or if this guide was helpful.
