---
title: Ingest geospatial data from Google Earth Engine to BigQuery
description: Use Cloud Dataflow and geobeam to ingest geospatial raster data from Google Earth Engine to BigQuery.
author: kannappans,remyw
tags: Dataflow, Google Earth Engine, geobeam, BigQuery
date_published: 2022-06-07
---

Remy Welch, Kannappan Sirchabesan | Cloud Data Engineers | Google

Donna Schut | Solutions Manager | Google

Travis Webb | Solutions Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Google Earth Engine is a geospatial processing platform powered by Google Cloud that combines a multi-petabyte catalog of satellite imagery and 
geospatial datasets with planetary-scale analysis capabilities. Earth Engine is used for analyzing forest and water coverage, analyzing land use change,
assessing the health of agricultural fields, and so on.

[geobeam](https://github.com/GoogleCloudPlatform/dataflow-geobeam) is a Python-based framework that provides a set of Apache Beam classes and utilities 
that make it easier to process and transform very large amounts of geospatial data using Google Cloud Dataflow.

This solution uses geobeam to ingest raster TIFF images that have been generated in Earth Engine into BigQuery.

## Objectives

* Import an Earth Engine TIFF image into a Cloud Storage bucket.
* Install the geobeam library.
* Run a geobeam job to ingest the TIFF file from the Cloud Storage bucket to BigQuery.
* Use BigQuery Geo Viz to verify that the TIFF image has been ingested correctly.

## Architecture

![architecture](https://storage.googleapis.com/gcp-community/tutorials/earthengine-to-bigquery/ee2bq_architecture.png)

There are several components to this architecture:

* **Google Earth Engine**: Geospatial data catalog and GIS-like processing service. This is where the GeoTIFF image from the USDA Cropland image 
  collection is exported from. 
* **Cloud Storage**: The exported GeoTIFF image from Earth Engine is stored in a Cloud Storage bucket.        
* **Dataflow**: The GeoTIFF image in the Cloud Storage bucket is processed in Dataflow using geobeam.
* **BigQuery**: The processed image is stored in BigQuery as a set of rows that include the BigQuery geospatial point using the
  [`GEOGRAPHY`](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types#geography_type) data type.

## Set up your project and environment

You can run all of the commands for this solution in [Cloud Shell](https://cloud.google.com/shell) or a
[Vertex AI notebook](https://cloud.google.com/vertex-ai/docs/workbench/introduction), or you can install the 
[gcloud CLI](https://cloud.google.com/sdk/docs/install) and run the commands locally.

1.  To allow for easier cleanup, create a Google Cloud project for this tutorial rather than using an existing project.
1.  [Get access to the Earth Engine API](https://signup.earthengine.google.com/).
1.  Enable the BigQuery API and the Cloud Storage API in the project.
1.  Ensure that you have Python 3.7 or 3.8. 
1.  Install the geobeam library:

        pip install geobeam
    
1.  Install the Earth Engine library:

        pip install earthengine-api

1.  Enable the Earth Engine API:

        gcloud services enable earthengine.googleapis.com

1.  Ensure that you have an existing Cloud IAM service account to run this code, or create a new one and assign appropriate permissions for the service
    account to write to BigQuery and Cloud Storage.

    This shouldn't be necessary if you are running this code from within a Vertex AI notebook or Cloud 
    shell.

1.  Set the following environment variables and replace the values with values corresponding to your project:

        export PROJECT_ID=remy-sandbox
        export IMAGES_BUCKET=tmp_images_bucket_rw3
        export GEOBEAM_BUCKET=tmp_geobeam_bucket_rw3
        export BQ_DATASET=geodata
        export BQ_DATASET_REGION=us-central1
        export BQ_TABLE=tutorial_test
        export SERVICE_ACCOUNT_EMAIL=your_serviceaccount_email

1.  Set the working project:

        gcloud config set project ${PROJECT_ID}
        
1.  Create two Cloud Storage buckets:

        gsutil mb gs://${IMAGES_BUCKET}
        gsutil mb gs://${GEOBEAM_BUCKET}

## Create a BigQuery dataset and table

1.  Create a BigQuery dataset where you will ingest the TIFF file:

        bq --location=${BQ_DATASET_REGION} mk --dataset ${PROJECT_ID}:${BQ_DATASET}

1.  Create a table in the dataset with the schema for the cropland dataset:

        bq mk --table ${PROJECT_ID}:${BQ_DATASET}.${BQ_TABLE} \
        croptype:INT64,geom:GEOGRAPHY

    For GeoTIFF assets, geobeam only ingests one band at a time, so the schema is of the form `[BAND_NAME]:[BAND_DATA_FORMAT],geom:GEOGRAPHY`.

## Download the Earth Engine image

1.  Authenticate to Earth Engine:

        earthengine authenticate

1.  Run the following Python code to export the first image in the USDA Cropland image collection as a TIFF file to the Cloud Storage bucket:

        import ee
        import os


        # Initialize the Earth Engine API
        ee.Initialize()

        # Retrieve the environment variable of the Cloud Storage bucket for storing images
        bucket_name = os.environ['IMAGES_BUCKET']

        # Specify a region in the US (roughly the state of Colorado) to reduce the export time for the sake of example
        colorado = ee.Geometry.Rectangle([-104, 37, -102, 38]);

        # Select the first (and only) image from the Cropland image collection for the year 2019, and the cropland band, which gives us the crop type.
        # Currently, geobeam will only ingest a single band from a GeoTIFF at time.
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
        print('Please wait for 5 minutes for the export to Cloud Storage to complete')

This process takes a couple of minutes.

## Run the geobeam job

1.  Get the credentials for running the geobeam job. This is only necessary if you are running this code from outside of the Google Cloud environment.

        export GOOGLE_APPLICATION_CREDENTIALS="<Path of the keyfile JSON>"

1.  Run the geobeam job to ingest the TIFF file from the Cloud Storage bucket into BigQuery.

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
          --centroid_only true \
          --service_account_email ${SERVICE_ACCOUNT_EMAIL}

    Notes for some of the parameters for the geobeam command above:

    - Make sure to specify the correct image based on the version of Python that you're using. If you're using python 3.8, use the container at 
      `gcr.io/dataflow-geobeam/example`. If you're using Python 3.7, use the container at `gcr.io/dataflow-geobeam/example-py37`. 

    - `band_column`: the name of the band value, as you specified in the `bq` table creation statement

    - `merge_blocks`: ingestion tuning parameter, which controls the area over which similar pixel values are merged

    - `centroid_only`: how to convert a pixel to a `GEOGRAPHY` object; false produces a `POLYGON` object that encompasses the pixel, and true produces a
      `POINT` object at the center of the pixel

The job takes about 11 minutes. 

You can monitor the progress of the Dataflow job in the Cloud Console. The job graph looks similar to the following image: 

![geobeam graph.](https://storage.googleapis.com/gcp-community/tutorials/earthengine-to-bigquery/geobeam_graph.png)

## Verify the data in BigQuery

When the geobeam job finishes, the data has been ingested into BigQuery. You can verify this in the Cloud console by looking at the preview of the 
BigQuery table. The output looks like the following, the `geom` column containing the points of the image as `POINT` objects with the corresponding
latitude and longitude, and the `croptype` column containing the crop type for each point.

![BigQuery data preview.](https://storage.googleapis.com/gcp-community/tutorials/earthengine-to-bigquery/bqdatapreview.png)

### Check BigQuery Geo Viz

Check BigQuery Geo Viz to make sure that the images are similar. As you can see, the points are projected in the correct area in the US.

![BigQuery Geo Viz visualization.](https://storage.googleapis.com/gcp-community/tutorials/earthengine-to-bigquery/bqgeoviz.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this document, you can delete the resources that you created:

1.  Delete the buckets:

        gsutil rm -r gs://${GEOBEAM_BUCKET}
        gsutil rm -r gs://${IMAGES_BUCKET}

1.  Delete the entire project:

        gcloud projects delete ${PROJECT_ID}
