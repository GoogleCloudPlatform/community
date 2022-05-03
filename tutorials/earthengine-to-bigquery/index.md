---
title: Ingest data from Google Earth Engine to BigQuery
description: Use Cloud Dataflow and GeoBeam to ingest raster image data(TIFF files) from Google Earth Engine to BigQuery. 
author: kannappans, remyw
tags: Dataflow, Google Earth Engine, GeoBeam, BigQuery
date_published: 2022-03-31
---

Authors: Remy Welch, Kannappan Sirchabesan | Cloud Data Engineers | Google  
Collaborator: Donna Schut | Solutions Manager | Google  
Collaborator: Travis Webb | Solutions Engineer | Google  

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Google Earth Engine is a geospatial processing platform powered by Google Cloud that combines a multi-petabyte catalog of satellite imagery and geospatial datasets with planetary-scale analysis capabilities. Earth Engine is used for analyzing forest and water coverage, analyzing land use change, assessing the health of agricultural fields, etc.

[geobeam](https://github.com/GoogleCloudPlatform/dataflow-geobeam) is a Python-based framework that provides a set of Apache Beam classes and utilities that make it easier to process and transform massive amounts of geospatial data using Google Cloud Dataflow. 

This solution uses geobeam to ingest raster TIFF images that have been generated in Earth Engine into BigQuery. 

## Objectives

* Import a Earth Engine TIFF image into a Cloud Storage bucket.
* Install the geobeam library.
* Run a geobeam job to ingest the TIFF file from the Cloud Storage bucket to BigQuery.
* Use BigQuery Geo Viz to verify that the TIFF image has been ingested correctly.

## Architecture

![architecture](image/ee2bq_architecture.png)

There are several components to this architecture:

* Google Earth Engine: Geospatial data catalog and GIS-like processing service. This is where the GeoTIFF image from the USDA Cropland image collection is exported from. 
* Cloud Storage: The exported GeoTIFF image from Earth Engine is stored in a Cloud Storage bucket.        
* Dataflow: The GeoTIFF image in the Cloud Storage bucket is processed in Dataflow using geobeam.
* BigQuery: The processed image is stored in BigQuery as a set of rows that include the BigQuery geospatial point using the [GEOGRAPHY](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types#geography_type) data type.

## Before you begin

You can run all the commands for this solution in [Cloud Shell](https://cloud.google.com/shell), or a [Vertex Notebook](https://cloud.google.com/vertex-ai/docs/workbench/introduction), or you can install the 
[gcloud CLI](https://cloud.google.com/sdk/docs/install) and run the commands locally.

1.  Create a Google Cloud project for this tutorial to allow for easier cleanup.
2.  [Get access](https://signup.earthengine.google.com/) to the Earth Engine API.
3.  Enable the BigQuery API and the Cloud Storage API in the project.
4.  Ensure you have Python 3.7 or 3.8. 
5.  Install the geobeam library:
    ```
    pip install geobeam
    ```
6.  Install the Earth Engine library:
    ```
    pip install earthengine-api
    ```
7.  Enable the Earth Engine API:
    ```
    gcloud services enable earthengine.googleapis.com
    ```
8.  Ensure you have an existing Cloud IAM service account to run this code, or create a new one and assign appropriate permissions for the service account to write to BigQuery and Cloud Storage. This shouldn't be necessary if you are running this code from within a GCP notebook or Cloud shell.

### Set environment variables

Set the following environment variables and replace the values with values corresponding to your project.
```
export PROJECT_ID=remy-sandbox
export IMAGES_BUCKET=tmp_images_bucket_rw3
export GEOBEAM_BUCKET=tmp_geobeam_bucket_rw3
export BQ_DATASET=geodata
export BQ_DATASET_REGION=us-central1
export BQ_TABLE=tutorial_test
export SERVICE_ACCOUNT_EMAIL=serviceaccount email
```

### Create Cloud Storage buckets

Create two buckets:
```
gcloud config set project ${PROJECT_ID}
gsutil mb gs://${IMAGES_BUCKET}
gsutil mb gs://${GEOBEAM_BUCKET}
```

### Create a BigQuery dataset

*   Create a BigQuery dataset where you want to ingest the TIFF file:
```
bq --location=${BQ_DATASET_REGION} mk \
--dataset ${PROJECT_ID}:${BQ_DATASET}
```
*   Create a table in the dataset with the schema for the cropland dataset. At this time, for GeoTIFFs, geobeam will only ingest one band at a time, so the schema should be 'bandname':{band data format},'geom':GEOGRAPHY
```
bq mk \
--table \
${PROJECT_ID}:${BQ_DATASET}.${BQ_TABLE} \
croptype:INT64,geom:GEOGRAPHY
```

### Download the Earth Engine image

Authenticate to Earth Engine:
```
earthengine authenticate
```

Run the following Python code to export the first image in the USDA Cropland image collection as a TIFF file to the Cloud Storage bucket. This process takes a couple of minutes.
```
import ee
import os

# Initialize the Earth Engine API
ee.Initialize()

# Retrieve the environment variable of GCS bucket for storing images
bucket_name = os.environ['IMAGES_BUCKET']

# Specify a region in the US (roughly the state of Colorado) to reduce the export time for the sake of example
colorado = ee.Geometry.Rectangle([-104, 37, -102, 38]);

# Select the first (and only) image from the Cropland image collection for the year 2019, and the cropland band, which gives us the crop type. Currently, Geobeam will only ingest a single band from a GeoTIFF at time.
image = ee.ImageCollection('USDA/NASS/CDL').filter(ee.Filter.date('2019-01-01', '2019-01-02')).first();
cropland = image.select('cropland');
task_config = {
    'description': 'cropland',
    'crs': 'EPSG:4326',  # specify this projection to ensure Biquery can ingest it properly
    'scale': 30, # also necessary to specify scale when reprojecting (30m is the original dataset scale)
    'bucket': bucket_name,
    'fileNamePrefix': 'croplandExport',
    'region': colorado,
    'maxPixels': 1e12 #increase max pixels limit for exports 
}

task = ee.batch.Export.image.toCloudStorage(cropland, **task_config)
task.start()
print('Please wait for 5 minutes for the export to GCS to complete')
```

### Run the geobeam job

Get the credentials for running the geobeam job. This is only necessary if you are running this code from outside of the GCP environment.

```
export GOOGLE_APPLICATION_CREDENTIALS="<Path of the keyfile JSON>"
```

Run the GeoBeam job to ingest the TIFF file from the Cloud Storage bucket into BigQuery. The job takes about 11 minutes. 
Make sure to specify the correct image based on the version of python you are using. If using python 3.8, use the container at gcr.io/dataflow-geobeam/example, if using python 3.7, use gcr.io/dataflow-geobeam/example-py37. 

Geobeam parameters:

**band_column** - the name of the band value, as you specified in the bq table creation statement

**merge_blocks** - ingestion tuning parameter. Increases the area over which similar pixel values are merged

**centroid_only** - how to convert a pixel to a GEOGRAPHY. false will produce a POLYGON that encompasses the pixel, true will produce a POINT at the center of the pixel

```
python -m geobeam.examples.crop_geotiff \
  --runner DataflowRunner \
  --worker_harness_container_image gcr.io/dataflow-geobeam/example \
  --experiment use_runner_v2 \
  --project ${PROJECT_ID} \
  --temp_location gs://${GEOBEAM_BUCKET}/ \
  --region ${BQ_DATASET_REGION} \
  --gcs_url gs://${IMAGES_BUCKET}/croplandExport.tif \ 
  --dataset ${BQ_DATASET} \
  --table ${BQ_TABLE} \
  --band_column croptype \
  --max_num_workers 4 \
  --machine_type c2-standard-4 \
  --merge_blocks 10 \
  --centroid_only true
  
```
# --service_account_email ${SERVICE_ACCOUNT_EMAIL} \
You can monitor the progress of the Dataflow job in the Cloud Console. The job graph looks similar to the following image: 

![geobeam graph.](image/geobeam_graph.png)

### Verify the data in BigQuery

When the geobeam job finishes, the data has been ingested into BigQuery. You can verify this in the Cloud Console by looking at the preview of the BigQuery table. The output looks like the following, the `geom` column containing the points of the image as POINT objects with the corresponding latitude and longitude, and the `croptype` column containing the crop type for each point.

![BigQuery data preview.](image/bqdatapreview.png)

### Check BigQuery Geo Viz

Check BigQuery Geo Viz to make sure that the images are similar. As you can see, the points are projected in the correct area in the US.

![BigQuery Geo Viz visualization.](image/bqgeoviz.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this document, you can delete the resources that you created:

```
gsutil rm -r gs://${GEOBEAM_BUCKET}
gsutil rm -r gs://${IMAGES_BUCKET}
# Delete the entire project
gcloud projects delete ${PROJECT_ID}
```
