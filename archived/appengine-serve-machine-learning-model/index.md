---
title: Serve a machine learning model on App Engine flexible environment
description: Learn how to serve a trained machine learning model with App Engine flexible environment.
author: dizcology
tags: App Engine, Cloud Endpoints, Machine Learning
date_published: 2017-12-18
---

Yu-Han Liu | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial takes a deeper look at the sample app [Model serve][modelserve].
It helps you build your own service serving a trained machine learning model for
online prediction.

## Objectives

1.  Deploy a service with [Cloud Endpoints][endpoints].
1.  Deploy a Python app on [App Engine][appengine] which loads a trained
    machine learning model.
1.  Send requests to the service and get responses.

## Before you begin

Follow the links in the [requirements section][requirements] to install Google
Cloud SDK and enable the APIs for App Engine, Cloud Endpoints, and
Cloud Storage.

## Overview

So you trained a machine learning model. Now what?

If the model's performance is good enough, consider deploying it as a service to
a production system where one or more clients can use it. Some possible
scenarios include:

- The model needs to simultaneously process user requests from your web
  application in real time, and batch process interaction logs you have
  previously stored in a database.
- The model's output is used by multiple other machine learning models in your
  application.

[App Engine][appengine] offers rolling updates, networking, and auto scaling.

[Cloud Endpoints][endpoints] helps you monitor the service's consumers, as well
as manage their permissions and quotas.

You can follow the [steps of the sample app][steps] to deploy a service. Below
we will look at some key pieces of the code to understand how it works.

## A closer look

### [`main.py`][main.py]

Our app expects `POST` requests to the path `/predict`.  It will look for the
value of `'X'` in the JSON data, send it to the trained model, and return the
result as the value of `'y'`:

```python
@app.route('/predict', methods=['POST'])
def predict():
    X = request.get_json()['X']
    y = MODEL.predict(X).tolist()
    return json.dumps({'y': y}), 200
```

Here `MODEL` is a global variable for the trained machine learning model we are
serving.  To make sure the model is loaded, we use the `before_first_request`
decorator, which will be triggered by App Engine's health check requests:

```python
MODEL_BUCKET = os.environ['MODEL_BUCKET']
MODEL_FILENAME = os.environ['MODEL_FILENAME']
MODEL = None

@app.before_first_request
def _load_model():
    global MODEL
    client = storage.Client()
    bucket = client.get_bucket(MODEL_BUCKET)
    blob = bucket.get_blob(MODEL_FILENAME)
    s = blob.download_as_string()

    MODEL = pickle.loads(s)
```

We store the model as a pickled file on [Cloud Storage][storage]. To make sure
the App Engine service knows where to find the model, we pass in the model's
bucket and file name as environment variables.  This is done in the `app.yaml`
configuration file.


### [`app.yaml`][app.yaml]

The `app.yaml` configuration file defines the App Engine service. We define
environment variables pointing to the trained model:

```yaml
env_variables:
    # The app will look for the model file at: gs://MODEL_BUCKET/MODEL_FILENAME
    MODEL_BUCKET: BUCKET_NAME
    MODEL_FILENAME: lr.pkl
```

You should replace `BUCKET_NAME` with a bucket owned by your project. `lr.pkl`
is a simple linear regression model included in the sample app.

To use Cloud Endpoints to manage the service, we need to specify a `config_id`
under the `endpoints_api_service` field:

```yaml
endpoints_api_service:
  name: modelserve-dot-PROJECT_ID.appspot.com
  config_id: CONFIG_ID
```

The `CONFIG_ID` is the configuration ID of a Cloud Endpoints service deployment.
To find existing deployments and their configuration IDs, go to the
[Cloud Endpoints console][endpoints], click on the service's title, then click
on the "Deployment history" tab.

To deploy a service to Cloud Endpoints, we configure it with the
`modelserve.yaml` file.

### [`modelserve.yaml`][modelserve.yaml]

The `modelserve.yaml` configuration file defines the service according to the
[OpenAPI specification][openapi]. We highlight only some of the key settings
below.

- Specify the host:

      host: "modelserve-dot-PROJECT_ID.appspot.com"

  This host means we will handle the requests with an App Engine service called
  `modelserve`.

- Enforce authentication with an API key by adding the `security` and
  `securityDefinitions` fields:

  ```yml
  security:
    - api_key: []
  securityDefinitions:
    api_key:
      type: "apiKey"
      name: "key"
      in: "query"
  ```

  This is optional, but allows you to grant service consumer permissions on the
  [Cloud Endpoints console][endpoints]. The API key must be associated with a
  Google Cloud project. You can create API keys on the
  [credentials][credentials] page.

- Additionally, you can configure quota for each consumer at the project level.
  First we specify a service level metric in order to track the number of
  requests:

  ```yml
  x-google-management:
    metrics:
      - name: "modelserve-predict"
        displayName: "modelserve predict"
        valueType: INT64
        metricKind: DELTA
    quota:
      limits:
        - name: "modelserve-predict-limit"
          metric: "modelserve-predict"
          unit: "1/min/{project}"
          values:
            STANDARD: 1000
  ```

  This configurations declares a metric `modelserve-predict` and sets its limit
  to 1000 units per minute per project.

  Only requests to specified paths are counted towards this metric. Specify
  these paths by adding the following in the `paths` field:

  ```yml
  paths:
    "/predict":
      post:
        ...
        x-google-quota:
          metricCosts:
            modelserve-predict: 1
  ```

  Each time a `POST` request is sent to
  `modelserve-dot-PROJECT_ID.appspot.com/predict`, the metric
  `modelserve-predict` increments by 1, and each project is limited to 1000
  calls per minute with the configuration above.

  You can manage quotas for individual projects on the
  [Cloud Endpoints console][endpoints]. For more information on configuring the
  quota, see the [documentation][quota_docs].

[modelserve]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/tutorials/sklearn/gae_serve
[requirements]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/tutorials/sklearn/gae_serve#requirements
[steps]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/tutorials/sklearn/gae_serve#steps
[modelserve.yaml]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/tutorials/sklearn/gae_serve/modelserve.yaml
[app.yaml]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/tutorials/sklearn/gae_serve/app.yaml
[main.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/tutorials/sklearn/gae_serve/main.py
[lr.pkl]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/tutorials/sklearn/gae_serve/lr.pkl

[appengine]: https://cloud.google.com/appengine/
[endpoints]: https://cloud.google.com/endpoints/
[storage]: https://cloud.google.com/storage/
[credentials]: https://console.cloud.google.com/apis/credentials
[quota_docs]: https://cloud.google.com/endpoints/docs/openapi/quotas-configure

[openapi]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
