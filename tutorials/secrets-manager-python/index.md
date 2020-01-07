---
title: Using Google Cloud Secrets Manager with Python
description: Simple best practices around using Google's Cloud Secret Manager with Python
author: thejaysmith
tags: Secret Manager, KMS, Security, Python
date_published: 2020-01-09
---

Jason "Jay" Smith | Customer Engineer Specialist | Google Cloud

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
