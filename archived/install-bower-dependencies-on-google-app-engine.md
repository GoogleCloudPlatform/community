---
title: Install Bower dependencies on App Engine flexible environment
description: Learn how to use Bower in a Node.js App Engine flexible environment app.
author: jmdobry
tags: App Engine, Bower, Node.js
date_published: 2016-05-20
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

If you're using [Bower](http://bower.io/) to install web dependencies for your app and you're
deploying your app to App Engine flexible environment, then there are
several ways to make sure the dependencies are available to your deployed app.
This tutorial discusses three different methods.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Install Bower:

        npm install -g bower

1. Create a `bower.json` file if you don't already have one:

        bower init

1. Then save new dependencies to your `bower.json` file with:

        bower install --save [YOUR_PACKAGE_NAME]

## Easiest: Do nothing

When you deploy to App Engine flexible environment a Docker image is created for
you and your code is copied into the image. This first method relies on the
Docker image build step to make Bower dependencies available to your app. This
method is the easiest.

This method is simple:

1. Install Bower dependencies locally
1. Deploy

For example:

    cd my-app
    bower install
    gcloud app deploy

The Bower dependencies will be installed, and during the deployment the files
will be copied into the Docker image, and thus will be available to your
deployed app.

## Less easy: Use package.json

Let's say you _don't_ want locally installed Bower dependencies to be copied
into the Docker image. To make the dependencies available to your deployed app,
you can have the dependencies installed _inside_ the Docker image as it is
constructed.

1.  Run the following command to generate an `app.yaml file if you don't already
have one:

        gcloud app gen-config . --runtime=nodejs

1.  To prevent locally installed Bower dependencies from being copied into the
Docker image, add the following to `app.yaml`:

        # Prevents locally installed Bower dependencies
        # from being copied into the Docker image
        skip_files:
          - ^(.*/)?.*/bower_components/.*$

1.  If you're deploying a Node.js app then you almost certainly have a `package.json` file. Add the following to `package.json`:
        
        "scripts": {
          ...
          "postinstall": "bower install --config.interactive=false",
          ...
        },
        "dependencies": {
          ...
          "bower": "^1.7.9",
          ...
        }

    The ellipses hide other configurations that may exist in `package.json`.

1.  Now deploy:

        gcloud app deploy

    As the Docker image is built it will run `npm install`, which will in turn
    run `bower install`.

## Much less easy: Use a Dockerfile

Another method that does not rely on `package.json` is to use a custom
`Dockerfile`.

To make Docker install the Bower dependencies you need to use `runtime: custom`.
Here we assume you're deploying a Node.js app, but with a little extra
customization in the `Dockerfile` you can make this work for other languages.

1.  Run the following command to generate the necessary files:

        gcloud app gen-config . --custom --runtime=nodejs

    This generates three files: `Dockerfile`, `.dockerignore`, and `app.yaml`.

1.  To prevent locally installed Bower dependencies from being copied into the
Docker image. Add the following to `app.yaml`:

        # Prevents locally installed Bower dependencies
        # from being copied into the Docker image
        skip_files:
          - ^(.*/)?.*/bower_components/.*$

1.  Now edit `Dockerfile` and insert the following beneath `COPY ./app/`:

        npm i -g bower
        bower install --config.interactive=false

    So that is has:

        COPY ./app/
        npm i -g bower
        bower install --config.interactive=false

1.  Now deploy:

        gcloud app deploy

    As the Docker image is built it will run `bower install`.

