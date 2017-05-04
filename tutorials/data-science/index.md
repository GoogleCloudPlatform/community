# Data Science on Google Cloud Platform

Data Science - a process for gleaning insight from data, and using said data to
perform actions - comprises a number of steps, any (or all) of which can aided
by tools provided by the Google Cloud Platform.

[Google Cloud Platform](https://cloud.google.com) provides a grip of tools to
enable you to glean actionable insight from arbitrarily large sets of data. To
explore these tools in the Data Science context, it's helpful to enumerate the
steps of which Data Science is commonly comprised. To wit:

* *Data collection*
  [<img src="../../resources/images/pubsub.png" title="Pub/Sub" height=25 align=center />][pubsub]
  [<img src="../../resources/images/gae.png" title="App Engine" height=25 align=center />][appengine]
  [<img src="../../resources/images/logging.png" title="Logging" height=25 align=center />][logging]
  [<img src="../../resources/images/gcs.png" title="Storage" height=25 align=center />][gcs]
  [<img src="../../resources/images/bigquery.png" title="BigQuery" height=25 align=center />][bigquery]
* Data extraction & transformation
  [<img src="../../resources/images/vision.png" title="Vision API" height=25 align=center />][vision]
  [<img src="../../resources/images/speech.png" title="Speech API" height=25 align=center />][speech]
  [<img src="../../resources/images/translate.png" title="Translate API" height=25 align=center />][translate]
  [<img src="../../resources/images/language.png" title="Natural Language API" height=25 align=center />][nl]
  * [Extracting data from audio and text](extraction.md)
* Cleaning & preprocessing
  [<img src="../../resources/images/dataprep.png" title="Cloud Dataprep" height=25 align=center />][dataprep]
  [<img src="../../resources/images/dataflow.png" title="Cloud Dataflow" height=25 align=center />][dataflow]
  [<img src="../../resources/images/dataproc.png" title="Dataproc" height=25 align=center />][dataproc]
  [<img src="../../resources/images/beam.png" title="Apache Beam" height=25 align=center />][beam]
  * [Cleaning & preprocessing in a pipeline](preprocessing.md)
* Exploration
  [<img src="../../resources/images/bigquery.png" title="BigQuery" height=25 align=center />][bigquery]
  [<img src="../../resources/images/datalab.png" title="Cloud DataLab" height=25 align=center />][datalab]
  * [Exploring data in BigQuery](bigquery.md)
* *Sharing, collaboration, visualization*
  [<img src="../../resources/images/datalab.png" title="Cloud DataLab" height=25 align=center />][datalab]
  [<img src="../../resources/images/jupyter.png" title="Jupyter Notebooks" height=25 align=center />][jupyter]
  [<img src="../../resources/images/datastudio.png" title="Data Studio" height=25 align=center />][datastudio]
* *Using data to train machines to do your dirty work*
  [<img src="../../resources/images/ml.png" title="Cloud Machine Learning" height=25 align=center />][ml-engine]
  [<img src="../../resources/images/tensorflow.png" title="Tensorflow" height=25 align=center />][tf]

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
