---
title: Serve Machine Learning Model on App Engine Flex
description: Learn how to serve a trained machine learning model with Google App Engine flex environment.
author: dizcology
tags: App Engine, Cloud Endpoints, Machine Learning
date_published: 
---
This tutorial takes a deeper look at the sample app [Model serve][modelserve].  It helps you build your own service serving a trained machine learning model for online prediction.

## Objectives

1. Deploy a service with [Google Cloud Endpoints][endpoints].
1. Deploy a Python app on [Google App Engine][appengine] which loads a trained machine learning model.
1. Send requests to the service and get responses.

## Before you begin

Follow the links in the [Requirements section][requirements] to install Google Cloud Platform SDK and enable the APIs for App Engine, Cloud Endpoints, and Google Cloud Storage.

## Overview

So you trained a machine learning model.  Now what?

If the model’s performance is good enough, consider deploying it as a service to a production system where one or more clients can use it.  Some possible scenarios include:

- The model needs to process requests in real time when the users are interacting with your web application while at the same time batch process interaction logs you have stored previously in a database.

- The model's output is used by multiple other machine learning models in your application.

App Engine offers rolling update, networking, and auto scaling.

Cloud Endpoints helps you manage permission and quota of the service's consumers.

You can follow the [steps of the sample app][steps] to deploy a service.  Below we will look at some key pieces of the code to understand how it works.

## A closer look

### [`modelserve.yaml`][modelserve.yaml]

The `modelserve.yaml` configuration file defines the service according to the [OpenAPI specification][openapi].

- Specify the path, method, and input/output types under the `paths` field:

    ```yaml
    paths:
      "/predict":
        post:
          description: "Get prediction given X."
          operationId: "predict"
          consumes:
          - "application/json"
          produces:
          - "application/json"
    ```

- Enforce authentication with API key by adding the `security` and `securityDefinitions` fields:

    ```yaml
    security:
      - api_key: []
    securityDefinitions:
      api_key:
        type: "apiKey"
        name: "key"
        in: "query"
    ```

    With this

### [`app.yaml`][app.yaml]

### [`main.py`][main.py]


[modelserve]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/gae_serve
[requirements]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/gae_serve#requirements
[steps]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/gae_serve#steps
[modelserve.yaml]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/gae_serve/modelserve.yaml
[app.yaml]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/gae_serve/app.yaml
[main.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/gae_serve/main.py
[lr.pkl]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/gae_serve/lr.pkl

[appengine]: https://cloud.google.com/appengine/
[endpoints]: https://cloud.google.com/endpoints/

[openapi]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md

