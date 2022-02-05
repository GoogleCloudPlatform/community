---
title: Credit card tokenization service for Google Cloud
description: Deploy a PCI-DSS-ready credit card tokenization service.
author: ianmaddox
tags: serverless, cloud run, DLP, javascript, iam, PCI, DSS, credit, card
date_published: 2019-12-26
---

Ian Maddox | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This code provides a PCI-DSS-ready credit card tokenization service built for containers running on Google Cloud. This code
is based on Google's
[Tokenizing sensitive cardholder data for PCI DSS](https://cloud.google.com/solutions/tokenizing-sensitive-cardholder-data-for-pci-dss)
whitepaper. It offers two methods of tokenizing: DLP and KMS. See the [Tokenization options](#tokenization-options) section 
below for more info.

This code uses [Cloud DLP](https://cloud.google.com/dlp/) to 
[securely encrypt](https://cloud.google.com/dlp/docs/transformations-reference#crypto) and tokenize sensitive credit card 
data in a manner consistent with the PCI Data Security Standard (DSS). This code is applicable to SAQ A-EP and SAQ D type 
merchants of any compliance level.

**Warning**: Confirm that your environment and installation are PCI-DSS-compliant before processing actual credit card data.
Google cannot guarantee PCI DSS compliance of customer applications.

For more information on PCI DSS compliance on Google Cloud, see
[PCI Data Security Standard compliance](https://cloud.google.com/solutions/pci-dss-compliance-in-gcp).

## Security

By definition, this service handles raw credit card numbers and other sensitive cardholder data. As a result, this code and 
anything able to directly call it are considered in-scope for PCI DSS. Appropriate security controls must be enacted to
avoid compliance failures and breaches.

### Encryption

The tokens created by this service are encrypted using
[AES in Synthetic Initialization Vector (AES-SIV)](https://tools.ietf.org/html/rfc5297) mode. For more information, see
[DLP deterministic encryption](https://cloud.google.com/dlp/docs/transformations-reference#de).

### Crypto keys

This service relies on a secret encryption key stored in the
[config JSON](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/pci-tokenizer/config) files. Before 
deploying to production, this plaintext key should be switched to a Cloud KMS wrapped key, which adds an additional layer of
security. See the section below and the page on
[DLP format-preserving encryption (FPE)](https://cloud.google.com/dlp/docs/deidentify-sensitive-data#cryptoreplaceffxfpeconfig)
for information on how to wrap crypto keys.

### Access control

Setting the `--no-allow-unauthenticated` flag prevents unauthorized calls to your tokenization service. This is critical for 
any service or system in-scope for PCI. To grant access, you must navigate to 
[your tokenization service in the console](https://console.cloud.google.com/run) and add the service accounts and users 
authorized to invoke the service. They will need to be granted the
[Cloud Run Invoker](https://cloud.google.com/run/docs/reference/iam/roles) IAM role.

Utility scripts have been provided in
[`examples`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/pci-tokenizer/examples/) that 
incorporate Google's recommended approach to
[authenticating developers](https://cloud.google.com/run/docs/authenticating/developers).

### Salting and additional encryption

The userID provided in the tokenization and detokenization requests is both a salt and validating factor. The addition of
additional salt or encryption wrappers is possible by modifying
[app.js](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/pci-tokenizer/src/app.js).

## Tokenization options

This tokenization service offers two methods of securing cardholder data, backed by DLP or KMS.

| Tokenization Type:   | DLP            | KMS            |
|----------------------|----------------|----------------|
| Deterministic output | Yes            | No             |
| Token type           | Encrypted data | Encrypted data |
| Key management       | CSEK           | Fully managed  |

**Deterministic output** means that a given set of inputs (card number, expiration, and userID) will always generate the 
same token. This is useful if you want to rely on the token value to deduplicate your token stores. You can simply match a 
newly generated token to your existing catalog of tokens to determine whether the card has been previously stored. Depending
on your application architecture, this can be a very useful feature. However, this could also be accomplished using a salted
hash of the input values.

**Token type** indicates whether the token itself contains encrypted data or if it is merely an identifier to look up 
information encrypted and stored elsewhere.

**Key management** determines who is responsible for generating and managing the encryption keys. CSEK comes with the
highest level of responsibility for the customer because they must securely generate, store, and rotate the encryption keys. 
Even with a wrapped key, the customer must keep the key a secret. CSEK rotation means manually versioning and potentially 
re-encrypting all existing data in the event of a suspected key breach. If the key is lost, all encrypted data will be
unreadable.

Fully-managed encryption keys take advantage of Google's internal 
[key rotation](https://cloud.google.com/kms/docs/key-rotation). This happens on a schedule determined by the encryption key
administrator.

## Before you begin

1.  In the Cloud Console, on the project selector page,
    [select or create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).

    **Note**: If you don't plan to keep the resources that you create in this procedure, create a project instead of selecting
    an existing project. After you finish these steps, you can delete the project, removing all resources associated with 
    the project.

1.  Make sure that billing is enabled for your Google Cloud project.
    [Learn how to confirm that billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project).

1.  [Enable the Cloud Build and Cloud Run APIs](https://console.cloud.google.com/flows/enableapi?apiid=cloudbuild.googleapis.com,run.googleapis.com&redirect=https://console.cloud.google.com).

1.  [Install and initialize the Cloud SDK](https://cloud.google.com/sdk/docs/).

1.  Update components:

        gcloud components update

1.  Run the following commands to check out the project code and move into your working directory:  

        git clone https://github.com/GoogleCloudPlatform/community gcp-community
        cd gcp-community/tutorials/pci-tokenizer

## Create a wrapped encryption key for DLP tokenization

If you intend to use DLP tokenization, you will be supplying your own data encryption key (DEK). In this step, you create a
data encryption key (DEK) and then wrap it in an additional layer of encryption called the *key encryption key (KEK)*. Note 
that the KEK is fully managed by [KMS](https://console.cloud.google.com/security/kms) and never leaves the service. Key 
wrapping is technically optional for testing DLP tokenization but should be a security requirement for production 
environments.

1.  [Create a KMS keyring](https://console.cloud.google.com/security/kms). Note the keyring name and location ("global" is
    recommended).

1.  Create a key for that ring. Note the key name.

1.  Copy and open the `local.envvars` file to configure the token wrapping utility:  

        cp examples/envvars examples/local.envvars
        nano examples/local.envvars
        
    Populate the variables `KMS_LOCATION`, `KMS_KEY_RING`, and `KMS_KEY_NAME` with the values noted in the previous steps.

1.  Generate the keys.

    There are many ways to generate random bytes. This command will use the Linux system's random number generator to 
    generate 16 hexadecimal bytes (32 characters); it creates two files: `key_##B.txt` and `key_##B.wrapped.txt`:
    
        LEN=32
        openssl rand $LEN | tee key_${LEN}B.txt | examples/wrapkey | tee key_${LEN}B.wrapped.txt

1.  Preserve the wrapped and unwrapped keyfiles along with the KMS key details.

1.  Grant permissions to the invoking service account:  

    1.  Navigate to [IAM permissions](https://console.cloud.google.com/iam-admin/iam).
    1.  Edit permissions of the **Compute Engine default service account**.
        It should look like this: `000000000000-compute@developer.gserviceaccount.com`.
    1.  Grant the role **DLP User**.

## Configuration

The tokenizer service uses the configuration file
[`config/default.json`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/pci-tokenizer/config/default.json) with overrides in 
`config/local.json`. The best practice is to copy `config/default.json` to `config/local.json` and make edits there.

-   `general.project_id` is required but it can either be set here or with each API call. API call project_id overrides this
    value if both are set.

-   `dlp.unwrapped_key` is the minimum required to perform DLP tokenization. Use an ASCII string 16, 24, or 32 bytes long.

-   `dlp.wrapped_key` is used if you wrapped your DLP encryption key using KMS. Instructions on how to do this are in the
    section above. Wrapping your keys using KMS is highly recommended to help avert leaks. *If used, you must also provide 
    the KMS key location, ring name, and key name.*

-   `kms.location` is typically "global".

-   `kms.key_ring` is the name of the key ring.

-   `kms.key_name` is the actual key name.

-   Other settings are documented in
    [`config/default.json`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/pci-tokenizer/config/default.json).

## Containerizing and deploying the tokenizer service

1.  Assign your Google Cloud project ID to a variable for ease of use in your terminal, replacing `[PROJECT_ID]` with your 
    Google Cloud project ID:  
    
        PROJECT=[PROJECT_ID]

    You can get your project ID with this command:
    
        gcloud config get-value project

1.  Build your container image using Cloud Build, by running the following command from the directory containing the
    Dockerfile: 
    
        gcloud builds submit --tag gcr.io/$PROJECT/tokenizer

    Upon success, you will see a success message containing the image name (gcr.io/`PROJECT-ID`/tokenizer). The image is
    stored in Container Registry and can be re-used.

1.  Deploy using the following command:  

        gcloud run deploy tokenizer --image gcr.io/$PROJECT/tokenizer --platform managed --no-allow-unauthenticated --region us-central1 --memory 128Mi

    - `tokenizer` is the name of your service.
    - `--image` is the image you created in the previous step.
    - `--platform` should be set to managed.
    - `--no-allow-unauthenticated` prevents anonymous calls.
    - `--region` can be changed to any of the [available regions](https://cloud.google.com/run/docs/locations).
    - `--memory` 128 MB ought to be enough for anyone.

    Wait a few moments until the deployment is complete. On success, the command line displays the service URL.

1.  Visit your deployed container by opening the service URL in a web browser.

Congratulations! You have just deployed an application packaged in a container image to Cloud Run. Cloud Run automatically 
scales your service to match traffic demand. It scales down to zero when not in use. You only pay for the CPU, memory, and 
networking consumed during request handling.

## Usage

After your tokenization service is deployed to Cloud Run and you have the URL, you can start calling the API. The 
[`examples`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/pci-tokenizer/examples/) directory 
contains demonstration `tokenize` and `detokenize` scripts that you can use to quickly test your API.

See the following sections for details on the `tokenize` and `detokenize` API methods.

### Tokenizing a card

- Adding `/dlp` to the end of the path sets the mode to DLP deterministic CSEK encryption.
- Adding `/kms` to the end of the path sets the mode to KMS non-deterministic encryption.

**Note:** DLP is the default mode that is used if you do not specify a mode. DLP and KMS generated tokens are not
cross-compatible.

```
Host and Port:  See deployment process output
Path:           /tokenize/[dlp|kms]
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
Path:           /detokenize/[dlp|kms]
Method:         HTTP POST
Params:
  * auth_token:   An OAuth 2.0 authentication token
  * [project_id:  GCP project ID]
  * cc_token:     64-character card token

Response:
  * On success: HTTP 200 and JSON payload containing cc, mm, yyyy, and user_id
  * On failure: HTTP 4xx,5xx and error message
```

## Examples

Example `curl` invocations of the tokenization and detokenization process can be found in
[`examples`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/pci-tokenizer/examples/).
See the 
[readme file](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/pci-tokenizer/examples/README.md) for 
information on how to configure and use the example scripts on your tokenization service.
