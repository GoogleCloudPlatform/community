# Data Science on Google Cloud Platform

Data Science - a process for gleaning insight from data, and using said data to
perform actions - comprises a number of steps, any (or all) of which can aided
by tools provided by the Google Cloud Platform.

[Google Cloud Platform](https://cloud.google.com) provides a grip of tools to
enable you to glean actionable insight from arbitrarily large sets of data. To
explore these tools in the Data Science context, it's helpful to enumerate the
steps of which Data Science is commonly comprised. To wit:

* *Data collection*
  [![Pub/Sub](../../resources/images/pubsub.png "Pub/Sub")][pubsub]
  [![App Engine](../../resources/images/gae.png "App Engine")][appengine]
  [![Logging](../../resources/images/logging.png "Logging")][logging]
  [![Storage](../../resources/images/gcs.png "Storage")][gcs]
  [![BigQuery](../../resources/images/bigquery.png "BigQuery")][bigquery]
* Data extraction & transformation
  [![Vision API](../../resources/images/vision.png "Vision API")][vision]
  [![Speech API](../../resources/images/speech.png "Speech API")][speech]
  [![Translate API](../../resources/images/translate.png "Translate API")][translate]
  [![Natural Language API](../../resources/images/language.png "Natural Language API")][nl]
  * [Extracting data from audio and text](extraction.md)
* Cleaning & preprocessing
  [![Cloud Dataprep](../../resources/images/dataprep.png "Cloud Dataprep")][dataprep]
  [![Cloud Dataflow](../../resources/images/dataflow.png "Cloud Dataflow")][dataflow]
  [![Dataproc](../../resources/images/dataproc.png "Dataproc")][dataproc]
  [![Apache Beam](../../resources/images/beam.png "Apache Beam")][beam]
  * [Cleaning & preprocessing in a pipeline](preprocessing.md)
* Exploration
  [![BigQuery](../../resources/images/bigquery.png "BigQuery")][bigquery]
  [![Cloud DataLab](../../resources/images/datalab.png "Cloud DataLab")][datalab]
  * [Exploring data in BigQuery](bigquery.md)
* *Sharing, collaboration, visualization*
  [![Cloud DataLab](../../resources/images/datalab.png "Cloud DataLab")][datalab]
  [![Jupyter Notebooks](../../resources/images/jupyter.png "Jupyter Notebooks")][jupyter]
  [![Data Studio](../../resources/images/datastudio.png "Data Studio")][datastudio]
* *Using data to train machines to do your dirty work*
  [![Cloud Machine Learning](../../resources/images/ml.png "Cloud Machine Learning")][ml-engine]
  [![Tensorflow](../../resources/images/tensorflow.png "Tensorflow")][tf]

[comment]:# (Some suggested article titles)
[comment]:# (* A/B testing with Google App Engine and Cloud Logging)
[comment]:# (* Scalable, subscribable data feeds using Cloud Pub/Sub)
[comment]:# (* Visualizations with interactive Jupyter [née iPython] notebooks on Cloud Datalab)
[comment]:# (* Presentations and dashboards using Data Studio)
[comment]:# (* Serving infrastructure)
[comment]:# (* Training and serving machine-learning models on Cloud ML Engine)

This document (like Data Science) is a work in progress, and as such is not
comprehensive in its mapping of Data Science steps to available tools. Please
contribute where there are gaps :-)

[appengine]: http://g.co/cloud/appengine
[beam]: http://beam.apache.org
[bigquery]: http://g.co/cloud/bigquery
[dataflow]: http://g.co/cloud/dataflow
[datalab]: http://g.co/cloud/datalab
[dataprep]: http://g.co/cloud/dataprep
[dataproc]: http://g.co/cloud/dataproc
[datastudio]: http://datastudio.google.com
[gcs]: http://g.co/cloud/storage
[jupyter]: http://jupyter.org
[logging]: http://g.co/cloud/logging
[ml-engine]: http://g.co/cloud/ml-engine
[nl]: http://g.co/cloud/natural-language
[pubsub]: http://g.co/cloud/pubsub
[speech]: http://g.co/cloud/speech
[tf]: http://tensorflow.org
[translate]: http://g.co/cloud/translate
[vision]: http://g.co/cloud/vision
