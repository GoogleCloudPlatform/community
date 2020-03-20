---
title: Firebase Auth on your App Engine Python application
description: Learn how to authenticate API requests using Firebase Auth on App Engine.
author: archelogos
tags: App Engine, Python, Falcon, API, Firebase, Auth, JWT
date_published: 2017-05-05
---

In this tutorial you will learn how to authenticate the requests that hit your API with JSON Web Tokens (JWT) using Firebase Auth.

[Firebase][Firebase] is a platform that provides you tools and infrastructure to build your apps easily.

To understand properly what a JWT is, you can find more information about it here: [JWT](https://jwt.io/).

This guide takes the basic concepts of an API from this tutorial: [Previous Tutorial](https://cloud.google.com/community/tutorials/appengine-python-falcon).

[Firebase]: https://firebase.google.com/

## Objectives

1. Create a Python app that uses Falcon as a framework.
2. Run the app locally.
3. Use Firebase Auth to authenticate and validate the requests.
4. Deploy the Python app to Google App Engine standard environment.

## Costs

This tutorial does not use billable components of Google Cloud Platform so
you do not need to enable the billing for your project to complete this tutorial.

## Before you begin

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/) and make note of the project ID.
2. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).
3. Import the Google Cloud Project in the [Firebase Console](https://console.firebase.google.com/).
4. Go to the Authentication section in the Firebase Console and enable at least one Sign-in provider. Follow this link
in case you need some information about how to do it, see: [https://firebase.google.com/docs/auth/](https://firebase.google.com/docs/auth/).

## Preparing the app

1.  Follow the steps described in the [previous tutorial](https://cloud.google.com/community/tutorials/appengine-python-falcon). Once the app is running locally, move on to the next steps.

2.  Add the following line to the [`requirements.txt`][requirements] file:

        firebase-admin==1.0.0

3.  Modify the [`app.yaml`][app] file adding the following contents:

        env_variables:
          GCLOUD_PROJECT: '[YOUR_PROJECT_ID]'

4.  Import the `firebase-admin` library to the [`__init__.py`][init] file and intialize the Firebase app.

        import firebase_admin
    
        ...
    
        default_app = firebase_admin.initialize_app()
    
5.  Modify now the [`AuthMiddleware`][middleware] using the Firebase ID Token Validator.

        ...
    
        from firebase_admin import auth
    
        class AuthMiddleware(object):
        """."""
    
            def process_request(self, req, resp):
                auth_value = req.get_header('Authorization', None)
                if auth_value is None or len(auth_value.split(' ')) != 2 or not self.token_is_valid(req, auth_value.split(' ')[1]):
                    raise falcon.HTTPUnauthorized(description='Unauthorized')
    
            def token_is_valid(self, req, token):
                try:
                    decoded_token = auth.verify_id_token(token)
                    req.context['auth_user'] = decoded_token
                except Exception as e:
                    return False
                if not decoded_token:
                   return False
                return True

    Because this middleware applies to all endpoints, from now you will need to send your requests
    with an 'Authorization' header which contains a valid JWT Token.

        Header['Authorization'] = 'Bearer [JWT_TOKEN]'
    
    You could also verify the user role in a separated Falcon hook to determine if the user has enough
    permission to do the operation.

        def is_admin(req, resp, resource, params):
            # Good place to check the user role.
            logging.info(req.context['auth_user'])
    
        ...
    
        @falcon.before(api_key)
        @falcon.before(is_admin)
        @falcon.after(say_bye_after_operation)
        def on_post(self, req, resp):
    
        ...
    
    As you can see, we are using the `req.context` to pass variables from the middleware layer to the hooks.        

6.  To generate ID Tokens and because of Firebase does not provide an API to generate them,
    we have to simulate a client sign in.

    To do that you can use several Firebase client libraries like [AngularFire](https://github.com/firebase/angularfire)
    or [FirebaseUI](https://github.com/firebase/FirebaseUI).
    You can find a sample in this repo [jwt][jwt]. Be sure that you set your Firebase Credentials before generate a token.

## Running the app

1. Install the dependencies into the `lib` folder with pip.

        pip install -t lib -r requirements.txt

2. Execute the following command to run the app.

        dev_appserver.py .

3. Visit http://localhost:8080 to see the app running.

4. Run the JWT generator using (for instance) a NodeJS http server.

   Be sure that you have already installed Node.js in your local machine and
   install a http-server module globally.

        node -v

        npm -g install http-server

        cd jwt

        http-server . -p 9000

   Visit http://localhost:9000 in the browser, sign in and copy the JWT.

4. Run the following command to test one of the endpoints:

        curl -X GET \
        http://localhost:8080/ \
        -H 'authorization: Bearer [JWT_TOKEN]' \
        -H 'cache-control: no-cache'

## Deploying the app

1. Run the following command to deploy your app:

        gcloud app deploy

2. Visit `http://[YOUR_PROJECT_ID].appspot.com` to see the deployed app.

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

3. Run the following command to view your app:

        gcloud app browse

[requirements]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-api-firebase-auth/requirements.txt
[app]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-api-firebase-auth/app.yaml
[init]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-api-firebase-auth/api/__init__.py
[middleware]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-api-firebase-auth/api/middleware.py
[jwt]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-api-firebase-auth/jwt
