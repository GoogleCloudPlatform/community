---
title: Develop a Serverless Application with Vision API
description: Discover the functionality of Vision API and KGSearch API and deploy a serverless application to Cloud Run that detects breeds of dogs in an image.
author: glasnt
tags: Python 
date_published: 2021-??-??
---

***This code is now in glasnt/community***


Katie McLaughlin | Senior Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to use various serverless technologies to evole an application using the Vision API.

## Objectives

In this tutorial, you do the following:

* Use the Vision API to detect objects in an image, and labels on an object.
* Use image editing libraries to draw detected objects on an image, split an image into multiple objects, and detect the labels on each
* Use the Knowledge Graph Search API to map detected labels to their categories.
* Combine the use of the Vision and Knowledge Graph APIs to detect the breeds of dog in an image.
* Deploy a website that detects breeds of dog in an uploaded image to Cloud Run using Cloud Buildpacks and Secret Manager

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Vision API](https://cloud.google.com/vision/pricing)
* [Cloud Run](https://cloud.google.com/run/pricing)
* [Cloud Build](https://cloud.google.com/build/pricing)
* [Artifact Registry](https://cloud.google.com/artifact-registry/pricing)
* [Secret Manager](https://cloud.google.com/secret-manager/pricing)

The completion of this tutorial should not exceed the free tier. 

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

You can run the commands in this tutorial in [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell) or with a
[local installation of gcloud](https://cloud.google.com/sdk/docs). 

We recommend that you create a new Google Cloud project for this tutorial, so that all created resources can be easily deleted when the tutorial is complete.

1.  In the Cloud Console, on the project selector page, create a Cloud project. For details,
    see [Create a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).
1.  Make sure that billing is enabled for your project. For details, see [Confirm billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project#confirm_billing_is_enabled_on_a_project).

1.  Enable the Cloud Build, Cloud Scheduler, and Cloud Functions APIs:

    - [Enable the APIs in the Cloud Console.](https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com,run.googleapis.com,cloudbuild.googleapis.com,secretmanager.googleapis.com,artifactregistry.googleapis.com)
    - Enable the APIs from the command line:

    ```
    gcloud services enable \
        vision.googleapis.com \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        secretmanager.googleapis.com \
        artifactregistry.googleapis.com
    ```


## Skip to content

This tutorial comes in many sections. It is suggested you follow each in order, but you can also jump to the different major sections. Ensure you complete the setup or configuration steps indicated if you wish to skip ahead.

* [Try out the Vision API from gcloud](#0_gcloud)
* [Setup for tutorial samples](#0_setup)
    * [Try out the Vision API from the Client Libraries](#1_vision_client_api)
    * [Identifying multiple images](#2_vision_image_markup)
    * [Labelling multiple images](#3_vision_split_labels)
* [Configure a Developer Key](#4_setup)
    * [Try out the Knowledge Graph Search API](#4_kgsearch_client_api)
    * [Classifying labels with Knowledge Graph Search](#5_kgsearch_and_vision)
    * [Running the functionality as a service](#6_doggo_demo)
    * [Deploying a service to Cloud Run](#7_doggo_service)
* [Clean up](#9_cleanup)


## <a name="0_gcloud"></a>Try out the Vision API from `gcloud`

There are multiple ways to interact with the Vision API. The simplest way without installing any additional packages or writing any code is to use the `gcloud ml vision` section of the `gcloud` command line. 

In this section, you will gain familiarity with the Vision API through `gcloud`.

1. Using the `gcloud` command line, [detect the objects](https://cloud.google.com/vision/docs/object-localizer) in the sample dog image: 

    ```shell
    gcloud ml vision detect-objects doggo.jpg
    ```

   You should get an output similar to the following: 

    ```json
    {
    "responses": [
        {
        "localizedObjectAnnotations": [
            {
            "boundingPoly": {
                "normalizedVertices": [
                ...
                ]
            },
            "mid": "/m/0bt9lr",
            "name": "Dog",
            "score": 0.9703006
            }
        ]
        }
    ]
    }
    ```

    **Note**: Each time this API is invoked, **results may differ slightly**. As such, the values of `score` and `topicality` may differ slightly in your results, but should genereally match the example code.


2. Run the same command using the [`--format`](https://cloud.google.com/blog/products/it-ops/filtering-and-formatting-fun-with) option to return partial results: 

    ```shel
    gcloud ml vision detect-objects doggo.jpg \
        --format "value(responses[].localizedObjectAnnotations[0].name)"
    ```
    
    You should get an output similar to the following: 

    ```
    Dog
    ```

3. Get more detailed information about the image by [detecting the labels](https://cloud.google.com/vision/docs/labels) on the image: 

    ```shell
    gcloud ml vision detect-labels doggo.jpg
    ```
    
    You should get an output similar to the following: 

    ```json
    {
        "responses": [
            {
            "labelAnnotations": [
                {
                "description": "Pug",
                "mid": "/m/016wkx",
                "score": 0.97835535,
                "topicality": 0.97835535
                },
                {
                "description": "Eye",
                "mid": "/m/014sv8",
                "score": 0.9368354,
                "topicality": 0.9368354
                },
                ...
            ]
            }
        ]
    }
    ```

4. Format the results of the previous image by returning only the label annotation descriptions: 

    ```shell
    gcloud ml vision detect-labels doggo.jpg \
        --format "value(responses[].labelAnnotations[].description)"
    ```

    You should get an output similar to the following: 

    ```json
    ['Pug', 'Eye', 'Dog', 'Carnivore', 'Dog breed', 'Whiskers', 'Fawn', 'Companion dog', 'Wrinkle', 'Toy dog']
    ```

## <a name="0_setup"></a>Setup for tutorial samples

In order to use the included examples in this tutorial, you will have to clone the sample code and configure application credentials.  

### Clone the sample code

The remaining examples in this tutorial use samples and examples from the community tutorial repo. 

1. Clone the sample repo: 

    ```shell
    git clone https://github.com/GoogleCloudPlatform/community
    ```
    
1. Navigate to the sample code: 

    ```shell
    cd community/tutorials/develop-serverless-app-with-vision-api
    ```

### Configure Application Credentials

In order to use the Client APIs, you need to configure application credentials. 

Later sections of this tutorial would make use of a dedicated service account, so this will be created now. 

1. Create a service account: 

    ```shell
    gcloud iam service-accounts create vision-service
    ```


1. Retrieve the email for the newly created service: 

    ```shell
    SERVICE_EMAIL=$(gcloud iam service-accounts list --filter vision-service --format "value(email)")
    ```

1. Generate a key for the newly created service account, saving it to your local file system: 

    ```shell
    gcloud iam service-accounts keys create vision_service.json \
        --iam-account=$SERVICE_EMAIL
    ```
    
1. Associate the key with the Google Application Credentials: 

    ```shell
    export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/vision_service.json
    ```

## <a name="1_vision_client_api"></a>Try out the Vision API from the Client Libraries

The Vision API can be interacted with in a number of programming languages by way of the Client Libaries for the Vision API. This allows more programatic interaction with the API, and more complex processing of the results.

In this section, you will perform similar tasks to the previous section, but this time using the [Vision API client library](https://cloud.google.com/vision/docs/libraries). This tutorial opts to use the [Python library](https://pypi.org/project/google-cloud-vision/), but this API is also available in [Java](https://cloud.google.com/vision/docs/libraries#client-libraries-install-java), [Go](https://cloud.google.com/vision/docs/libraries#client-libraries-install-go), [Node.js](https://cloud.google.com/vision/docs/libraries#client-libraries-install-nodejs), [Ruby](https://cloud.google.com/vision/docs/libraries#client-libraries-install-ruby), or [C#](https://cloud.google.com/vision/docs/libraries#client-libraries-install-csharp). 

1. Install the Python Vision API Client Library (you may choose to first create a `virtualenv`): 

    ```shell
    pip3 install google-cloud-vision==2.3.1
    ```
    
1. Open the code sample and read the contents: 

    ```shell
    cat 1_vision_client_api/vision.py
    ```

    This code: 

    1. Initialises the Vision API
    1. Loads the sample image from file
    1. Performs the same steps as the previous section:
        * detecting the objects,
        * filtering the object information, 
        * detecting the labels, and 
        * filtering the label information.

1. Run the code sample:

    ```shell
    python3 1_vision_client_api/vision.py
    ```

    You should get an output similar to the "Try the Vision API from `gcloud`" step.


## <a name="2_vision_image_markup"></a>Identifying multiple images

So far the source image has been of one primary object. When multiple objects are in an image, the information from the Vision API can be used to draw bounding boxes on the image to show where the separate objects were detected.

In this section we will use a image manipulation library, `pillow`, to draw the `normalized_vertices`, ignored from previous steps. 

We will be using a new sample image with multiple objects, showing how different objects are detected by the Vision API. 

1. Re-run the earlier object detection example, using the provided sample image of two dogs. 
    ```shell
    gcloud ml vision detect-objects two-doggos.jpg
    ```

    Notice in the output that there are two `localizedObjectAnnotations` returned. Each of these have their own `boundingPoly` output of four `localizedObjectAnnotations` x/y co-ordinates.

    These are the four corners of a bounding boxes for each of the detected objects. We will now run a script that will draw these boxes onto the image.

1. Install the `pillow` library:

    ```shell
    pip3 install Pillow
    ```
    
1. Open the code sample and read the contents: 

    ```shell
    cat 2_vision_image_markup/markup.py
    ```

    This code: 

    1. Initialises the Vision API.
    1. Loads the second sample image from file.
    1. Performs the object detection.
    1. For each object detected, it draws a box around the object using the values of the `boundingPoly`.
    1. Saves the resulting image.


1. Run the code sample:

    ```shell
    python3 2_vision_image_markup/markup.py
    ```

    You should get the created file `result.png`, that has two boxes drawn in blue around the two dogs in the image.

## <a name="3_vision_split_labels"></a>Labelling multiple images

Since the image is now more complex, each object in isolation needs to be processed to run the more detailed process of label analysis. Processing each object in an image allows for differences in objects to be identified. 

In this section, we extend the previous example by isolating each object detected and run label detection on each in isolation. This allows us to get more detailed information for each object in an image.

1. Open the code sample and read the contents: 

    ```shell
    cat 3_vision_split_labels/split_labels.py
    ```

    This code: 

    1. Initialises the Vision API.
    1. Loads the second sample image from file.
    1. Performs the object detection.
    1. For each object detected, it:
        1. Crops the image and saves it to a separate file.
        1. Loads the file, and detects the full labels.
        1. Prints the new file name and the resulting labels.


1. Run the code sample:

    ```shell
    python3 3_vision_split_labels/split_labels.py
    ```

    You should get two images created, `doggo_1.png` and `doggo_2.png`, with their labels printed in your result.

## <a name="4_kgsearch_client_api"></a>Try out the Knowledge Graph Search API

Retrieving a number of labels of an object is useful information, but being able to identify the classification of those labels is useful knowledge. Each object and label in the earlier examples came with a `mid` or machine-generated identifier. These are unique identifiers that correspond to an entity's Google Knowledge Graph entry.

In this section, you'll start to look at the Knowledge Graph Search API, and use this API to further process the returned `mid` values. The Knowledge Graph Search API is accessible from the discovery-based API library rather than a dedicated package like Vision API was.


### <a name="4_setup"></a>Configure a Developer Key

Before trying the Knowledge Graph Search API, you will need to register a developer key. 

1. [Enable the kgsearch API through the Console](https://console.developers.google.com/start/api?id=kgsearch.googleapis.com&credential=client_key). Ensure you select the project for your tutorial.
1. Click **Go to credentials**.
1. Confirm "Knowledge Graph Search API" is selected under "Which API are you using?"
1. Under "Credential Type", select "Public data". 
1. Click **Next**. 
1. Copy the value of the "API Key". 
1. Store this value in the `KGSEARCH_API` environment variable: 

    ```shell
    export KGSEARCH_API="<value>"
    ```

You can retrieve this value again by going to the [Credentials](https://console.cloud.google.com/apis/credentials) screen and copying the value from "API keys". 

### Using the Knowledge Graph API

1. Re-run the earlier example of detecting the labels in an image: 

    ```shell
    gcloud ml vision detect-labels doggo.jpg
    ```

   Notice in the output the `description` "Pug" is associated with the `mid` "/m/016wkx".

1. Install the `google-api-python-client` package: 

    ```shell
    pip3 install google-api-python-client
    ```

1. Open the code sample and read the contents: 

    ```shell
    cat 4_kgsearch_client_api/kgsearch.py
    ```

    This code: 

    1. Imports the Discovery API
    1. Builds a resource class for the Knowledge Graph Search API, allowing it to be used.
    1. Searches for entities with the `mid`, printing the results.

1. Run the code sample:

    ```shell
    python3 4_kgsearch_client_api/kgsearch.py
    ```

    You should get a dictionary result showing a `itemListElement`, with the `name` "Pug", and `description` "Dog breed". 

## <a name="5_kgsearch_and_vision"></a>Classifying labels with Knowledge Graph Search

In the previous example, you identified that the label "Pug" was a dog breed. Earlier examples showed the labels are returned in decreasing order of score. By checking the description of each label and returning the breed of dog as soon as it is found, we can quickly establish the breed, if known, of each object detected in an image. 

In this section, you'll connect the Vision API and Knowledge Graph Search API and detect breeds of dog in the sample image. 


1. Open the code sample and read the contents: 

    ```shell
    cat 5_kgsearch_and_vision/showbreeds.py
    ```

    This code: 

    1. Initialises both the Vision and Discovery API.
    1. Loads the sample image of two dogs from file. 
    1. Extends the earlier image splitting example: 
        1. For each object detected, it:
            1. Prints all labels.
            1. Gets the Knowledge Search Graph entries for the `mid`.
            1. Finds the earliest instance (by order of decreasing confidence score) of a breed of dog.
            1. If found, prints the dog breed.

1. Run the code sample:

    ```shell
    python3 5_kgsearch_and_vision/showbreeds.py
    ```

    You should get: 
     
      * two generated images, `doggo_1.png` and `doggo_2.png`
      * for both images: 
        * the list of labels, and 
        * which label was detected as the breed. 
        
    The result should be: Standard Schnauzer, and Pug. 

## <a name="6_doggo_demo"></a>Running the functionality as a service

The present implementation separates output into images and console output.

By wrapping the functionality in a web application, the results can be more visuality appealing. 

In this section, you'll run a small Flask application that provides a richer implementation of the previous code. This tutorial opts to use [Flask](https://flask.palletsprojects.com/en/2.0.x/), a popular micro web framework for Python.

1. Navigate to the code sample and list the directory contents: 

    ```shell
    cd 6_doggo_demo
    ls
    ```

    You'll notice several files:

        * `app.py`, a Flask app with similar contents to the most recent example.
        * `requirements.txt`, a file listing all the packages installed so far, plus `Flask`
        * a copy of the sample image, for ease of use.
    
1. Create a new virtualenv in this directory (if you haven't already): 

    ```shell
    python3 -m venv venv
    source venv/bin/activate
    ```

1. Install the dependencies: 

    ```shell
    pip3 install -r requirements.txt
    ```

1. Run the local web server: 

    ```shell
    python3 app.py
    ```

1. Navigate to the application: [http://localhost:8080](http://localhost:8080)

    You'll notice an output similar to the previous examples, except the images are inline to the results. 

1. Stop the local web server by entering `Ctrl-C`. 


## <a name="7_doggo_service"></a>Deploying a service to Cloud Run

While the most recent example works well on the local machine, it requires locally configured development environments, API keys, and programming knowledge. It also could do with visual improvements on top of the previous output of the images and text.

In this section, you will use the provided code to deploy the service to Cloud Run, and use Secret Manager to store credentials. This tutorial opts to use [Cloud Buildpacks](https://github.com/GoogleCloudPlatform/buildpacks) for each of deployment to Cloud Run, and `gunicorn` as a production-ready web server.

You'll also notice from the last section that there are images being created and stored in the local file system. This ephemeral content won't persist in a serverless deployment. This section instead uses streamed images so no files are stored within the running service.

### Try the service locally

1. Navigate to the code sample and list the directory contents: 

    ```
    cd ../7_doggo_service
    ls -R
    ```

    You'll notice several files: 

        * `app.py`, a Flask app with similar contents to the most recent example, with some changes to have information output in a dictionary, and streamed images. 
        * `requirements.txt`, the same packages as the last example, adding `gunicorn`.
        * `Procfile`, a file defining how to start the Flask app. 
        * `templates/index.html`, a template to show nicer output. 
    
1. If you have your virtualenv setup and active from the last step, no change required. Otherwise, create a new virtualenv in this directory, installing the depedencies: 

    ```
    python3 -m venv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
    ```

1. Run the application locally through `gunicorn`: 

    ```
    python3 -m gunicorn app:app
    ```

    The previous step used the Flask development server, and when you started it, it said not to use it in production. `gunicorn` is a production-ready web server. 

1. Navigate to the application: [http://localhost:8080](http://localhost:8080)

    Note that this application allows for custom uploaded images. 

1. In the upload dialog, select the provided `two-doggos.jpg` and click **Upload**. Wait while the image is processed.

    Note how the result is similar to the previous output, but in a refined visual format.

1. Upload the provided `doggo.jpg` file. 

    Note how the output is for a single dog. 

1. Upload an image without a dog, such as the [Google Cloud logo](https://upload.wikimedia.org/wikipedia/en/thumb/5/51/Google_Cloud_logo.svg/2880px-Google_Cloud_logo.svg.png). 

    Note how the output detects no dogs.

### Setup elements

Before you can deploy the service, we will need to handle the secret values we previously used environment variables for. 

The `GOOGLE_APPLICATION_CREDENTIALS` value is not required, as Cloud Run services handle their application credentials by way of their default service account. 

The `KGSEARCH_API` value, however, should be secured and referenced by the service, which we can do with Secret Manager's integration with Cloud Run, which means we don't need to make any code changes.

1. Create a secret with the value of the `KGSEARCH_API`: 

    ```
    echo -n "$KGSEARCH_API" | gcloud secrets create kgsearch_key --data-file -
    ```

1. Confirm the value of the secret matches the expected value: 

    ```
    echo $KGSEARCH_API
    gcloud secrets versions access latest --secret kgsearch_key
    ```

    Note that if you see a `%`, or a lack of new line between the end of your secret and your terminal prompt, this is expected, as the secret was created without a newline ending, and it's output can be malformated in the terminal.

1. Grant access to the secret from the default Cloud Run service: 

    ```
    DEFAULT_SA=$(gcloud iam service-accounts list --filter compute --format "value(email)")
    gcloud secrets add-iam-policy-binding kgsearch_key \
        --member serviceAccount:$DEFAULT_SA \
        --role roles/secretmanager.secretAccessor
    ```

### Deploy to Cloud Run

Now you have setup the secret, you can deploy your application:

1. Ensure you are in the correct directory: 

    ```
    pwd
    ```

    You should see `7_doggo_service`.

1. Deploy the provided code sample to Cloud Run, referencing the created secret: 

    ```
    gcloud beta run deploy demo-doggo \
        --source . \
        --platform managed --region us-central1 --allow-unauthenticated \
        --set-secrets KGSEARCH_API=kgsearch_key:latest
    ```

    If prompted to create a new Artifact Registry repository, type 'Y' to continue.

    This command: 
    
    * Creates a new image for the code within the current directory using [Cloud Buildpacks](https://github.com/GoogleCloudPlatform/buildpacks)
    * Stores the image in Artifact Registry
    * Deploys a new public service, using the newly created image, referencing the secret.

    Once complete, note the returned service URL from this command. 

1. Open the generated service URL. You can also find the URL from the command line: 

    ```
    gcloud run services describe demo-doggo --format="value(service.url)"
    ```

1. Try uploading the sample image, and viewing the results. 

1. Try uploading other images, and viewing the results. 

    The application will:

     * if one or more dogs are detected:
       * return the breed, if found.
       * otherwise, say "An amazing doggo".
     * if no dogs are detected:
       * return "Uploaded image contains no dogs". 

You have now successfully deployed a serverless application that uses the Vision API and Knowledge Graph API to detect dogs in uploaded images. 

## Extending the application

This application focuses on dogs and dog breeds, but could be extended for other objects and label group classifications. 

For instance, try editing the service to detect difference types of food in an uploaded image. 

To find other potential categories, use the [`gcloud ml`](#0_gcloud) CLI on a few test images, then use the [kgsearch API](#4_kgsearch_client_api) to inspect common mids. 


## <a name="9-cleanup"></a> Clean up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, delete the project created specifically for this tutorial. 

1. In the Cloud Console, go to the **Manage resources** page.
1. In the project list, select the project that you want to delete, and then click **Delete**.
1. In the dialog, type the project ID and then click **Shut down**.


## Learn More

 * Try the [Dense document text detection tutorial](https://cloud.google.com/vision/docs/fulltext-annotations)
 * Watch the [Serverless Demo Derby from I/O '21](https://www.youtube.com/watch?v=g4ES7wXn8oQ)


## Image Credits

doggo.jpg - Photo by [Marcus Cramer](https://unsplash.com/@marcuslcramer?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on [Unsplash](https://unsplash.com/s/photos/pug?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText)

two_doggos.jpg - Photo by [Sebastian Coman Travel](https://unsplash.com/@sebcomantravel?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on [Unsplash](https://unsplash.com/s/photos/two-dogs?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText)

