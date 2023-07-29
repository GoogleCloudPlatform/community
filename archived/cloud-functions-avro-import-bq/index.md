---
title: Import AVRO and CSV files to BigQuery from Cloud Storage with a Cloud Function
description: Use this Cloud Function to import AVRO or CSV files into BigQuery from Cloud Storage.
author: mikekahn
tags: Cloud Functions, BigQuery, Cloud Storage
date_published: 2018-05-06
---

Mike Kahn | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using a [Cloud Function][function] to create a serverless cron
scheduled import for data management or data science workflows. One such use case would
be when a third party provides data uploaded to a Cloud Storage bucket on a
regular basis in a Google Cloud project. Instead of manually importing the CSV or AVRO file to
BigQuery each day, you can use a Cloud Function with a trigger on
[object.finalize][finalize] on a set bucket. This way, whenever a CSV or an AVRO file is
uploaded to that bucket, the function imports the file to a new BigQuery table to the
specified dataset.

![Cloud Function AVRO import workflow](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-avro-import-bq/cloud-function-import.png)

[function]: https://cloud.google.com/functions/docs/
[finalize]: https://cloud.google.com/functions/docs/calling/storage#object_finalize

## Instructions:

1.  Enable Cloud Functions, Cloud Storage, and BigQuery APIs in the Cloud Console.
1.  Open Cloud Shell in the Cloud Console
1.  Download the ZIP file with all files:

        wget https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/cloud-functions-avro-import-bq/gcf_gcs.zip

1.  Extract:

        unzip gcf_gcs.zip

1.  Update `index.js` with your `projectId` and `datasetId` (destination).
1.  Update `install.sh` `--trigger-resource` flag with your source Cloud Storage
    bucket (replace avro-import-source)
1.  Run the function:

        ./install.sh

1.  Verify the function is running in the [Cloud Console][console].
1.  Upload an AVRO file to the source Cloud Storage bucket you specified in `install.sh`.

[console]: https://console.cloud.google.com/functions/

This cloud function should deploy and wait for new objects to be finalized on
the source Cloud Storage bucket. Once a new AVRO file is uploaded to the source it
will use the BigQuery API to load the new dataset into a new table.

This will only create a new table for each new import. You might need to
update the function for replacing previous tables.
