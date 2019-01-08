# Credit Card Tokenization Service for Google Cloud
A PCI DSS compliant credit card tokenization service built for Google Cloud. Capable of running in both Docker and Cloud Functions.

This project employs KMS and Datastore to securely encrypt and tokenize sensitive credit card data in a manner consistent with the PCI Data Security Standard. This code is applicable to SAQ A-EP and SAQ D type merchants of any compliance level.

For more information, see the Google Cloud solution paper on [Tokenizing Sensitive Cardholder Data for PCI DSS](https://TBD).

# Configuration
Before the code can bed deployed, some customizations must be made. See the configuration file config/default.json for available options before proceeding. Best practice is to copy config/default.json to config/local.json and make edits there. More functionality is available for environment-specific configs. See https://www.npmjs.com/package/config for more info.

# Running in Docker
Run the following command to check out the project code and move into your working directory:

```
git clone https://github.com/ianmaddox/gcs-cf-tokenizer
cd gcs-cf-tokenizer
```

The application can be deployed with the example script src/docker_run.sh. Any files added to config/ in the filesystem where the Docker image is run are linked into the app.

# Running in Cloud Functions
You can also deploy this application in Google Cloud Functions. This allows for rapid testing and development, but you are responsible for developing compensating controls for egress traffic restrictions if Cloud Functions are used as part of your in-scope PCI environment.

The exported function names are "tokenize" and "detokenize". To deploy through the web UI, open the GCP Cloud Console and then open the Cloud Shell. Cloud Shell can be opened with the ">_" icon in the top-right of the console.
Run the following command to check out the project code and move into the working directory:

```
git clone https://github.com/ianmaddox/gcs-cf-tokenizer
cd gcs-cf-tokenizer
```

This folder contains the file index.js which is the source for two different cloud functions we will be creating. It also contains package.json which tells Cloud Functions which packages it needs to run.

Run the following commands to deploy both of the cloud functions:
```
gcloud beta functions deploy tokenize --runtime=nodejs8 --trigger-http --entry-point=tokenize --memory=256MB --source=.

gcloud beta functions deploy detokenize --runtime=nodejs8 --trigger-http --entry-point=detokenize --memory=256MB --source=.
```

These commands create two separate Cloud Functions: one for turning the card number into a token and another to reverse the process. The differing entry-points direct execution to the proper starting function within index.js.

These same deploy commands are available in convenient utility scripts:
```
src/deploy-tokenize.sh
src/deploy-detokenize.sh
```

Once the functions are deployed, you can verify they were successfully created by navigating to the Cloud Functions page in the Google Cloud Console. Doing so will not close the Cloud Shell. You should see your two functions with green checkmarks next to each.

# Usage
Once the application has been deployed, there are two available API calls.
### Tokenizing a card
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
