---
title: Build and deploy a Flask CRUD API with Firestore and Cloud Run
description: Build a CRUD (create, read, update, delete) API to manage to-do lists using Flask (a microframework for Python) and Firestore, and deploy with Cloud Run.
author: timtech4u
tags: Flask Framework, Python 3, REST API, Firestore, Cloud Run
date_published: 2019-09-03
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you build a CRUD (create, read, update, delete) API to manage to-do lists using Flask (a
microframework for Python) and Firestore (a flexible, scalable database for mobile, web, and server development), and you deploy the API to
[Cloud Run](https://cloud.google.com/run/) (a serverless environment to run containers
on Google Cloud).

[Firestore](https://firebase.google.com/docs/firestore) stores data as collections of documents. It also features
richer, faster queries and scales further than the [Firebase Realtime Database](https://firebase.google.com/docs/database).
You can manage to-do list fields through the API.

# Requirements

-  [Python3.7](https://www.python.org/downloads/) 
-  [Flask](https://github.com/pallets/flask) 
-  [Firebase Admin Python SDK](https://github.com/firebase/firebase-admin-python) 

# Before you begin

1.  [Create a new Firebase project](https://console.firebase.google.com), or use an existing one.
    1.  Click **Database** and **Create database** in the Cloud Firestore section.
    1.  Set your [security rules](https://firebase.google.com/docs/firestore/security/get-started) and
    [location](https://firebase.google.com/docs/projects/locations).
    
    You should have an initial screen similar to the following:  ![screenshot](https://storage.googleapis.com/gcp-community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run/utHBNSvvO.png)
    
1.  Download your Firebase Service Account Key.
    1.  Click the **Settings** icon at the top of the dashboard.
    1.  Click the **Service Account** tab.
    1.  Select **Python** option for **Admin SDK configuration snippet**, click **Generate new private key**, and save it
        as `key.json`.  ![screenshot](https://storage.googleapis.com/gcp-community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run/e2TxYLV5d.png)

1.  [Create a new Google Cloud project](https://console.cloud.google.com/project?_ga=2.69989718.-735545701.1566156833), or use an 
    existing one. You need the Google Cloud project so that you can deploy to Cloud Run.
1.  Open [Cloud Shell](https://cloud.google.com/shell/) or install the [Cloud SDK](https://cloud.google.com/sdk/docs/).
1.  (Optional) To set up continuous deployment follow the instructions
    [here](https://fullstackgcp.com/simplified-continuous-deployment-on-google-cloud-platform-bc5b0a025c4e).
1.  Ensure that you can run `gcloud -h` on in Cloud Shell.  ![screenshot](https://storage.googleapis.com/gcp-community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run/wH8YC5i0S.png)

# Source code

    # app.py
    
    # Required imports
    import os
    from flask import Flask, request, jsonify
    from firebase_admin import credentials, firestore, initialize_app

    # Initialize Flask app
    app = Flask(__name__)

    # Initialize Firestore DB
    cred = credentials.Certificate('key.json')
    default_app = initialize_app(cred)
    db = firestore.client()
    todo_ref = db.collection('todos')

    @app.route('/add', methods=['POST'])
    def create():
        """
            create() : Add document to Firestore collection with request body.
            Ensure you pass a custom ID as part of json body in post request,
            e.g. json={'id': '1', 'title': 'Write a blog post'}
        """
        try:
            id = request.json['id']
            todo_ref.document(id).set(request.json)
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"

    @app.route('/list', methods=['GET'])
    def read():
        """
            read() : Fetches documents from Firestore collection as JSON.
            todo : Return document that matches query ID.
            all_todos : Return all documents.
        """
        try:
            # Check if ID was passed to URL query
            todo_id = request.args.get('id')
            if todo_id:
                todo = todo_ref.document(todo_id).get()
                return jsonify(todo.to_dict()), 200
            else:
                all_todos = [doc.to_dict() for doc in todo_ref.stream()]
                return jsonify(all_todos), 200
        except Exception as e:
            return f"An Error Occurred: {e}"

    @app.route('/update', methods=['POST', 'PUT'])
    def update():
        """
            update() : Update document in Firestore collection with request body.
            Ensure you pass a custom ID as part of json body in post request,
            e.g. json={'id': '1', 'title': 'Write a blog post today'}
        """
        try:
            id = request.json['id']
            todo_ref.document(id).update(request.json)
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"

    @app.route('/delete', methods=['GET', 'DELETE'])
    def delete():
        """
            delete() : Delete a document from Firestore collection.
        """
        try:
            # Check for ID in URL query
            todo_id = request.args.get('id')
            todo_ref.document(todo_id).delete()
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"

    port = int(os.environ.get('PORT', 8080))
    if __name__ == '__main__':
        app.run(threaded=True, host='0.0.0.0', port=port)

There are individual methods and routes for each action that the API performs. You can improve upon the code snippet and
add more functions to meet your needs.

For each CRUD (create, read, update, delete) action, you define the route and its corresponding
[HTTP method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods). The API implementation tries to perform that 
action and returns a response with the `200` status code if successful. If there's a problem, the implementation returns the
exception's error code.

# Deploy to Cloud Run

To build your API implementation in a container and run it on Cloud Run, you need a `Dockerfile`:

    # Dockerfile
    FROM python:3.7-stretch
    RUN apt-get update -y
    RUN apt-get install -y python-pip python-dev build-essential
    COPY . /app
    WORKDIR /app
    RUN pip install -r requirements.txt
    ENTRYPOINT ["python"]
    CMD ["app.py"]

Ensure that you have a `requirements.txt` file with the following contents:

    # requirements.txt
    flask
    firebase_admin

Finally, create a `cloudbuild.yaml` file, which you will use to trigger builds:

    # cloudbuild.yaml
    steps:
      # build & push the container image
    - name: "gcr.io/kaniko-project/executor:latest"
      args: ["--cache=true", "--cache-ttl=48h", "--destination=gcr.io/$PROJECT_ID/todo:latest"]
      # Deploy container image to Cloud Run
    - name: "gcr.io/cloud-builders/gcloud"
      args: ['beta', 'run', 'deploy', 'todo', '--image', 'gcr.io/$PROJECT_ID/todo:latest', '--region', 'us-central1', '--allow-unauthenticated', '--platform', 'managed']

You can also import your `key.json` Firebase service account file into the same directory; it is recommended that you not 
push it to your source repository. A fast approach to this is to add an additional Cloud Build step that downloads the 
service account from a private location, such as a Cloud Storage bucket.

## Execute the build and deploy steps with Cloud Shell

Run the following command to build your Docker container and push to Container Registry as specified in the 
`cloudbuild.yaml` file.

    gcloud builds submit --config cloudbuild.yaml .

 This also performs the step of deploying to Cloud Run.

## (Optional) Deploy using the Cloud Run Button

Recently, Google announced
[Cloud Run Button](https://cloud.google.com/blog/products/serverless/introducing-cloud-run-button-click-to-deploy-your-git-repos-to-google-cloud),
an image and link that you can add to the `README` file for your source code repositories to allow others to deploy your 
application to Google Cloud using Cloud Run.

The steps to add the Cloud Run Button to your repository are as follows:

1.  Copy and paste this Markdown into your `README.md` file:
    
        [![Run on Google Cloud](https://storage.googleapis.com/cloudrun/button.svg)](https://console.cloud.google.com/cloudshell/editor?shellonly=true&cloudshell_image=gcr.io/cloudrun/button&cloudshell_git_repo=[YOUR_HTTP_GIT_URL])

1.  Replace `[YOUR_HTTP_GIT_URL]` with your HTTP git URL, as in the following example:

        [![Run on Google Cloud](https://storage.googleapis.com/cloudrun/button.svg)](https://console.cloud.google.com/cloudshell/editor?shellonly=true&cloudshell_image=gcr.io/cloudrun/button&cloudshell_git_repo=https://github.com/GoogleCloudPlatform/flask-firestore.git)

    This creates a button like the following:

    [![Run on Google Cloud](https://storage.googleapis.com/cloudrun/button.svg)](https://console.cloud.google.com/cloudshell/editor?shellonly=true&cloudshell_image=gcr.io/cloudrun/button&cloudshell_git_repo=https://github.com/GoogleCloudPlatform/flask-firestore.git)

1.  Ensure that your repository has a `Dockerfile`.
  
# Cleaning up

To prevent unnecessary charges, clean up the resources created for this tutorial. This includes deleting any projects 
that you created for this tutorial.

# Useful links
-  [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/)
-  [Firestore documentation](https://firebase.google.com/docs/firestore) 
-  [Cloud Run documentation](https://cloud.google.com/run/docs/) 
-  [Cloud Build documentation](https://cloud.google.com/cloud-build/docs/)
