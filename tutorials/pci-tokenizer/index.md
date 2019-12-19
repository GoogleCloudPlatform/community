---
title: Credit card tokenization service for Google Cloud Platform
description: Deploy a PCI DSS ready credit card tokenization service.
author: ianmaddox
tags: serverless, cloud run, DLP, javascript, iam, PCI, DSS, credit, card
date_published: 2019-12-18
---

# Overview

This code provides a PCI DSS ready credit card tokenization service built for containers running in Google Cloud Platform (GCP). This code is based on Google's [Tokenizing sensitive cardholder data for PCI DSS](https://cloud.google.com/solutions/tokenizing-sensitive-cardholder-data-for-pci-dss) whitepaper.

This project uses [DLP](https://cloud.google.com/dlp/)  to [securely encrypt](https://cloud.google.com/dlp/docs/transformations-reference#crypto) and tokenize sensitive credit card data in a manner consistent with the PCI Data Security Standard. This code is applicable to SAQ A-EP and SAQ D type merchants of any compliance level.

**Warning: Please confirm your environment and installation are PCI DSS compliant before processing actual credit card data. Google can not guarantee PCI DSS compliance of customer applications.**

For more information on PCI DSS compliance on GCP, see [PCI Data Security Standard compliance](https://cloud.google.com/solutions/pci-dss-compliance-in-gcp).

# Security
By definition, this service handles raw credit card numbers. As a result, this code and anything able to directly call it are considered in-scope for PCI DSS. Appropriate security controls must be enacted to avoid compliance failures and breaches.

### Encryption
The tokens created by this service are encrypted using [AES in Synthetic Initialization Vector mode (AES-SIV)](https://tools.ietf.org/html/rfc5297). For more information, see [DLP deterministic encryption](https://cloud.google.com/dlp/docs/transformations-reference#de).

### Crypto keys
This service relies on a secret encryption key stored in the [config/*.json](./config/) files. Before deploying to production, this plaintext key should be switched to a Cloud KMS wrapped key which will add an additional layer of security. See [DLP format-preserving encryption (FPE)](https://cloud.google.com/dlp/docs/deidentify-sensitive-data#cryptoreplaceffxfpeconfig) for information on how to wrap crypto keys.

### Access control
Setting the --no-allow-unauthenticated prevents anonymous calls to your tokenization service. In order to grant access, you must navigate to [your tokenization service in the console](https://pantheon.corp.google.com/run) and add the service accounts and users authorized to invoke the service. They will need to be granted the [Cloud Run Invoker](https://cloud.google.com/run/docs/reference/iam/roles) IAM role.

### Salting and additional encryption
The userID provided in the tokenization and detokenization requests is both a salt and validating factor. The addition of additional salt or encryption wrappers is possible by modifying [app.js](./src/app.js).

# Before you begin
1. In the Cloud Console, on the project selector page, select or create a Google Cloud project.
[GO TO THE PROJECT SELECTOR PAGE](https://console.cloud.google.com/projectselector2/home/dashboard)

  **Note: If you don't plan to keep the resources that you create in this procedure, create a project instead of selecting an existing project. After you finish these steps, you can delete the project, removing all resources associated with the project.**

1. Make sure that billing is enabled for your Google Cloud project. [Learn how to confirm billing is enabled for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

1. Enable the Cloud Build and Cloud Run APIs.
[ENABLE THE APIS](https://console.cloud.google.com/flows/enableapi?apiid=cloudbuild.googleapis.com,run.googleapis.com&redirect=https://console.cloud.google.com)

1. [Install and initialize the Cloud SDK](https://cloud.google.com/sdk/docs/).

1. Update components:
`gcloud components update`

# Configuration

1. Run the following commands to check out the project code and move into your working directory:
```
git clone https://github.com/GoogleCloudPlatform/community gcp-community
cd gcp-community/tutorials/pci-tokenizer
```
1. See the configuration file `config/default.json` for available options before proceeding. Copy `config/default.json` to `config/local.json` and make edits there. More functionality is available for [environment-specific configs](https://www.npmjs.com/package/config).

  `general.project_id` is required but it can either be set here or with each API call. API call project_id overrides this value if both are set.

  `dlp.crypto_key` is required to perform tokenization. Use a string 16, 24, or 32 bytes long

# Containerizing and deploying the tokenizer service
1. Assign your Google Cloud project ID to a variable for ease of use:

  ```
  PROJECT=[PROJECT-ID]
  ```
  where PROJECT-ID is your GCP project ID. You can get it by running gcloud config get-value project.

1. Build your container image using Cloud Build, by running the following command from the directory containing the Dockerfile:

  ```
  gcloud builds submit --tag gcr.io/$PROJECT/tokenizer
  ```
  Upon success, you will see a SUCCESS message containing the image name (gcr.io/PROJECT-ID/tokenizer). The image is stored in Container Registry and can be re-used if desired.

1. Deploy using the following command:
```
gcloud run deploy tokenizer --image gcr.io/$PROJECT/tokenizer --platform managed --no-allow-unauthenticated --region us-central1 --memory 128M
```
 - `tokenizer` is the name of your service.
 - `--image` is the image you created in the previous step
 - `--platform` should be set to managed
 - `--no-allow-unauthenticated` prevents anonymous calls
 - `--region` can be changed as desired to any of the [available regions](https://cloud.google.com/run/docs/locations).
 - `--memory` 128 MB ought to be enough for anyone.

  Then wait a few moments until the deployment is complete. On success, the command line displays the service URL.

1. Visit your deployed container by opening the service URL in a web browser.

Congratulations! You have just deployed an application packaged in a container image to Cloud Run. Cloud Run automatically and horizontally scales your container image to handle the received requests, then scales down when demand decreases. You only pay for the CPU, memory, and networking consumed during request handling.

# Usage
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

## Detokenizing a card

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

# Examples
Example curl invocations of the tokenization and detokenization process can be found in ./examples. See [the readme file](./examples/README.md) for information on how to configure and use the example scripts on your tokenization service.
