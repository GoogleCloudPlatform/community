---
title: Use Secret Manager with Python
description: Store and access a secret with a Python app, using Secret Manager.
author: thejaysmith
tags: Secret Manager, KMS, Security, Python
date_published: 2020-01-17
---

Jason "Jay" Smith | Customer Engineer Specialist | Google Cloud

## Overview of using Secret Manager with Python

[Secret Manager](https://cloud.google.com/secret-manager/docs/) on Google Cloud stores API keys, passwords, 
certificates, and other sensitive data. Secret Manager provides convenience while improving security.

This tutorial shows a simple example of storing and accessing a secret with a Python app. In this tutorial, you create a
simple containerized application running on [Cloud Run](https://cloud.google.com/run/) that can pull financial data.

This tutorial uses the [Alpha Vantage](https://www.alphavantage.co/) financial APIs. Alpha Vantage offers a free tier that 
allows you to make 500 calls per 24-hour period, so it's well suited for testing API features.

The code used in this tutorial is in the
[`py-secrets-manager`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/secrets-manager-python/py-secrets-manager/currencyapp)
directory on GitHub.

## Set up the environment

1.  This tutorial requires a Google Cloud project.
    [Create a new Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
    or open an exisitng project in the [Cloud Console](https://console.cloud.google.com/cloud-resource-manager).
    
1.  You use the Cloud Shell command-line interface in the Cloud Console to run commands in this tutorial. Open Cloud Shell
    by clicking the **Activate Cloud Shell** button in the navigation bar in the upper-right corner of the Cloud Console.

1.  Run the following commands to set some project variables, enable APIs, and install `gcloud` beta components:

        # Set environment variables for project
        export PROJECT_ID=$(gcloud config get-value project)
        export PROJ_NUMBER=$(gcloud projects list --filter="${PROJECT_ID}" --format="value(PROJECT_NUMBER)")
        
        # Enable API services
        gcloud services enable container.googleapis.com \
        containerregistry.googleapis.com \
        cloudbuild.googleapis.com \
        cloudkms.googleapis.com \
        storage-api.googleapis.com \
        storage-component.googleapis.com \
        cloudscheduler.googleapis.com \
        run.googleapis.com \
        secretmanager.googleapis.com
        
        # Enable gcloud beta components
        sudo gcloud components update
        gcloud components install beta

1.  Give your service account the ability to access the Secret Manager:

        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$PROJ_NUMBER-compute@developer.gserviceaccount.com --role roles/secretmanager.admin

## Create the secret in Secret Manager

This tutorial uses the `gcloud` command-line interface to create the secret. You can also create a secret using the web
interface or through the API. For more information, see
[Using the Secret Manager API](https://cloud.google.com/secret-manager/docs/how-to-use-secret-manager-api).

1.  Get your API key from the [Alpha Vantage site](https://www.alphavantage.co/support/#api-key).
1.  Create a secret called `alpha-vantage-key` with this command, replacing `[API_KEY]` with the API key value from the
    previous step:

        echo -n [API_KEY] | gcloud beta secrets create alpha-vantage-key --replication-policy=automatic --data-file=-

    This creates a key named `alpha-vantage-key` with the value of your API key. This example uses a string but, if you were
    given a flat file such as a JSON file, you could set that value.

## Get the app code

1.  Run the following command to get the app code:

        git clone https://github.com/GoogleCloudPlatform/community gcp-community

1.  Navigate into the app directory:

        cd gcp-community/tutorials/secrets-manager-python/py-secrets-manager/currencyapp

## Review the app code

Review the code in
[`app.py`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/secrets-manager-python/py-secrets-manager/currencyapp),
which is a simple Flask app that takes an input (a stock symbol) and returns stock information in 15-minute intervals.

The following excerpt from the app creates a `secrets` object using the
[Python Client for Secret Manager API](https://github.com/googleapis/python-secret-manager). Then it creates a variable, 
`ALPHA_VANTAGE_KEY`, which is assigned the name of the key. The standard format of the name is
`projects/PROJECT_ID/secrets/SECRET_NAME/versions/VERSION_NUMBER`. The key is pulled from from `payload.data` attributes, 
and the response is decoded, giving the key in plain text.

    secrets = secretmanager.SecretManagerServiceClient()

    ALPHA_VANTAGE_KEY = secrets.access_secret_version("projects/"+PROJECT_ID+"/secrets/alpha-vantage-key/versions/1").payload.data.decode("utf-8")

The following excerpt creates an endpoint called `/api/v1/symbol` and uses the
[Alpha Vantage Python library](https://github.com/RomelTorres/alpha_vantage) to look up the stock symbol and give
information in 15 minute intervals:

    @app.route('/api/v1/symbol', methods=['POST'])
    def get_time_series():
        if request.method == 'POST':
            symbol = request.args['symbol']
            data, metadata = ts.get_intraday(
                    symbol, interval='15min', outputsize="25")
        return jsonify(data=data)

## Containerize the application
 
1.  In the `py-secrets-manager/currencyapp` directory, run the following command, replacing `[PROJECT-ID]` with your
    actual project ID:

        gcloud builds submit --tag gcr.io/[PROJECT-ID]/currency-secret .

    This command creates a container called `currency-secret`, which has your `app.py` application and is ready to deploy
    to Google Cloud. 

## Deploy and test the application

1.  Run the following command, replacing `[PROJECT-ID]` with your actual project ID:

        gcloud run deploy currency-secret --image gcr.io/[PROJECT-ID]/currency-secret --platform managed --region us-central1 --allow-unauthenticated --update-env-vars PROJECTID=$PROJECT_ID

    This command does the following:

    - Creates a service called `currency-secret`, using the image that was created using `gcloud builds submit` in the 
      previous step.
    - Deploys on the Fully Managed version of Cloud Run. You can learn more about the differences between
      Fully Managed and Anthos version [here](https://cloud.google.com/run/choosing-a-platform).
    - Makes the service publicly accessible on the internet, with the `--allow-unauthenticated` option.
    - Sets an environment variable for the project ID. 

1.  Wait for a few minutes for the service to deploy and start.
1.  Run the following command, which assigns your service's URL to the variable `SVCURL`:

        export SVCURL="$(gcloud run services list --platform managed --format=json | grep "currency-secret" | grep "url" | head -1 | cut -d: -f2- | tr -d '"')/api/v1/symbol?symbol=GOOG"
    
1.  Run the following command:

        echo $SVCURL
 
    You will see a URL such as this:
    `https://currency-secret-xxxxxxxxxx.a.run.app/api/v1/symbol?symbol=GOOG`

    The first part is the service name followed by a random string and then the URL base of `run.app`. In our Flask app, we 
    have a route called `/api/v1/symbol` that only accepts POST commands. It looks for a key named `symbol` and the 
    corresponding value should be an NYSE stock symbol. For our example, we used `GOOG` but you can use whatever you prefer.

1.  Use `curl` to query the service URL:

        curl -X POST $SVCURL

    You get a JSON response similar to the following:

        {
            "data": {
                "2019-12-31 10:45:00": {
                    "1. open": "1331.8400",
                    "2. high": "1332.0000",
                    "3. low": "1330.4948",
                    "4. close": "1331.0000",
                    "5. volume": "40492"
                },
                "2019-12-31 11:00:00": {
                    "1. open": "1330.3100",
                    "2. high": "1331.2800",
                    "3. low": "1329.4301",
                    "4. close": "1330.7900",
                    "5. volume": "23349"
                },

    These are 15-minute snapshots of the stock price associated with the symbol passed as a parameter in the service URL.
    
Congratulations! You ran an application that used a third-party API with a key and didn't need to include the key in the 
code. This is great when you want to execute code with Google Cloud but worry about sharing and storing keys.
