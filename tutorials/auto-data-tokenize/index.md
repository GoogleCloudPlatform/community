---
title: Automatically tokenize sensitive file-based data with Cloud Data Loss Prevention, Cloud Key Management Service, and Dataflow
description: A tool to tokenize Avro or Parquet files in bulk.
author: anantdamle
tags: data governance, DLP, encryption, tokenization, de-identification, data migration, KMS
date_published: 2021-01-11
---

Anant Damle | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This document discusses how to identify and tokenize data with an automated data transformation pipeline.

This pipeline uses [Cloud Data Loss Prevention (Cloud DLP)](https://cloud.google.com/dlp) to detect sensitive data like personally identifiable information 
(PII), and it uses [Cloud Key Management Service (Cloud KMS)](https://cloud.google.com/kms) for encryption.

De-identification techniques like encryption let you preserve the utility of your data for joining or analytics while reducing the risk of handling the data by
obfuscating the raw sensitive identifiers. To minimize the risk of handling large volumes of sensitive data, you can use an automated data transformation
pipeline to create de-identified datasets that can be used for migrating from on-premises to the cloud or keep a de-identified replica for analytics. When the
dataset has not been characterized, Cloud DLP can inspect the data for sensitive information using
[more than 100 built-in classifiers](https://cloud.google.com/dlp/docs/infotypes-reference). 

One of the daunting challenges during data migration to the cloud is how to manage sensitive data. The sensitive data can be in structured forms like analytics 
tables or unstructured like chat history or transcription records. You can use Cloud DLP to identify sensitive data from both of these kinds of sources
and then tokenize the sensitive parts.

Tokenizing structured data can be optimized for cost and speed by using representative samples for each of the columns to categorize the kind of information,
followed by bulk encryption of sensitive columns. This approach reduces the cost of using Cloud DLP by limiting the use to classification of a small 
representative sample, instead of all of the records. The throughput and cost of tokenization can be optimized by using envelope encryption for columns 
classified as sensitive. 

This document demonstrates a reference implementation of tokenizing structured data through two tasks: _sampling and identification_, followed by
_bulk tokenization_ using symmetric encryption to tokenize data using envelope encryption.

In a [companion document](https://cloud.google.com/community/tutorials/auto-bigquery-tokenize), the solution described in the current document is extended to use 
BigQuery tables as a data source, instead of using files as input.

This document is intended for a technical audience whose responsibilities include data security, data processing, or data analytics. This document assumes that 
you're familiar with data processing and data privacy, without the need to be an expert. This document assumes some familiarity with shell scripts and basic 
knowledge of Google Cloud.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Dataflow](https://cloud.google.com/dataflow/pricing)
* [Cloud Storage](https://cloud.google.com/storage/pricing)
* [Cloud Data Loss Prevention](https://cloud.google.com/dlp/pricing)
* [Cloud Key Management Service](https://cloud.google.com/kms/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your
projected usage.

## Architecture

The solution described in this document comprises two pipelines, one for each of the tasks:

  * Sample and identify
  * Tokenize

![Auto tokenizing pipelines](https://storage.googleapis.com/gcp-community/tutorials/auto-data-tokenize/Auto_Tokenizing_Pipelines_Arch.svg)

The *sample-and-identify* pipeline extracts a few sample records from the source files. The *identify* part of pipeline then decomposes each sample record into
columns to categorize them into one of the [built-in infoTypes](https://cloud.google.com/dlp/docs/infotypes-reference) or
[custom infoTypes](https://cloud.google.com/dlp/docs/creating-custom-infotypes) using Cloud DLP. 

The sample-and-identify pipeline outputs the following files to Cloud Storage:

  * Avro schema of the file
  * Detected infoTypes for each of the input columns

The *tokenize* pipeline then encrypts the user-specified source columns using the schema information from the sample-and-identify pipeline and user-provided
enveloped data encryption key. The tokenizing pipeline performs the following transforms on each of the records in the source file:

  1. Unwrap the data encryption key using Cloud KMS.
  1. Un-nest each record into a flat record.
  1. Tokenize required values using
     [deterministic AEAD](https://github.com/google/tink/blob/master/docs/PRIMITIVES.md#deterministic-authenticated-encryption-with-associated-data).
  1. Re-nest the flat record into an Avro record.
  1. Write an Avro file with encrypted fields.

### Concepts

[Envelope encryption](https://cloud.google.com/kms/docs/envelope-encryption) is a form of encryption that uses multiple layers of keys 
for encrypting data. Envelope encryption is the process of encrypting the actual data encryption key with another key to secure the data encryption key.

[Cloud Key Management Service (Cloud KMS)](https://cloud.google.com/kms) provides management of encryption keys at scale.

[Tink](https://github.com/google/tink) is an open source library that provides APIs for handling encryption and decryption. Tink integrates with Cloud KMS for 
use with envelope encryption.

[Deterministic Authenticated Encryption with Associated Data (AEAD)](https://github.com/google/tink/blob/master/docs/PRIMITIVES.md#deterministic-authenticated-encryption-with-associated-data) is used for the following purposes:

* Permits use of the ciphertext as join keys. The deterministic property of the cipher ensures that ciphertext for the same plaintext is always the same.
  Using this property, you can use the encrypted data for performing statistical analysis like cardinality analysis and frequency analysis.
* Store signed plaintext within the cipher to assert authenticity.
* Reversibility. The use of a 2-way encryption algorithm permits reversing the algorithm to obtain the original plaintext. Hashing doesn't permit such 
  operations.

[Cloud Data Loss Prevention (DLP)](https://cloud.google.com/dlp) is a Google Cloud service that provides data classification, de-identification, and
re-identification features, allowing you to manage sensitive data in your enterprise.

Record flattening is the process of converting nested and repeated records as a flat table. Each leaf node of the record gets a unique identifier. This 
flattening process enables sending data to DLP for identification purposes, since the DLP API supports simple
[data tables](https://cloud.google.com/dlp/docs/examples-deid-tables).

Consider a contact record for Jane Doe, which has a nested and repeated field `contacts`:
   
    {
        "name": "Jane Doe",
        "contacts": [
        {
           "type": "WORK",
           "number": 2124567890  
        },
        {
           "type": "HOME",
           "number": 5304321234
        }
        ]
     }
 
Flattening this record yields a
[`FlatRecord`](https://github.com/GoogleCloudPlatform/auto-data-tokenize/blob/master/proto-messages/src/main/resources/proto/google/cloud/autodlp/auto_tokenize_messages.proto#L103)
with the following data:
   
    {
       "values": {
        "$.name": "Jane Doe",
        "$.contacts[0].contact.type": "WORK",
        "$.contacts[0].contact.number": 2124567890,
        "$.contacts[1].contact.type": "WORK",
        "$.contacts[1].contact.number": 5304321234   
       },
 
       "keySchema": {
        "$.name": "$.name",
        "$.contacts[0].contact.type": "$.contacts.contact.type",
        "$.contacts[0].contact.number": "$.contacts.contact.number",
        "$.contacts[1].contact.type": "$.contacts.contact.type",
        "$.contacts[1].contact.number": "$.contacts.contact.number"   
       }
    }
 
In the `values` map, each leaf node of the contact record is mapped using a [JsonPath](https://goessner.net/articles/JsonPath/) notation.
The `keySchema` block shows a mapping between the leaf value's key to a schema key to demonstrate that leaf nodes of same type share the same key schema.
For example, `$.contacts[0].contact.number` is logically the same as `$.contacts[1].contact.number`, because both of them have the same key schema
`$.contacts.contact.number`.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make
cleanup easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google
    Cloud project.
1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

    At the bottom of the Cloud Console, a [Cloud Shell](https://cloud.google.com/shell/docs/features) session opens and
    displays a command-line prompt. Cloud Shell is a shell environment with the Cloud SDK already installed, including
    the [gcloud](https://cloud.google.com/sdk/gcloud/) command-line tool, and with values already set for your current
    project. It can take a few seconds for the session to initialize.

1.  Enable APIs for Cloud DLP, Cloud KMS, Compute Engine, Cloud Storage, Dataflow, and BigQuery services:

        gcloud services enable \
        dlp.googleapis.com \
        cloudkms.googleapis.com \
        compute.googleapis.com \
        storage.googleapis.com \
        dataflow.googleapis.com \
        bigquery.googleapis.com

## Setting up your environment

1.  In Cloud Shell, clone the source repository and go to the directory for this tutorial:

        git clone https://github.com/GoogleCloudPlatform/auto-data-tokenize.git
        cd auto-data-tokenize/

1.  Use a text editor to modify the `set_variables.sh` file to set the required environment variables:

        # The Google Cloud project to use for this tutorial
        export PROJECT_ID="[YOUR_PROJECT_ID]"

        # The Compute Engine region to use for running Dataflow jobs and create a 
        # temporary storage bucket
        export REGION_ID="[YOUR_COMPUTE_ENGINE_REGION]"

        # The Cloud Storage bucket to use as a temporary bucket for Dataflow
        export TEMP_GCS_BUCKET="[CLOUD_STORAGE_BUCKET_NAME]"

        # Name of the service account to use (not the email address)
        export DLP_RUNNER_SERVICE_ACCOUNT_NAME="[SERVICE_ACCOUNT_NAME_FOR_RUNNER]"

        # Name of the Cloud KMS key ring name
        export KMS_KEYRING_ID="[KEY_RING_NAME]"

        # name of the symmetric key encryption kms-key-id
        export KMS_KEY_ID="[KEY_ID]"

        # The JSON file containing the Tink wrapped data key to use for encryption
        export WRAPPED_KEY_FILE="[PATH_TO_THE_DATA_ENCRYPTION_KEY_FILE]"   

1.  Run the script to set the environment variables:

        source set_variables.sh

## Creating resources

The tutorial uses following resources:

 * A service account to run Dataflow pipelines, enabling fine-grained access control
 * A symmetric Cloud KMS managed [key encryption key (KEK)](https://cloud.google.com/kms/docs/envelope-encryption#key_encryption_keys), which is used to wrap the
   actual data encryption key
 * A Cloud Storage bucket for temporary data storage and test data

### Create service accounts

We recommend that you run pipelines with fine-grained access control to improve access partitioning. If your project doesn't have a user-created service account,
create one using following instructions.

You can use your browser by going to [**Service accounts**](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts?supportedpurview=project)
page in the Cloud Console.

1.  Create a service account to use as the user-managed controller service account for Dataflow:

        gcloud iam service-accounts create  ${DLP_RUNNER_SERVICE_ACCOUNT_NAME} \
        --project="${PROJECT_ID}" \
        --description="Service Account for Tokenizing pipelines." \
        --display-name="Tokenizing pipelines"

1.  Create a custom role with required permissions for accessing Cloud DLP, Dataflow, and Cloud KMS:

        export TOKENIZING_ROLE_NAME="tokenizing_runner"

        gcloud iam roles create ${TOKENIZING_ROLE_NAME} \
        --project=${PROJECT_ID} \
        --file=tokenizing_runner_permissions.yaml

1.  Apply the custom role to the service account:

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${DLP_RUNNER_SERVICE_ACCOUNT_EMAIL}" \
        --role=projects/${PROJECT_ID}/roles/${TOKENIZING_ROLE_NAME}

1.  Assign the `dataflow.worker` role to allow the service account to allow it to run as a Dataflow worker:

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${DLP_RUNNER_SERVICE_ACCOUNT_EMAIL}" \
        --role=roles/dataflow.worker

### Create the key encryption key (KEK)

The data is encrypted using a data encryption key (DEK). You use [envelope encryption](https://cloud.google.com/kms/docs/envelope-encryption) to encrypt 
the DEK using a key encryption key (KEK) in [Cloud KMS](https://cloud.google.com/kms). This helps to ensure that the DEK can be stored without compromising it.

1.  Create a Cloud KMS key ring:

        gcloud kms keyrings create --project ${PROJECT_ID} --location ${REGION_ID} ${KMS_KEYRING_ID}

1.  Create a Cloud KMS symmetric key to use for encrypting your data encryption key:

        gcloud kms keys create --project ${PROJECT_ID} --keyring=${KMS_KEYRING_ID} --location=${REGION_ID} --purpose="encryption" ${KMS_KEY_ID}

1.  Download and extract the latest version of [Tinkey](https://github.com/google/tink/blob/master/docs/TINKEY.md), which is an open source utility to create 
    wrapped encryption keys:

        mkdir tinkey/
        tar zxf tinkey-[VERSION].tar.gz -C tinkey/
        alias tinkey='${PWD}/tinkey/tinkey'

1.  Create a new wrapped data encryption key:

        tinkey create-keyset \
        --master-key-uri="${MAIN_KMS_KEY_URI}" \
        --key-template=AES256_SIV \
        --out="${WRAPPED_KEY_FILE}" \
        --out-format=json

### Create the Cloud Storage bucket

Create a Cloud Storage bucket for storing test data and Dataflow staging location:

    gsutil mb -p ${PROJECT_ID} -l ${REGION_ID} "gs://${TEMP_GCS_BUCKET}"

### Copy test data to Cloud Storage

You can use your own file datasets or copy the included demonstration dataset (`userdata.avro` or `userdata.parquet`).

     gsutil cp userdata.avro gs://${TEMP_GCS_BUCKET}

## Compile modules

You need to compile all of the modules to build executables for deploying the sample-and-identify and tokenize pipelines.

     ./gradlew buildNeeded shadowJar

**Tip**: To skip running the tests, you can add the `-x test` flag.

## Using the sample-and-identify pipeline

Run the sample-and-identify pipeline to identify sensitive columns in the data that you need to tokenize.

The pipeline extracts `sampleSize` number of records, flattens the record and identifies sensitive columns
using [Cloud DLP](https://cloud.google.com/dlp). Cloud DLP provides functionality
to [identify](https://cloud.google.com/dlp/docs/inspecting-text) sensitive information types. The Cloud DLP identify method
supports only flat tables, so the pipeline flattens the Avro or Parquet records, since they can contain nested or repeated fields.

### Run the sample-and-identify pipeline

    sample_and_identify_pipeline --project="${PROJECT_ID}" \
    --region="${REGION_ID}" \
    --runner="DataflowRunner" \
    --serviceAccount=${DLP_RUNNER_SERVICE_ACCOUNT_EMAIL} \
    --gcpTempLocation="gs://${TEMP_GCS_BUCKET}/temp" \
    --stagingLocation="gs://${TEMP_GCS_BUCKET}/staging" \
    --tempLocation="gs://${TEMP_GCS_BUCKET}/bqtemp" \
    --workerMachineType="n1-standard-1" \
    --sampleSize=500 \
    --sourceType="AVRO" \
    --inputPattern="gs://${TEMP_GCS_BUCKET}/userdata.avro" \
    --reportLocation="gs://${TEMP_GCS_BUCKET}/dlp_report/"

The pipeline detects all of the standard infoTypes supported by Cloud DLP.

To provide additional custom infoTypes that you need, use `--observableInfoTypes`.

### Sample-and-identify pipeline DAG

The Dataflow execution DAG (directed acyclic graph) looks like the following:

![Sample-and-identify pipeline DAG](https://storage.googleapis.com/gcp-community/tutorials/auto-data-tokenize/sample_and_identify_pipeline_dag.png)

### Retrieve the report

The sample-and-identify pipeline outputs the Avro schema (or converted for Parquet) of the files and one file for each of the columns determined to contain 
sensitive information. 

1.  Retrieve the report to your local machine:

        mkdir -p dlp_report/ && rm dlp_report/*.json
        gsutil -m cp "gs://${TEMP_GCS_BUCKET}/dlp_report/*.json" dlp_report/

1.  List all of the column names that have been identified:

        cat dlp_report/col-*.json | jq .columnName

    The output matches the following list:

        "$.kylosample.birthdate"
        "$.kylosample.cc"
        "$.kylosample.email"
        "$.kylosample.first_name"
        "$.kylosample.ip_address"
        "$.kylosample.last_name"

1.  View the details of an identified column with the `cat` command for the file:

        cat dlp_report/col-kylosample-cc-00000-of-00001.json

    The following is a snippet of the `cc` column:

        {
          "columnName": "$.kylosample.cc",
          "infoTypes": [
            {
              "infoType": "CREDIT_CARD_NUMBER",
              "count": "394"
            }
          ]
        }

    The `"count"` value varies based on the randomly selected samples during execution.

## Use the tokenize pipeline

The sample-and-identify pipeline used few samples from the original dataset to identify sensitive information using
Cloud DLP. The tokenize pipeline processes the entire dataset and encrypts the desired columns using the provided data
encryption key (DEK).

### Run the tokenize pipeline

    tokenize_pipeline --project="${PROJECT_ID}" \
    --region="${REGION_ID}" \
    --runner="DataflowRunner" \
    --tempLocation="gs://${TEMP_GCS_BUCKET}/bqtemp" \
    --serviceAccount=${DLP_RUNNER_SERVICE_ACCOUNT_EMAIL} \
    --workerMachineType="n1-standard-1" \
    --schema="$(<dlp_report/schema.json)" \
    --tinkEncryptionKeySetJson="$(<${WRAPPED_KEY_FILE})" \
    --mainKmsKeyUri="${MAIN_KMS_KEY_URI}" \
    --sourceType="AVRO" \
    --inputPattern="gs://${TEMP_GCS_BUCKET}/userdata.avro" \
    --outputDirectory="gs://${TEMP_GCS_BUCKET}/encrypted/" \
    --tokenizeColumns="$.kylosample.cc" \
    --tokenizeColumns="$.kylosample.email"

The pipeline executes asynchronously on Dataflow. You can check the progress by following the job link printed in the following format:

    INFO: JobLink: https://console.cloud.google.com/dataflow/jobs/[YOUR_DATAFLOW_JOB_ID]>?project=[YOUR_PROJECT_ID]

The tokenize pipeline's DAG looks like the following:

![Encryption pipeline DAG](https://storage.googleapis.com/gcp-community/tutorials/auto-data-tokenize/encryption_pipeline_dag.png)

### Verify encrypted results

Load the tokenize pipeline's output files into BigQuery to verify that all of the columns specified using the `tokenizeColumns` flag have been encrypted.

1.  Create a BigQuery dataset for tokenized data:

        bq --location=[BIGQUERY_REGION] \
        --project_id="${PROJECT_ID}" \
        mk --dataset tokenized_data

    Replace `[BIGQUERY_REGION]` with a region of your choice. Ensure that the BigQuery dataset region or multi-region is in the same region as the Cloud Storage 
    bucket. For more information, read about [considerations for batch loading data](https://cloud.google.com/bigquery/docs/batch-loading-data).

1.  Load tokenized data into a BigQuery table:

        bq load \
        --source_format=AVRO \
        --project_id="${PROJECT_ID}" \
        "tokenized_data.TokenizedUserdata" \
        "gs://${TEMP_GCS_BUCKET}/encrypted/*"

1.  Check some records to confirm that the `email` and `cc` fields have been encrypted:

        bq query \
        --project_id="${PROJECT_ID}" \
        "SELECT first_name, encrypted_email, encrypted_cc FROM tokenized_data.TokenizedUserdata LIMIT 10"

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

## What's next

* Watch the YouTube video to understand the code:
[Level Up - Automatically tokenize sensitive data with DLP and Dataflow](https://www.youtube.com/watch?v=S6fYkWvUBDo).
* Read the companion document about a similar solution that uses BigQuery tables or queries as input:
[Automatically tokenize sensitive BigQuery data with Cloud Data Loss Prevention, Cloud Key Management Service, and Dataflow](https://cloud.google.com/community/tutorials/auto-bigquery-tokenize).
* Learn more about [Cloud DLP](https://cloud.google.com/dlp).
* Learn more about [Cloud KMS](https://cloud.google.com/kms).
* Learn about [inspecting storage and databases for sensitive data](https://cloud.google.com/dlp/docs/inspecting-storage).
* Learn about handling
  [de-identification and re-identification of PII in large-scale datasets using Cloud DLP](https://cloud.google.com/solutions/de-identification-re-identification-pii-using-cloud-dlp).
