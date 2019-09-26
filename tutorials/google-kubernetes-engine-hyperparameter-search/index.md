---
title: Hyperparameter search with Google Kubernetes Engine
description: Learn how to run Scikit-Learn's SearchCV hyperparameter search on Google Kubernetes Engine.
author: dizcology
tags: Kubernetes Engine, Machine Learning, Scikit-Learn
date_published: 2018-06-13
---

This tutorial takes a deeper look at the [sample notebook][gke_randomized_search].
It illustrates how to run parallelized hyperparameter search for Scikit-Learn models on [Google Kubernetes Engine][gke].

## Objectives

1.  Build a docker image with [Container Registry][gcr].
1.  Create a cluster on [Google Kubernetes Engine][gke].
1.  Fit a [RandomizedSearchCV][randomizedsearchcv] object on the cluster.

## Before you begin

Follow the links in the [requirements section][requirements] to enable the APIs for Container Registry, Google Kubernetes 
Engine, and Cloud Storage.

Follow the steps in the [Before you start section][beforeyoustart] to install dependencies.

## Overview

Hyperparameter search is one of the time-consuming parts of fitting a machine learning model. A model is fitted to the data
many times, each time with different hyperparameters, and the performance recorded. This can be parallelized in the 
following ways:

-   Many scikit-learn models have the `n_jobs` argument allowing multi-thread model fitting, for instance 
    [RandomForestClassifier][rfc].

-   The wrappers such as [RandomizedSearchCV][randomizedsearchcv] that handle hyperparameter search also have their `n_jobs`
    argument running separate model fitting jobs on multiple subprocesses in parallel.

Running fitting jobs in parallel speeds up the search, but can require a lot of computational resources. The
[sample notebook][gke_randomized_search] provides a workflow that allows you to set up hyperparameter search experiments on
your computer but sends the actual workload to a cluster on Google Kubernetes Engine. The advantages of doing this include 
the following:

-   You can continue to use your laptop/workstation for other work while waiting for the results.
-   You can use more powerful machines to speed up the search, for instance mulitple nodes with 64 virtual CPU cores.

To accomplish this, we will create a `SearchCV` object in the notebook, upload a pickled copy of this object to Cloud 
Storage. A job running on a cluster which we will create then retrieves that pickled object and calls its `fit` method and 
saves the fitted object to Cloud Storage. Finally, we can download the fitted object and call its prediction method or 
examine evaluation metrics.

## A closer look

### Overview of the workflow

The sample is designed to keep most of the workflow in a Jupyter notebook and to feel very similar to a typical 
experimentation workflow. To run a scikit-learn hyperparameter search job locally on your laptop, you might run something 
like this (snippets from [sample notebook][gke_randomized_search]):

    rfc = RandomForestClassifier(n_jobs=-1)
    param_distributions = {
        'max_features': uniform(0.6, 0.4),
        'n_estimators': range(20, 401, 20),
    }
    search = RandomizedSearchCV(estimator=rfc, param_distributions=param_distributions, n_iter=100, n_jobs=-1)

And follow it with a `search.fit(X, y)` call.

With the helper modules included in this sample, you can send the computation workload to Kubernetes Engine by wrapping the
`SearchCV` object and call its `fit` method:

    from gke_parallel import GKEParallel

    gke_search = GKEParallel(search, project_id, zone, cluster_id, bucket_name, image_name)
    gke_search.fit(X, y)

(For the purposes of this overview, we skipped a few additional steps for creating a Docker image and a cluster that we need
to run before calling `gke_search.fit`.)

While the job is running on the cluster, you can monitor its progress with this command:

    gke_search.done()

When all workers have finished their portion of the work, you can download the fitted object with

    result = gke_search.result(download=True)

You can use it as you normally would a `SearchCV` object:

    prediction = gke_search.predict(X_test)

You can follow the steps in the [sample notebook][gke_randomized_search] to run a hyperparameter search fitting job on
Google Kubernetes Engine.

The sample code comes with some [helper modules][helper] to keep the workflow in the notebook by handling various 
upload/download tasks. Below we look at some key pieces of the helper modules to better understand how they work.

### [`cloudbuild_helper.py`][cloudbuild_helper.py]

To run the hyperparameter search job on a Google Kubernetes Engine cluster, we need to package the code in a Docker image.
For the purpose of this sample, you can think of a Docker image as a piece of executable code that is already bundled with
its dependencies and can be run anywhere.

We use a service provided by Cloud Registry to build and register the docker image we need.

    # cloudbuild_helper.py
    service = discovery.build('cloudbuild', 'v1', credentials=credentials)
    build = service.projects().builds().create(projectId=project_id, body=body).execute()

Here the request `body` contains all the information needed to build the Docker image. For example, it might look like this:

    # cloudbuild_helper.py
    {
        'source': {
            'storageSource': {
                'bucket': 'YOUR-GCS-BUCKET-NAME',
                'object': 'PATH-TO-ZIPPED-SOURCE-ON-GCS'
            }
        },
        'steps': [
            {
                'name': 'gcr.io/cloud-builders/docker',
                'args': ['build', '-t', 'gcr.io/$PROJECT_ID/IMAGE_NAME', '.']
            }
        ],
        'images': [
            'gcr.io/$PROJECT_ID/IMAGE_NAME'
        ]
    }

