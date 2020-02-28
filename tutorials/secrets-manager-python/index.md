---
<<<<<<< HEAD
title: Using Google Cloud Secrets Manager with Python
description: Simple example around using secret manager with python.
author: thejaysmith
tags: Secret Manager, KMS, Security, Python
date_published: 2020-01-07
=======
title: Use Secret Manager with Python
description: Store and access a secret with a Python app, using Secret Manager.
author: thejaysmith
tags: Secret Manager, KMS, Security, Python
date_published: 2020-01-17
>>>>>>> 78d53375360e36685d99946d24441c920e292c30
---

Jason "Jay" Smith | Customer Engineer Specialist | Google Cloud

<<<<<<< HEAD
## Using Google Cloud Secrets Manager with Python

Google Cloud has announced [Secret Manager](https://cloud.google.com/secret-manager/docs/ "Secret Manager") as a secure and convenient tool for storing API keys, passwords, certificates, and other sensitive data. It is currently in Beta but it can still provide you with a secure way to store and use keys. It uses a simple key value structure to store keys.

The purposes of this tutorial is to show a simple example in storing and accessing a secret with a Python app. We will create a simple containerized application runing on [Cloud Run](https://cloud.google.com/run/ "Cloud Run") that can pull financial data.

We will use one of my favorite financial APIS, [AlphaVantage](https://www.alphavantage.co/). They have a free tier that allows you to make 500 calls per 24 hour period so it's perfect for testing API features. All of the code that we will use is in the `py-secrets-manager` directory.

First will want to set the stage of our environment. Let's set some project variables, enable our needed APIs and install gcloud beta components.

``` bash
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
secretmanager.googleapis.com

# Enable gcloud beta components
gcloud components update
gcloud components install beta
```

Next, let's give our service account the ability to access the Secret Manager.

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$PROJ_NUMBER-compute@developer.gserviceaccount.com --role roles/secretmanager.admin
```

Now let's create our secret in Secret Manager. You are able to do this in the UI or directly via the API but today we will use our gcloud. You can read more about other usage methods [here](https://cloud.google.com/secret-manager/docs/how-to-use-secret-manager-api, "here").

 If you haven't already, go [here](https://www.alphavantage.co/support/#api-key, "AlphaVantage API Key") to acquire your API key from AlphaVantage. Once you have the key, replace the "Your AlphaVantage API Key" text with the actual key. Then run the below command to create a secret called `alpha-vantage-key`.

```bash
echo -n "Your AlphaVantage API Key" | \
    gcloud beta secrets create alpha-vantage-key --replication-policy=automatic --data-file=-
```

This creates a key named `alpha-vantage-key` with the value being your API key. This example used a string but if you were given a flat file such as a JSON file, you could set that are value.

Now the next step is to deploy our application to Google Cloud Run. The first step is to containerize the application. First, I would encourage you to review the code in `currencyapp/app.py`. It is a very simple Flask application that will read take an input (stock symbol) and give you a read out of the time series in 15 minute intervals.

```python
secrets = secretmanager.SecretManagerServiceClient()

ALPHA_VANTAGE_KEY = secrets.access_secret_version("projects/"+PROJECT_ID+"/secrets/alpha-vantage-key/versions/1").payload.data.decode("utf-8")
```

In the above block, we create a `secrets` object using [Python Client for Secret Manager API](https://github.com/googleapis/python-secret-manager, "Python Client for Secret Manager API"). Next, we create a variable called `ALPHA_VANTAGE_KEY`. We use `access_secret_version` and pass the name of the key. The standard format of the name will be `projects/PROJECT ID/secrets/SECRET NAME/versions/VERSION NUMBER`. From there I am pulling the key from `payload.data` attributes then decoding the response. This will give me the key in plain text.

```python
@app.route('/api/v1/symbol', methods=['POST'])
def get_time_series():
    if request.method == 'POST':
        symbol = request.args['symbol']
        data, metadata = ts.get_intraday(
                symbol, interval='15min', outputsize="25")
    return jsonify(data=data)
```

This route will create an endpoint call `/api/v1/symbol`. This simple example will take any value for 'symbol' abd then use this [AlphaVantage Python Library](https://github.com/RomelTorres/alpha_vantage, "AlphaVantage") to do the stock symbol lookup and give us information in 15 minute intervals. You can review the rest of the code for some standard Flask code.

Now let's containerize the application. Navigate to `py-secrets-manager/currencyapp` as that will be where we will execute the below command. Be sure to replace `PROJECT-ID` with your actual Project ID.

```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/currency-secret .
```

We just created a container called "currency-secret". This has our app.py application and is ready to deploy to Google Cloud. Let's run the below command.

```bash
gcloud run deploy currency-secret --image gcr.io/PROJECT-ID/currency-secret --platform managed --region us-central1 --allow-unauthenticated --update-env-vars PROJECTID=$PROJECT_ID
```

This command will do a few things.

1. It will create a service called `currency-secret`
2. It will use the image that we created using `gcloud builds submit` ealier
3. It will deployed on the Fully Managed version of Cloud Run
   * You can learn more about the differences between Fully Managed and Anthos version [here](https://cloud.google.com/run/choosing-a-platform, "Cloud Run Platform")
4. We will deploy in the `us-cental1` region but you can choose a different [supported region](https://cloud.google.com/run/docs/setup#before-you-begin, "Supported Region")
5. This will allow the service to be publicly accessible to the internet
6. We will set an environment variable for Project ID

Give yourself about 2-3 minutes for the service to deploy and start. Once done, run the below command. It will grab your service's URL and assign it to a variable called `SVCURL`

```bash
export SVCURL="$(gcloud run services list --platform managed --format=json | grep "currency-secret" | grep "url" | head -1 | cut -d: -f2- | tr -d '"')/api/v1/symbol?symbol=GOOG"
echo $SVCURL
```

You will see a URL such
`https://currency-secret-xxxxxxxxxx.a.run.app/api/v1/symbol?symbol=GOOG`

The first part is the service name followed by a random string and then the URL base of `run.app`. In our Flask app, we have a route called `/api/v1/symbol` that only accepts POST commands. It looks for a key named `symbol` and the corresponding value should be a NYSE stock symbol. For our example, we used `GOOG` but you can use whatever you prefer.

Finally, let's curl this URL and see what we get.

```bash
curl -X POST $SVCURL
```

You will get a JSON response that looks similar to this

```bash
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
```

These are 15 minute snapshots of the stock price of the GOOG symbol (or whichever smbol you chose). Congratulations, you were able to execute an application that used a third-party API with key and didn't need to include the key in the code. This is great when you are wanting to execute code with Google Cloud but worry about sharing and storing keys.

In a future tutorial, we will use JSON keys and show full [Cloud KMS](https://cloud.google.com/kms/, "Google Cloud KMS") integration.
=======
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
>>>>>>> 78d53375360e36685d99946d24441c920e292c30
