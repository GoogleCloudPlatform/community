---
title: Export a custom AutoML Tables model and serve it with Cloud Run
description: Learn how to export a custom AutoML Tables model and serve it with Cloud Run or any other environment where you can run a container.
author: amygdala
tags: ML, machine learning, TensorBoard
date_published: 2020-08-18
---

With [AutoML Tables](https://cloud.google.com/automl-tables/docs/), you can automatically build and deploy state-of-the-art machine-learning models using your
own structured data. See [this notebook](https://cloud.google.com/blog/products/ai-machine-learning/use-automl-tables-from-a-jupyter-notebook) for a walkthrough.

AutoML Tables includes a feature with which you can [export](https://cloud.google.com/automl-tables/docs/model-export) your full custom model, packaged such that
you can serve it with a Docker container. This lets you serve your models anywhere that you can run a container.

This tutorial shows you how to package an exported AutoML Tables model to serve on [Cloud Run](https://cloud.google.com/run/docs/). With Cloud Run, your model 
serving automatically scales up with traffic and scales down to 0 when it’s not being used. This tutorial also shows how you can examine your trained custom 
model in [TensorBoard](https://www.tensorflow.org/tensorboard).

This tutorial uses the [Cloud Console](https://console.cloud.google.com/automl-tables/datasets), but you could also accomplish the same steps through the 
command-line interface or using the [AutoML Tables client libraries](https://googleapis.dev/python/automl/latest/gapic/v1beta1/tables.html).

## About the dataset and scenario

The [Cloud Public Datasets Program](https://cloud.google.com/bigquery/public-data/) makes available public datasets that are useful for experimenting with 
machine learning. Just as in
[Explaining model predictions on structured data](https://cloud.google.com/blog/products/ai-machine-learning/explaining-model-predictions-structured-data),
this tutorial uses data that is essentially a join of two public datasets stored in
[BigQuery](https://cloud.google.com/bigquery/)--[London bike rentals](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=london_bicycles&page=dataset) and
[NOAA weather data](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=noaa_gsod&page=dataset)--with some additional processing to clean up 
outliers and derive additional GIS and day-of-week fields. 

You’ll use this dataset to build a _regression model_ to predict the duration of a bike rental based on information about the start and end stations, the day of 
the week, the weather on that day, and other data. If you were running a bike rental company, for example, these predictions and their explanations could help 
you to anticipate demand and plan how to stock each location.

You can use AutoML Tables for tasks as varied as asset valuations, fraud detection, credit risk analysis, customer retention prediction, and analyzing item 
layouts in stores.

## Create a dataset

The first step in training a Tables model is to create a *dataset* using your data. This tutorial uses the bike rentals and weather dataset described above. You
can also follow along with your own tabular dataset, but in that case you’ll need to construct your own prediction instances, too. 

1.  Visit the [**Tables** page](https://console.cloud.google.com/automl-tables/datasets) in the Cloud Console, and enable the API as necessary.

    ![Enable the AutoML Tables API](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/enable_api.png)

1.  Create a new Tables dataset.

    ![Create a new Tables dataset](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/create_dataset.png)

1.  Import your data into the dataset.

    To ingest the example data, select **Import data from BigQuery** and enter `aju-dev-demos` as the BigQuery Project ID, `london_bikes_weather` as the
    dataset ID, and `bikes_weather` as the table name.

    ![Import the data](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/import_data.png)
    
## Edit the dataset’s schema

After the import is complete, you edit the dataset schema. You'll need to change a few of the inferred types.

Make sure that your schema reflects what’s in the figure below:

1.  Change `bike_id`, `end_station_id`, `start_station_id`, and `loc_cross` to be of type **Categorical**.
1.  Select `duration` as in the **Target column** section. 

![Adjust the dataset schema](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/schema.png)

Useful statistics are generated for the columns, including correlation statistics with the target column, which can help you determine which columns you want
to use as model inputs.

## Train the Tables model

Now you're ready to train a model on the dataset.  

You'll train a model to predict ride duration given all the other dataset inputs, so you'll train a
[regression](https://cloud.google.com/automl-tables/docs/problem-types) model. 

For this example, enter a training budget of 1 hour, and include all available feature columns.

![Train a model to predict ride](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/train.png)

## Export the trained model

After the model is trained, you export the result, so that it can be served from any environment in which you can run a container. Alternatively, you could
[deploy](https://cloud.google.com/automl-tables/docs/predict) your model to AI Platform for online prediction.

You'll find the export option under **TEST & USE**. (See the [documentation](https://cloud.google.com/automl-tables/docs/model-export) for detail on the export process). Click the "**Container**" card to export your trained model to be run from a Docker container.  You'll need to use a *regional* GCS bucket, in the same region as your model. 

You also might want to create a sub-folder for the model export in the GCS bucket, so that if you have multiple exports, you can keep track of .  An easy way to create the folder is via the web UI, as we’ve done here with the `model_export_1` sub-folder.

![Export trained model to be run from Docker container](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/export1.png)

Click the "Container" card to export your trained model to be run from a Docker container.

Then, browse to select the Google Cloud Storage folder into which you want to export your model and click the **EXPORT** button.

![Browse to Cloud Storage folder to export model](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/export2.png)

When the export is finished, create a local directory, like `bikes_weather`, to hold your model.

Copy the download command provided in the cloud console, which will look something like the following:
`gsutil cp -r gs://<your-bucket>/model_export_1//* ./download_dir`

Then, edit this command: add quotes around the `gs` URI, and remove one of the end slashes.  Then edit `download_dir` to point to the directory you created.  The result should look something like the following. Run it from the parent directory of your `bikes_weather` directory:

```sh
gsutil cp -r 'gs://<your-bucket>/model_export_1/*' ./bikes_weather
```

The exported model will be copied to `./bikes_weather`.

**Note**: to run `gsutil`, you will need [`gcloud`](https://cloud.google.com/sdk/install) installed. You can run these commands from the [Cloud Shell](https://cloud.google.com/shell/) instead of your local machine if you don't want to install the SDK locally.

## Test your exported model locally

After you've downloaded your model, you can run and test it locally. This provides a good check before deploying to Cloud Run.
The process is described in detail in the [AutoML Tables documentation](https://cloud.google.com/automl-tables/docs/model-export).

- change to the `bikes_weather` directory. You should see a `model_export` subdirectory, which is the result of your download.
- rename the `model_export/tbl/tf_saved_model*` subdirectory to remove the timestamp suffix.

Then, create and run a container to serve your new trained model.  Edit the following to point to your renamed directory path:

```sh
docker run -v `pwd`/model-export/tbl/<your_renamed_directory>:/models/default/0000001 -p 8080:8080 -it gcr.io/cloud-automl-tables-public/model_server
```

This starts up a model server to which you can send requests.  Note that we're using the `gcr.io/cloud-automl-tables-public/model_server` container image and mounting our local directory.

Next, download or navigate to the `instances.json` file, which holds data for three prediction instances for the “bikes & weather” model.
From the directory where you placed `instances.json`, run:

```sh
curl -X POST --data @instances.json http://localhost:8080/predict
```

You’ll get back predictions for all of the instances in the `json` file.   
The actual duration for the third instance is 1200.

## View information about your exported model in TensorBoard

You can view your exported custom model in [TensorBoard](https://www.tensorflow.org/tensorboard).  This requires a conversion step. 
You will need to have TensorFlow 1.14 or 1.15 [installed](https://www.tensorflow.org/install/pip#2.-create-a-virtual-environment-recommended) to run the the conversion script.

Then, download or navigate to the `convert_oss.py` script.  Copy it to the parent directory of `model_export`.  Create a directory for the output (e.g. `converted_export`), then run the script as follows:

```sh
mkdir converted_export
python ./convert_oss.py --saved_model ./model-export/tbl/<your_renamed_directory>/saved_model.pb --output_dir converted_export
```

**The script requires TensorFlow 1.x**.  Then, point TensorBoard to the converted model:

```sh
tensorboard --logdir=converted_export
```
You can view an exported custom Tables model in Tensorboard.

You will see a rendering of the model graph, and can pan and zoom to view model sub-graphs in more detail.

![View exported custom Tables model in Tensorboard](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/tb1.png)

![](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/tb2.png)

Zooming in to see part of the model graph in more detail.

![Zooming in to see part of the model graph in more detail](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/tb3.png)

## Create a Google Cloud Run service based on your exported model

At this point, we have a trained model that we've exported and tested locally.  Now we are almost ready to deploy it to [Cloud Run](https://cloud.google.com/run/docs/). As the last step of prep, we'll create a container image that uses `gcr.io/cloud-automl-tables-public/model_server` as a base image and `ADD`s the model directory, and push that image to the [Google Container Registry](https://cloud.google.com/container-registry/), so that Cloud Run can access it.

### Build a container to use for Cloud Run

In the same `bikes_weather` directory that holds the `model_export` subdir, create a file called `Dockerfile` that contains the following two lines.  The template is in `./Dockerfile.template` as well. **Edit the second line to use your correct path to the exported model, the same path that you used above when running locally**.

```
FROM gcr.io/cloud-automl-tables-public/model_server

ADD model-export/tbl/YOUR_RENAMED_DIRECTORY/models/default/0000001
```

Then, build a container from the `Dockerfile`.  In this example we'll call it `bw-serve`.
You can do this as follows (**replace `[PROJECT_ID]` with the id of your project**):

```bash
docker build . -t gcr.io/[PROJECT_ID]/bw-serve
```

Next, push it to the Google Container Registry (again replacing `[PROJECT_ID]` with the id of your project):

```bash
docker push gcr.io/[PROJECT_ID]/bw-serve
```

If you get an error, you may need to configure Docker to use `gcloud` to [authenticate requests to Container Registry](https://cloud.google.com/container-registry/docs/quickstart#add_the_image_to).

Alternately, you can use [Cloud Build](https://cloud.google.com/cloud-build/docs/quickstart-docker) to build the container instead, as follows:

```bash
gcloud builds submit --tag gcr.io/[PROJECT_ID]/bw-serve .
```

### Create your Cloud Run service

Now we're ready to deploy the container we built to Cloud Run, where we can scalably serve it for predictions.  Visit the [Cloud Run page in the console](https://console.cloud.google.com/marketplace/details/google-cloud-platform/cloud-run). (Click the “START USING..” button if necessary).  Then click the **CREATE SERVICE** button.

![Creating a Cloud Run Service](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/cloud_run1.png)

For the container URL, enter the name of the container that you just built above. Select the “Cloud Run (fully managed)” option.  Create a service name (it can be anything you like). Select the **Require Authentication** option. Then, click on **SHOW OPTIONAL REVISION SETTINGS**.  Change the **Memory allocated** option to **2GiB**. Leave the rest of the defaults as they are, and click **CREATE**.

![Set service instances to use 2GiB of memory](https://storage.googleapis.com/gcp-community/tutorials/automl-tables-model-export/cloud_run2.png)

### Send prediction requests to the Cloud Run service

After your Cloud Run service is deployed, you can send prediction requests to it. Your new service has a URL that starts with your service name and ends
with `run.app`. You can send JSON predictions to the Cloud Run service just as with the local server you tested earlier; but with Cloud Run, the service will
scale up and down based on demand. 

Assuming that you selected the **Require Authentication** option, you can make prediction requests like this:

```bash
curl -X POST -H \
"Authorization: Bearer $(gcloud auth print-identity-token)" --data @./instances.json \
https:/[YOUR_SERVICE_URL]/predict
```

It may take a second or two for the first request to return, but subsequent requests will be faster.

If you set up your Cloud Run service endpoint so that it does not require authentication, you don’t need to include the authorization header in your `curl` 
request.

## What’s next?

In this tutorial, you saw how to export a custom AutoML Tables trained model, view model information in TensorBoard, and build a container image that lets you serve the model from any environment. Then you saw how you can deploy that image to Cloud Run for scalable serving. See the
[Cloud Run documentation](https://cloud.google.com/run/docs/authenticating/overview) for more information on how to configure your prediction endpoint for
end-user or service-to-service authentication.

Once you’ve built a model-serving container image, you can deploy it to other environments as well. For example, if you have installed
[Knative serving](https://github.com/knative/serving) on a [Kubernetes](https://kubernetes.io/) cluster, you can create a Knative *service* like this, using the 
same container image (replacing `[PROJECT_ID]` with your project):

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: bikes-weather
spec:
  template:
    spec:
      containers:
        - image: gcr.io/[PROJECT_ID]/bw-serve
```

Though the example model for this tutorial fits on a 2-GiB Cloud Run instance, you might have models that are too large for the managed Cloud Run service, and 
serving it with Kubernetes/GKE is a good alternative.

If you’re curious about the details of your custom model, you can use Cloud Logging to
[view information about your AutoML Tables model](https://cloud.google.com/automl-tables/docs/logging). Using Cloud Logging, you can see the final model 
hyperparameters and the hyperparameters and object values used during model training and tuning.

You may also be interested in exploring the updated [AutoML Tables client libraries](https://googleapis.dev/python/automl/latest/gapic/v1beta1/tables.html), 
which make it easy for you to
[train and use Tables programmatically](https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/tables/automl/notebooks), or reading about how to create a _contextual bandit_ model pipeline
[using AutoML Tables, without needing a specialist for tuning or feature engineering](https://cloud.google.com/blog/products/ai-machine-learning/how-to-build-better-contextual-bandits-machine-learning-models).
