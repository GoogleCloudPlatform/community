---
title: Credit card tokenization service for Google Cloud Platform
description: Learn how to build a PCI DSS compliant credit card tokenization service.
author: ianmaddox
tags: serverless, cloud functions, javascript, iam, PCI, DSS, credit, card
date_published: 2019-04-02
---

# Overview

This example provides a PCI DSS compliant credit card tokenization service built for Google Cloud Platform (GCP), which
can run in both Docker and Cloud Functions. This code is based on Google's 
[Tokenizing sensitive cardholder data for PCI DSS](/solutions/tokenizing-sensitive-cardholder-data-for-pci-dss) whitepaper.

This project uses [KMS](https://cloud.google.com/kms/) and [Datastore](https://cloud.google.com/datastore/) to securely
encrypt and tokenize sensitive credit card data in a manner consistent with the PCI Data Security Standard. This code is
applicable to SAQ A-EP and SAQ D type merchants of any compliance level.

For more information on PCI DSS compliance on GCP, see [PCI Data Security Standard compliance](https://cloud.google.com/solutions/pci-dss-compliance-in-gcp).

# Configuration

Before the code can be deployed, some customizations must be made. See the configuration file `config/default.json` for
available options before proceeding. A best practice is to copy `config/default.json` to `config/local.json` and make edits
there. More functionality is available for [environment-specific configs](https://www.npmjs.com/package/config).

# Running in Docker

Run the following command to check out the project code and move into your working directory:

```
git clone https://github.com/GoogleCloudPlatform/community/tutorials/gcp-pci-tokenizer
cd gcp-pci-tokenizer
```

The application can be deployed with the example script `src/docker_run.sh`. Any files added to `config/` in the filesystem
where the Docker image is run are linked into the app.

# Running in Cloud Functions

You can also deploy this application in Cloud Functions. This allows for rapid testing and development, but you are 
responsible for developing compensating controls for egress traffic restrictions if Cloud Functions are used as part of
your in-scope PCI environment.

The exported function names are `tokenize` and `detokenize`. To deploy through the web UI, open the GCP Console and then
open [Cloud Shell](https://cloud.google.com/shell/). This use-anywhere Linux terminal can be opened with
the **Activate Cloud Shell** button in the top-right of the GCP Console.

Run the following command to check out the project code and move into the working directory:

```
git clone https://github.com/GoogleCloudPlatform/community/tutorials/gcp-pci-tokenizer

cd gcp-pci-tokenizer
```

This folder contains the file `index.js`, which is the source for two different Cloud Functions we will be creating. It
also contains `package.json`, which tells Cloud Functions which packages it needs to run.

Run the following commands to deploy both of the Cloud Functions:

```
gcloud functions deploy tokenize --runtime=nodejs8 --trigger-http --entry-point=tokenize --memory=256MB --source=.

gcloud functions deploy detokenize --runtime=nodejs8 --trigger-http --entry-point=detokenize --memory=256MB --source=.
```

These commands create two separate Cloud Functions: one for turning the card number into a token and another to reverse the
process. The differing entry points direct execution to the proper starting function within `index.js`.

These same deploy commands are available in convenient utility scripts:

```
src/deploy-tokenize.sh
src/deploy-detokenize.sh
```

After the functions are deployed, you can verify they were successfully created by navigating to the Cloud Functions page
in the GCP Console. Doing so will not close the Cloud Shell. You should see your two functions, with a green checkmark next
to each.

# Usage

After the application has been deployed, there are two available API calls.

## Tokenizing a card

```
Host and Port:  See deployment process output
Path:           /tokenize
Method:         HTTP POST
Params:
  * auth_token:   An OAuth 2.0 authentication token
  * [project_id:  GCP project ID]
  * cc:           The payment card to tokenize
  * mm:           Two digit expiration month
  * yyyy:         Four digit expiration year
  * user_id:      Arbitrary user identification string

Response:
  * On success: HTTP 200 and 64 character token value
  * On failure: HTTP 4xx,5xx and error message
```

### Detokenizing a card

```
Host and Port:  See deployment process output
Path:           /detokenize
Method:         HTTP POST
Params:
  * auth_token:   An OAuth 2.0 authentication token
  * [project_id:  GCP project ID]
  * cc_token:     64-character card token

Response:
  * On success: HTTP 200 and JSON payload containing cc, mm, yyyy, and user_id
  * On failure: HTTP 4xx,5xx and error message
```

# Apache 2.0 License
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