When a build request is successfully executed on Cloud Registry, a Docker image will be created and registered with an
identifier such as `gcr.io/$PROJECT_ID/IMAGE_NAME`. Later we will pass this to Google Kubernetes Engine so the source code 
packaged in the Docker image can be executed on a cluster.

Note that we need to upload a zipped folder containing the source code to Cloud Storage. The helpers in this sample take 
care of that for us.

### [`source`][source]

The `source` folder contains the code that will actually be executed on the cluster. It contains a simple
[Dockerfile][Dockerfile] that contains the instructions for Cloud Registry to build the docker image.

The file [worker.py][worker.py] contains the code that retrieves a pickled `SearchCV` object from Cloud Storage and calls
its `fit` method.

    # worker.py
    X = download_uri_and_unpickle(X_uri)
    y = download_uri_and_unpickle(y_uri)
    search = download_and_unpickle(bucket_name, 'worker_0/search.pkl')

    search.fit(X, y)

Here `download_uri_and_unpickle` and `download_and_unpickle` are helper methods in [gcs_helper.py][gcs_helper.py].

In the code snippet above we see that the training data are provided as Cloud Storage URIs. This allows you to upload the 
data just once and use it for multiple hyperparameter search jobs.

### [`gke_helper.py`][gke_helper.py]

To make it easy to create a cluster on which our jobs will run, the sample code includes helpers to send cluster creation 
requests to Google Kubernetes Engine.

    # gke_helper.py
    service = discovery.build('container', 'v1', credentials=credentials)
    create = service.projects().zones().clusters().create(body=body, zone=zone, projectId=project_id).execute()

Here the request `body` specifies the cluster to be created, such as the type and number of nodes. For example, a cluster of
one node with 64 cores might be specified as follows:

    # gke_helper.py
    cluster = {
        'master_auth': {
            'username': 'admin'
        },
        'name': 'YOUR-CLUSTER-ID',
        'node_pools': [
            {
                'name': 'default-pool',
                'initial_node_count': 1,
                'config': {
                    'machine_type': 'n1-standard-64',
                    'oauth_scopes': [
                        # required scopes here
                    ]
                }
            }
        ]
    }

    body = {
        'cluster': cluster
    }

Some `oauth_scopes` are required for the cluster to interact with Cloud Registry (to pull the Docker image we created) and
Cloud Storage (to get the training data and pickled `SearchCV` object).

### [`kubernetes_helper.py`][kubernetes_helper.py]

To execute the code we packaged as a Docker image on a cluster, we need to submit a `job` to the cluster. We use 
the Kubernetes client library for that.

    # kubernetes_helper.py
    v1 = client.BatchV1Api()

    job = v1.create_namespaced_job(body=job_body, namespace=namespace)

Here `job_body` specifies the registered Docker image and what command to execute.

### [`gke_parallel.py`][gke_parallel.py]

Our `job_body` might look like:

    # gke_parallel.py
    body = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': 'worker_0'
        },
        'spec': {
            'template': {
                'spec': {
                    'containers': [
                        {
                            'image': 'gcr.io/$PROJECT_ID/IMAGE_NAME',
                            'command': ['python'],
                            'args': ['worker.py', 'YOUR-GCS-BUCKET-NAME', 'TASK_NAME', '0', X_uri, y_uri],
                            'name': 'worker'
                        }
                    ],
            'restartPolicy': 'OnFailure'}
            }
        }
    }

In addition to the parallelization offered by scikit-learn objects through the `n_jobs` arguments, a `GKEParallel` object 
deploys one `job` to every available node in the cluster.

In the case of a `RandomizedSearchCV` job, these different jobs simply try different hyperparameters according to the same
distribution. In the cases of `GridSearchCV` or `BayesSearchCV`, the sample code implements simple logic to split up the 
parameter grids or parameter spaces so that different jobs will explore different parts of the hyperparameter space.

### What's next

Here are are some things that you should consider doing besides adapting the [sample notebook][gke_randomized_search] in 
your own hyperparameter search experiments.

- Update [worker.py][worker.py] so that it does more. Here are some ideas:
  - Send the cross-validation metrics data to a dashboard for easier management.
  - Deploy the best model if it performs better on a held out test dataset than the model currently in production.
- Update [gke_parallel.py][gke_parallel.py], especially the logic of splitting parameter grids and parameter spaces to 
  better suite your needs.
- Learn how Docker and Kubernetes can help you with your data science workflow.

[gke_randomized_search]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/gke_randomized_search.ipynb
[requirements]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/hpsearch#requirements
[beforeyoustart]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/hpsearch#before-you-start
[rfc]: http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
[helper]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/hpsearch/helpers
[cloudbuild_helper.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/helpers/cloudbuild_helper.py
[source]: https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/sklearn/hpsearch/source
[Dockerfile]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/source/Dockerfile
[worker.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/source/worker.py
[gcs_helper.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/helpers/gcs_helper.py
[gke_helper.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/helpers/gke_helper.py
[kubernetes_helper.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/helpers/kubernetes_helper.py
[gke_parallel.py]: https://github.com/GoogleCloudPlatform/ml-on-gcp/blob/master/sklearn/hpsearch/gke_parallel.py

[gke]: https://cloud.google.com/kubernetes-engine/
[gcr]: https://cloud.google.com/container-registry/
[randomizedsearchcv]: http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html

