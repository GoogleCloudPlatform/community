---
title: AVRO/CSV Import to BigQuery from Cloud Storage with a Cloud Function
description: Use this Cloud Function to import AVRO or CSV files in Google Cloud Storage
author: mikekahn, tfrantzen
tags: Cloud Functions, BigQuery, Cloud STorage
date_published: 2018-05-06
---
## Introduction

This use of a [cloud function][function] demonstrates a serverless cron scheduled import for data management or data science workflows. 
The use case would be, a 3rd party provides data uploaded to a cloud storage bucket on regular basis in GCP project. 
Instead of manually importing the CSV or AVRO to BigQuery each day, we use a cloud function with a trigger on [object.finalize][finalize] on a set bucket. 
This way whenever a CSV or AVRO is uploaded to that bucket, the function is triggered and the file is imported to a new BQ table to the specified dataset.

![Cloud Function AVRO import workflow](https://storage.googleapis.com/avro-import-source/cloud-function-import.png)

[function]: https://cloud.google.com/functions/docs/
[finalize]: https://cloud.google.com/functions/docs/calling/storage#object_finalize

Here is how to set it up:

## Instructions:

1. Enable cloud functions, cloud storage and bigquery APIs in the GCP console
2. Open cloud shell in the GCP console
3. 
```
wget https://github.com/mkahn5/community/raw/patch-1/tutorials/cloud-functions-avro-import-bq/gcf_gcs.zip
```
4. 
```
unzip gcf_gcs.zip
```
5. update index.js with the projectid and datasetid (destination)
6. update install.sh trigger-resource with the source gcs bucket (replace avro-import-source)
7. Run the function: 
```
./install.sh
```
8. Verify the function is running in the [GCP console][console]
9. Upload an avro to the source gcs bucket you specified in install.sh

[console]: https://console.cloud.google.com/functions/

This cloud function should deploy and wait for new objects to be finalized on the source GCS bucket.
Once a new AVRO is uploaded to the source it will use the BQ API to load the new dataset into a new table.
Note: This will only create a new table for each new import. You may need to update the function for replacing previous tables.
