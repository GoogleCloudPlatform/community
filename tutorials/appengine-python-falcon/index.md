---
title: Falcon API on App Engine standard environment
description: Learn how to build a Falcon API in the App Engine standard environment.
author: archelogos
tags: App Engine, Python, Falcon, API
date_published: 2017-04-27
---

This tutorial shows how to build a Python API with [Falcon][falcon].

Falcon is a high-performance Python framework for building cloud APIs. It follows the REST architectural style, and tries to do as little as possible while remaining highly effective.

In order to follow this guide, you will need to install Python in your local machine.

[python]: https://www.python.org/
[falcon]: https://falconframework.org/

## Objectives

1. Create a Python app that uses Falcon as a framework.
2. Run the app locally.
3. Deploy the Python app to Google App Engine standard environment.

## Costs

This tutorial does not use billable components of Google Cloud Platform so
you do not need to enable the billing for your project to complete this tutorial.

## Before you begin

1.  Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/) and make note of the project ID.
2.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/)

## Preparing the app

1.  Create a [`requirements.txt`][requirements] file with the following contents:

        falcon==1.1.0

2.  Create an [`appengine_config.py`][appengine_config] file with the following contents:

        from google.appengine.ext import vendor
        vendor.add('lib')
 
3.  Create an [`app.yaml`][app] file with the following contents:

         runtime: python27
         api_version: 1
         threadsafe: true

         handlers:
           - url: /.*
             script: api.app
  
4.  Copy the [`api`][api] module in your workspace

    This module contains the following files:

    1.  [`__init__.py`][init]. This is where the api module is initialized and its routes are created.
        You can see how the app variable is defined using the Falcon library.

            app = falcon.API(middleware=[
                AuthMiddleware()
            ])
    
        You can add a route with the following method:

            app.add_route('/', Resource())
        
    2.  The resources can be defined in the [`resources.py`][resources] file. The `Resource` class
        implements four different methods `on_get`, `on_post`, `on_patch` and `on_delete`
        that define the endpoints for each HTTP method.

            def on_get(self, req, resp):
                ...
    
            def on_post(self, req, resp):
                ...
    
            def on_patch(self, req, resp):
                ...
    
            def on_delete(self, req, resp):
                ...
    
    3.  In the [`middleware.py`][middleware] file you can find the `AuthMiddleware` class
        which is used to ensure that all requests are authenticated.
        Because this is just an example, it is not implemented with any kind
        of validation.

            class AuthMiddleware(object):

                def process_request(self, req, resp):
                    token = req.get_header('Authorization')
                    ...

    4.  The [`hooks.py`][hooks] file contains definitions of custom functions that can be called
        before or after an endpoint function is executed. They can be used, for instance, to validate
        the input data or serialize the API responses.

## Running the app

1. Install the dependencies into the `lib` folder with pip.

        pip install -t lib -r requirements.txt

2. Execute the following command to run the app.

        dev_appserver.py .

3. Visit http://localhost:8080 to see the app running.

4. Run the following command to test one of the endpoints:

        curl -X GET \
        http://localhost:8080/ \
        -H 'authorization: Bearer 1234' \
        -H 'cache-control: no-cache'

## Deploying the app

1. Run the following command to deploy your app:

        gcloud app deploy

2. Visit `http://[YOUR_PROJECT_ID].appspot.com` to see the deployed app.

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

3. Run the following command to view your app:

        gcloud app browse

[requirements]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/requirements.txt
[appengine_config]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/appengine_config.py
[app]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/app.yaml
[api]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/api
[init]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/api/__init__.py
[resources]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/api/resources.py
[middleware]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/api/middleware.py
[hooks]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-python-falcon/api/hooks.py
