---
title: AVRO/CSV Import to BigQuery from Cloud Storage with a Cloud Function
description: Use this Cloud Function to import AVRO or CSV files in Google Cloud Storage
author: mikekahn
tags: Cloud Functions, BigQuery, Cloud Storage
date_published: 2018-05-06
---
## Introduction

This use of a [Cloud Function][function] demonstrates a serverless cron
scheduled import for data management or data science workflows. The use case
would be, a 3rd party provides data uploaded to a cloud storage bucket on
regular basis in GCP project. Instead of manually importing the CSV or AVRO to
BigQuery each day, we use a cloud function with a trigger on
[object.finalize][finalize] on a set bucket.  This way whenever a CSV or AVRO is
uploaded to that bucket, the function is triggered and the file is imported to a
new BQ table to the specified dataset.

![Cloud Function AVRO import workflow](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-avro-import-bq/cloud-function-import.png)

[function]: https://cloud.google.com/functions/docs/
[finalize]: https://cloud.google.com/functions/docs/calling/storage#object_finalize

Here is how to set it up:

## Instructions:

1.  Enable cloud functions, cloud storage and bigquery APIs in the GCP console
1.  Open cloud shell in the GCP console
1.  Download the zip with all files

        wget https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/cloud-functions-avro-import-bq/gcf_gcs.zip

1.  Unzip

        unzip gcf_gcs.zip

1.  Update `index.js` with your `projectId` and `datasetId` (destination).
1.  Update `install.sh` `--trigger-resource` flag with your source Cloud Storage
    bucket (replace avro-import-source)
1.  Run the function: 

        ./install.sh

1.  Verify the function is running in the [GCP console][console].
1.  Upload an avro to the source Cloud Storage bucket you specified in `install.sh`.

[console]: https://console.cloud.google.com/functions/

This cloud function should deploy and wait for new objects to be finalized on
the source Cloud Storage bucket. Once a new AVRO is uploaded to the source it
will use the BQ API to load the new dataset into a new table.

Note: This will only create a new table for each new import. You may need to
update the function for replacing previous tables.
