---
title: App Engine deployment with Angular, Nginx, Docker, and Cloud Build
description: Learn how to deploy a sample Angular application to App Engine using Nginx and Docker with Cloud Build.
author: livesankp
tags: App Engine, Docker, nginx, angular
date_published: 2021-04-05
---

Sandeep Parmar

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows you how to deploy a sample Angular application to App Engine using the `gcloud` command-line tool.

After following this tutorial, you will be able to deploy an Angular user interface in App Engine using Cloud Build, Nginx, and Docker. Using this technique, you
can have dynamic API URLs or configuration directly defined in an `app.yaml` file so that you can use the same Docker image and deploy it in different 
environments like development, testing, staging, and production. All that you have to do is have a separate `app.yaml` file for each environment.

This technique can be integrated into GitLab CI/CD pipelines as separated build steps of build (Angular UI using `ng build`), publish (using Cloud Build),
and deploy (using `gcloud app deploy`).

![flow-diagram](https://storage.googleapis.com/gcp-community/tutorials/appengine-angular-nginx-docker/flow-diagram.png)

This tutorial assumes that you know the basics of the following products and services:

  - [App Engine](https://cloud.google.com/appengine/docs)
  - [Cloud Build](https://cloud.google.com/build/docs)
  - [`gcloud`](https://cloud.google.com/sdk/docs)
  - [Docker](https://docs.docker.com/engine/reference/commandline/run)
  - [Nginx](https://docs.nginx.com/nginx/admin-guide/web-server/web-server)

## Objectives

*   Create and set up an Angular project using the [Angular CLI](https://cli.angular.io/).
*   Build and containerize your app using the [Cloud SDK](https://cloud.google.com/sdk).
*   Deploy your app to the web using the [`gcloud` command-line tool](https://cloud.google.com/sdk/gcloud).

## Before you begin

1.  Select or create a Google Cloud project.

    [Go to the **Manage resources** page.](https://console.cloud.google.com/cloud-resource-manager)

1.  Enable the App Engine, Cloud Build, and Container Registry APIs. For details, see
    [Enabling APIs](https://cloud.google.com/apis/docs/getting-started#enabling_apis).

## Angular project and App Engine environment variable setup

In this section, you create a sample Angular application and use App Engine environment variables to use dynamic API URLs in for your application interface.

You can see the sample code in
[this tutorial's GitHub repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-angular-nginx-docker/).

1.  Follow these instructions to create a sample Angular application: [Setting up the local environment and workspace](https://angular.io/guide/setup-local).
1.  Verify that that the sample Angular application is working by going to `http://localhost:4200`.
1.  In the `src/assets` folder, add `envconfig.js` and `envconfig.template.js` files.
1.  Copy the following code into the `envconfig.js` file:

        (function(window) {
              window["envconfig"] = window["envconfig"] || {};

              // Environment variables
              window["envconfig"]["apiurl"] = "http://localhost:8080/api";
        })(this);

1.  Copy the following code into the `envconfig.template.js` file:

        (function(window) {
              window.envconfig = window.envconfig || {};

              // Environment variables
              window["envconfig"]["apiurl"] = "${API_URL}";           
        })(this);

1.  Add a reference to the `envconfig.js` file in `index.html`.
1.  Remove `/` from `<base href="">` in the `index.html` file. This will be useful when you want to use `dispatch.yaml` later.
1.  Update the `environment.ts` file with this code:

        export const environment = {
             production: false,
             webapiurl: (window as any)["envconfig"]["apiurl"] || "default"                   
        };

1.  For testing whether `API_URL` is working or not, add usage of this `environment.webapiurl` anywhere in the application. 

    For example, you can add it as shown in the sample code in
    [`app.component.html`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-angular-nginx-docker/sample-app/src/app/app.component.html)
    and [`app.component.ts`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-angular-nginx-docker/sample-app/src/app/app.component.ts).

1.  Update `outputPath` in the build section of the `angular.json` file with `"outputPath": "dist"`.

1.  Build your Angular project again and verify that you are able to see the `webapiurl` value as `http://localhost:8080/api` when you open the app in a browser.

    If everything is working, then you can go to the next steps using Cloud Build.
     
## Cloud Build

There are many ways of using Cloud Build for any application. For simplicity, this tutorial uses the `dist` folder of the sample app for output.

1.  Create an `nginx-hosting` folder and copy the `dist` folder into it.
1.  Add a `Dockerfile` file in the `nginx-hosting` folder, and copy the following code into the file:
  
        # The standard nginx container just runs nginx. The configuration file added
        # below will be used by nginx.
        FROM nginx

        # Copy the nginx configuration file. This sets up the behavior of nginx. Most
        # important, it ensures that nginx listens on port 8080. Google App Engine expects
        # the runtime to respond to HTTP requests at port 8080.
        COPY nginx.conf /etc/nginx/nginx.conf

        # create log dir configured in nginx.conf
        RUN mkdir -p /var/log/app_engine

        # Create a simple file to handle health checks. Health checking can be disabled
        # in app.yaml, but is highly recommended. Google App Engine will send an HTTP
        # request to /_ah/health and any 2xx or 404 response is considered healthy.
        # Because 404 responses are considered healthy, this could actually be left
        # out as nginx will return 404 if the file isn't found. However, it is better
        # to be explicit.
        RUN mkdir -p /usr/share/nginx/www/_ah && \
            echo "healthy" > /usr/share/nginx/www/_ah/health

        # Finally, all static assets.
        ADD dist/ /usr/share/nginx/www/sampleapp

        CMD ["/bin/sh",  "-c",  "envsubst < /usr/share/nginx/www/sampleapp/assets/envconfig.template.js > /usr/share/nginx/www/sampleapp/assets/envconfig.js && exec nginx -g 'daemon off;'"]

1.  Add an `nginx.conf` file in the `nginx-hosting` folder, and copy the following code into the file:

        events {
           worker_connections 768;
        }

        http {
            sendfile on;
            tcp_nopush on;
            tcp_nodelay on;
            keepalive_timeout 65;
            types_hash_max_size 2048;
            include /etc/nginx/mime.types;
            default_type application/octet-stream;

            # Logs will appear on the Google Developer's Console when logged to this
            # directory.
            access_log /var/log/app_engine/app.log;
            error_log /var/log/app_engine/app.log;

            gzip on;
            gzip_disable "msie6";

            server {
                # Google App Engine expects the runtime to serve HTTP traffic from port 8080.
                listen 8080;  

                # Root directory and index files
                index index.html index.htm;

                location / {
                    root /usr/share/nginx/www/sampleapp;
                }

    	        location /sampleapp/ {
   	            root /usr/share/nginx/www;
                }
            }
        }

1.  Add a `cloudbuild.yaml` file in the `nginx-hosting` folder, and copy the following code into the file:
  
        steps:
        - name: 'gcr.io/cloud-builders/docker'
          args: ['build', '-t', 'us.gcr.io/$PROJECT_ID/angular-nginx-container', '.']
        - name: 'gcr.io/cloud-builders/docker'
          args: ['push', 'us.gcr.io/$PROJECT_ID/angular-nginx-container']
        images: ['us.gcr.io/$PROJECT_ID/angular-nginx-container']

1.  Add an `app.yaml` file in the `nginx-hosting` folder, and copy the following code into the file:

        runtime: custom
        env: flex
        service: angular-ui-dev
        threadsafe: true

        env_variables:
          API_URL: "https://webapi-dev.appname.com"

1.  If you want to verify the setup in your local Docker environment, you can do so with the following two commands on the `nginx-hosting` folder.
    (To make this work you have to comment out `listen 8080;` in the `nginx` file.)

        docker build -t sampleapp .
        docker run --env API_URL="https://webapi-dev.appname.com" -dp 8080:80 sampleapp

     Verify on `http://localhost:8080` that everything works.
     
1.  You can directly use the above four files to deploy your app in App Engine using the `gcloud` command-line tool. To do so, run the following commands:

    1.  Create the Docker image on the specified path in the `cloudbuild.yaml` file.

            gcloud builds submit
	    
        After this command, verify that you have a container image created at `https://console.cloud.google.com/gcr/images/yourprojectid?project=yourprojectid`.

    1.  Deploy your image to App Engine with the service name that you provided in the `app.yaml` file:

            gcloud app deploy --image-url us.gcr.io/yourprojectid/angular-nginx-container
     
1.  Verify that the `webapiurl` matches what you provided in the environment variable as shown in the flow diagram at the beginning of this tutorial.

## App Engine dispatch

You can extend the solution for [`dispatch.yaml`](https://cloud.google.com/appengine/docs/standard/python/reference/dispatch-yaml). This deployment using nginx
supports additional locations so that when you use `dispatch` as shown in the following example, you should be able to access your application using the root URL
of your project. To make this work, you have to update the `nginx` location with your service name as a location `angular-ui-dev` and you should be able to 
access your application using the `https://your-project-id.uc.r.appspot.com/angular-dev-ui/` URL.

      dispatch:
      # Default service serves simple hostname request.
      - url: "your-project-id.uc.r.appspot.com/"
        service: default
  
      # Dispatch UI
      - url: "*/angular-ui-dev/*"
        service: angular-ui-dev
