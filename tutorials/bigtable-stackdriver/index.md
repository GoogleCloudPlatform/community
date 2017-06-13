---
title: Using matplotlib to visualize Stackdriver metrics for Bigtable
description: Learn about using matplotlib to plot Stackdriver metrics for Bigtable
author: waprin
tags: Stackdriver, Bigtable, matplotlib
date_published: 2017-06-13
---

[Google Stackdriver Monitoring](https://cloud.google.com/monitoring/docs/) is
a service that collects metrics, events, and metadata from Google Cloud Platform or
Amazon Web Services (AWS).

Stackdriver Monitoring comes with a built in console for exploring metrics and
plotting figures. The console can be found by first going to the
[Google Cloud Console](https://console.cloud.google.com), clicking on the
top left menu navigation, selecting Monitoring, then clicking through
the various screens.

Many useful charts will automatically be created for you, and many more custom
graphs can be built within the Stackdriver console. For
[Google Cloud Bigtable](https://cloud.google.com/bigtable/), some charts can
be found in the Bigtable console, as well as in the Stackdriver
'Metrics Explorer'.

However, as an alternative
approach, the Python library `matplotlib` can be uesd in conjunction with the
[Google Cloud Python client library](https://github.com/GoogleCloudPlatform/google-cloud-python/tree/master/monitoring)
and its built-in integration with the  [pandas](http://pandas.pydata.org/)
data science library to make sophisticated graphs. This tutorial demonstrates
 some simple plotting to get started, in conjunction with the Bigtable
 autoscaler sample.

The Stackdriver Python client library can be used either in vanilla
[Jupyter](http://jupyter.org/) notebooks or with
[Google Cloud Datalab](https://cloud.google.com/datalab/). This tutorial
focuses on vanilla Jupyter.

Jupyter notebook allow you to create interactive, annotated notebooks that
can be shared with others. Since the sample notebook relies on default
authentication and project configurations, plots and figures created
with your data will be automatically re-populated with the data of the users
you share the notebook with when they run your notebook.

Follow this link for [a more in-depth introduction to Stackdriver Monitoring
client using Cloud Datalab](https://github.com/googledatalab/notebooks/tree/master/tutorials/Stackdriver%20Monitoring).

## Prerequisites

This tutorial assumes some familiarity with Python development, including
virtualenv and pip. Previous knowledge of Google Cloud Platform, Jupyter,
pandas, and matplotlib will also be helpful.

## Objectives

1.  Install Jupyter and the Python Stackdriver dependencies
1.  Explore basic plotting of Cloud Bigtable metrics during an autoscaling event

## Costs

This tutorial uses billable components of Google Cloud Platform, including:

- Google Cloud Bigtable
- Google Stackdriver Monitoring

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK][cloud-sdk].
1.  Create a client ID to run the sample code:

     gcloud auth application-default login

[console]: https://console.cloud.google.com/
[cloud-sdk]: https://cloud.google.com/sdk/

## Getting started

1.  Install Jupyter by following the [installation instructions](jupyter).

1. Install virtualenv by following the [installation instructions](virtualenv)

1. Create and activate a virtualenv

1. Download the ['requirements.txt`](requirements.txt) and use `pip` to install
the requirements:

    pip install -r requirements.txt

[jupyter]: http://jupyter.readthedocs.io/en/latest/install.html
[virutalenv]: https://virtualenv.pypa.io/en/stable/installation/

## Loading the notebook

Download the [tutorial notebook](monitoring_metrics.ipynb).

With the necessary dependencies installed into the virtualenv, start a new
Jupyter notebook:

    jupyter notebook

Open the Jupyter notebook in the browser. From there you can follow the
 tutorial to see how basic Bigtable metrics were plotted, and how they
 responded to autosacling.
