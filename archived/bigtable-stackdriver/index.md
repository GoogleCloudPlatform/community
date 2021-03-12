---
title: Using Matplotlib to visualize Cloud Monitoring metrics for Cloud Bigtable
description: Learn about using Matplotlib to plot Cloud Monitoring metrics for Cloud Bigtable.
author: waprin
tags: Stackdriver, Bigtable, matplotlib
date_published: 2017-06-13
---

Bill Prin | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Cloud Monitoring](https://cloud.google.com/monitoring/) is
a service that collects metrics, events, and metadata from Google Cloud or
Amazon Web Services (AWS).

Cloud Monitoring comes with a built-in console for exploring metrics and
plotting figures. To see this console:

1. Open the [Cloud Console](https://console.cloud.google.com/monitoring).
1. Sign in and create or select an account, if prompted.

Many useful charts are automatically created for you, and many more custom
graphs can be built within the console. For
[Cloud Bigtable](https://cloud.google.com/bigtable/), some charts can
be found in the Bigtable console, as well as in the
Metrics Explorer.

As an alternative
approach, you can use the Python library [Matplotlib](https://matplotlib.org/) in conjunction with the
[Google Cloud Python client library](https://github.com/GoogleCloudPlatform/google-cloud-python/tree/master/monitoring),
and its built-in integration with the [pandas](http://pandas.pydata.org/)
data science library, to make sophisticated graphs. 

This tutorial demonstrates
some simple plotting to help you get started, in conjunction with the
sample code for programmatically scaling Cloud Bigtable.

The Stackdriver Python client library can be used either in standard
[Jupyter](http://jupyter.org/) notebooks or with
[Datalab](https://cloud.google.com/datalab/). This tutorial
focuses on vanilla Jupyter.

Jupyter notebooks allow you to create interactive, annotated notebooks that
can be shared with others. Because the sample notebook relies on default
authentication and project configurations, plots and figures created
using your data are automatically repopulated with the data of the users
you share the notebook with, when they run your notebook.

You can read [a more in-depth introduction to Cloud Monitoring
client using Cloud Datalab](https://github.com/googledatalab/notebooks/tree/master/tutorials/Stackdriver%20Monitoring).

This tutorial explores Cloud Bigtable metrics during a loadtest
and while running the [sample code for scaling Cloud Bigtable programmatically](https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/bigtable/autoscaler).

## Prerequisites

This tutorial assumes some familiarity with Python development, including
`virtualenv` and `pip`. Previous knowledge of Google Cloud, Jupyter,
pandas, and Matplotlib is helpful.

## Objectives

1.  Install Jupyter and the Python Stackdriver dependencies.
1.  Explore basic plotting of Bigtable metrics during a scaling event.

## Costs

This tutorial uses billable components of Google Cloud, including:

- Bigtable
- Cloud Monitoring

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Cloud Console][console].
1.  Enable billing for your project.
1.  Install the [Cloud SDK][cloud-sdk].
1.  Create a client ID to run the sample code:

        gcloud auth application-default login

[console]: https://console.cloud.google.com/
[cloud-sdk]: https://cloud.google.com/sdk/

## Getting started

1.  Install Jupyter by following the [installation instructions](http://jupyter.readthedocs.io/en/latest/install.html).

1.  Install `virtualenv` by following the [installation instructions](https://virtualenv.pypa.io/en/stable/installation/).

1.  Create and activate a `virtualenv` virtual environment.

1.  Download [`requirements.txt`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/bigtable-stackdriver/requirements.txt) and use `pip` to install
the required components:

        pip install -r requirements.txt

## Loading the notebook

Download the [tutorial notebook](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/bigtable-stackdriver/monitoring_metrics.ipynb).

With the necessary dependencies installed into the `virtualenv` environment, start a new
Jupyter notebook:

    jupyter notebook

Open the Jupyter notebook in the browser. From there you can follow the tutorial to see
how basic Bigtable metrics are plotted and how they respond to programmatic scaling.
