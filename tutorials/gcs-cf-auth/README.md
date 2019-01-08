# Google Cloud Functions Access Control
This code demonstrates using Oauth 2.0 authorization tokens in order to control access to a Google Cloud Function. It takes an auth token as a POST parameter and validates that against an IAM controlled GCS bucket before allowing access to the rest of the function. This approach allows service accounts and other authenticated users access to a public HTTPS GCF endpoint without relying on the permissions granted to the default service account attached to all of the Cloud Functions within the GCP project.

# Configuration
Before the code can be deployed, some customizations must be made. In particular, the GCS bucket to be used for auth must be set. See below for instructions regarding the bucket.

See the configuration file config/default.json for all available options. Best practice is to copy config/default.json to config/local.json and make edits there. More functionality is available for environment-specific configs. See https://www.npmjs.com/package/config for more info.

# Deploying to Cloud Functions
The exported function name is "example_auth". To deploy through the web UI, open the GCP Cloud Console and then open the Cloud Shell. Cloud Shell can be opened with the ">_" icon in the top-right of the console.
Run the following command to check out the project code and move into the working directory:

```
git clone https://github.com/ianmaddox/gcs-cf-auth.git
cd gcs-cf-auth
```

This folder contains the file index.js which is the source for the cloud function we will be creating. It also contains `cf_auth.js` which contains the auth logic and package.json which tells Cloud Functions which packages this app needs to run.

Run the following command to deploy the cloud function:
```
gcloud functions deploy authenticated_cf --runtime=nodejs8 --trigger-http --entry-point=example_auth --memory=256MB --source=.
```

For future reference, this same deploy command is available in the handy utility script `src/deploy.sh`

Once the function is deployed, you can verify it was successfully created by navigating to the Cloud Functions page in the Google Cloud Console. Doing so will not close the Cloud Shell. You should see your function with a green checkmark next to it.

Click the function name then click the Trigger tab. Copy the URL displayed here and use it in place of [YOUR_CF_URL] below.

# Enabling access
The actual authentication is done between a specially made service account and a single-purpose GCS bucket.

First, create a service account and download the .json credentials. You will need those to generate your auth tokens.

Next, create an empty bucket in Google Cloud Storage and add the service account you just created as a Storage Object Viewer. This bucket can remain empty unless the service account needs to use it for your particular application.

Once access has been granted, you can generate an auth token and use it to call the Cloud Function. See `src/getToken.js` for a token generator you can use for testing.

# Usage
Once the Cloud Function has been deployed, there is one available API call:
### Testing auth
```
Host and Port:  See deployment process output
Path:           /example_auth
Method:         HTTP POST
Params:
  * auth_token:   An OAuth 2.0 authentication token

Response:
  * On success: HTTP 200 and a test message
  * On failure: HTTP 4xx/5xx and error message
```

Example test commands:
```
AUTH_TOKEN=`node src/getToken.js`
curl -s -X POST "[YOUR_CF_URL]" -H "Content-Type:application/json" --data '{"auth_token":"'$AUTH_TOKEN'"}'
```

Executing the above commands should generate an auth token then use it to call the Cloud Function. If everything was set up correctly, you should see output like "Test Authentication success."

# Integration
You can integrate CF auth into your application by cloning cf_auth.js and modifying `authenticateAndBuildServices()` to create auth objects for each service to which you wish to enable access. In this manner, you can use the supplied token to connect to any compatible service you've authorized for the service account.

See https://github.com/ianmaddox/gcs-pci-tokenizer for an example of CF auth in action.

# Apache 2.0 License
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
