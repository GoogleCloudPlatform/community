---
title: Data science on Google Cloud
description: Use Google Cloud tools to automate, share, and scale data science workflows.
author: jerjou
tags: Data Science
date_published: 2017-05-23
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Data science - gleaning insight from data to perform and inform action -
comprises a number of steps, any (or all) of which can aided by tools provided
by the Google Cloud.

[Google Cloud](https://cloud.google.com) provides a set of tools to
enable you to glean actionable insight from arbitrarily large sets of data. To
explore these tools in the Data Science context, it's helpful to enumerate the
steps of which data science is commonly comprised. To wit:

* **Data collection**
  [![Pub/Sub](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Cloud-PubSub_25.png "Pub/Sub")][pubsub]
  [![App Engine](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/compute/App-Engine_25.png "App Engine")][appengine]
  [![Logging](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/management_tools/Logging_25.png "Logging")][logging]
  [![Storage](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/storage_and_databases/Cloud-Storage_25.png "Storage")][gcs]
  [![BigQuery](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/BigQuery_25.png "BigQuery")][bigquery]

* **Data extraction & transformation**
  [![Vision API](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/machine_learning/Cloud-Vision-API_25.png "Vision API")][vision]
  [![Speech API](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/machine_learning/Cloud-Speech-API_25.png "Speech API")][speech]
  [![Translate API](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/machine_learning/Cloud-Translation-API_25.png "Translate API")][translate]
  [![Natural Language API](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/machine_learning/Cloud-Natural-Language-API_25.png "Natural Language API")][nl]

    + [Extracting data from audio and text](/community/tutorials/data-science-extraction)

* **Cleaning & preprocessing**
  [![Cloud Dataprep](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Cloud-Dataprep_25.png "Cloud Dataprep")][dataprep]
  [![Cloud Dataflow](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Cloud-Dataflow_25.png "Cloud Dataflow")][dataflow]
  [![Dataproc](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Cloud-Dataproc_25.png "Dataproc")][dataproc]
  [![Apache Beam](https://storage.googleapis.com/gcp-community/tutorials/data-science/beam.png "Apache Beam")][beam]

    + [Cleaning & preprocessing in a pipeline](/community/tutorials/data-science-preprocessing)

* **Exploration**
  [![BigQuery](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/BigQuery_25.png "BigQuery")][bigquery]
  [![Cloud DataLab](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Cloud-Datalab_25.png "Cloud DataLab")][datalab]

   + [Exploring data in BigQuery](/community/tutorials/data-science-exploration)

* **Sharing, collaboration, visualization**
  [![Cloud DataLab](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Cloud-Datalab_25.png "Cloud DataLab")][datalab]
  [![Jupyter Notebooks](https://storage.googleapis.com/gcp-community/tutorials/data-science/jupyter.png "Jupyter Notebooks")][jupyter]
  [![Data Studio](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/big_data/Data-Studio_25.png "Data Studio")][datastudio]

* **Using data to train machines to do your dirty work**
  [![Cloud Machine Learning](https://storage.googleapis.com/gcp-community/resources/gcp_icons/products_and_services/machine_learning/Cloud-Machine-Learning_25.png "Cloud Machine Learning")][ml-engine]
  [![Tensorflow](https://storage.googleapis.com/gcp-community/tutorials/data-science/tensorflow.png "Tensorflow")][tf]

[comment]:# (Some suggested article titles)
[comment]:# (* A/B testing with Google App Engine and Cloud Logging)
[comment]:# (* Scalable, subscribable data feeds using Cloud Pub/Sub)
[comment]:# (* Visualizations with interactive Jupyter [née iPython] notebooks on Cloud Datalab)
[comment]:# (* Presentations and dashboards using Data Studio)
[comment]:# (* Serving infrastructure)
[comment]:# (* Training and serving machine-learning models on Cloud ML Engine)

This document (like data science) is a work in progress, and as such is not
comprehensive in its mapping of Data Science steps to available tools. Please
contribute where there are gaps.

[appengine]: /appengine
[beam]: http://beam.apache.org
[bigquery]: /bigquery
[dataflow]: /dataflow
[datalab]: /datalab
[dataprep]: /dataprep
[dataproc]: /dataproc
[datastudio]: http://datastudio.google.com
[gcs]: /storage
[jupyter]: http://jupyter.org
[logging]: /logging
[ml-engine]: /ml-engine
[nl]: /natural-language
[pubsub]: /pubsub
[speech]: /speech
[tf]: http://tensorflow.org
[translate]: /translate
[vision]: /vision
