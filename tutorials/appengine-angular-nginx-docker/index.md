---
title: App Engine with angular, nginx, docker and cloud build
description: Learn how to deploy a sample angular application to App Engine using nginx and docker with cloud build.
author: livesankp
tags: App Engine, Docker, nginx, angular
date_published: 2021-03-16
---

# App Engine multi environment deployment using angular, nginx, docker, cloud build in custom flex env

## Introduction

This tutorial shows you how to deploy a sample angular application to App Engine using the `gcloud` command for builds and app engine.

![image](https://user-images.githubusercontent.com/13769236/111506916-1f5bb200-8718-11eb-8600-71449f0af5e9.png)

## Assumptions

You have google cloud project created. You have enabled app engine, cloud builds, container registry apis.

## Steps

Here are the steps you will be taking.

*   **Create an angular project using angular quick start**

    How to create and setup angular project using angular-cli

*   **Build and run your sample app**

    You'll learn how to build and containerize your app using Cloud SDK. At the end, you'll deploy your app to the web using the `gcloud`
    command.

*   **After the tutorial...**

    Your app will be real and you'll be able to experiment with it after you
    deploy, or you can remove it and start fresh.

## Angular Project setup

* Follow this page to create a sample angular application https://angular.io/guide/setup-local
* Once you have a project created and verify that it's working on http://localhost:4200 as per above guide
* We are also going to learn, how to use environment variable of app engine to use dynamic API urls in UI application. For that follow below steps
  - Under src/assets folder add env.js and env.template.js files
  - Copy this content in env.js
  
    ```
    (function(window) {
          window["env"] = window["env"] || {};

          // Environment variables
          window["env"]["apiurl"] = "http://localhost:8080/api";
    })(this);
    ```
   - Copy this content in env.template.js
   
     ```
     (function(window) {
           window.env = window.env || {};

           // Environment variables
           window["env"]["apiurl"] = "${API_URL}";           
     })(this);
     ```
   - Add reference of env.js file in index.html
   - Remove `/` from index.html <base href="">. This will be useful when you want to use dispatch.yaml later.
* Update environment.ts with this.

     ```
     export const environment = {
          production: false,
          webapiurl: (window as any)["env"]["apiurl"] || "default"                   
     };
     ```
* For testing whether API_URL working or not add usage of this environment.webapiurl anywhere in the application. For example I have added that in app.componennt.html and         app.component.ts

     ```
     <span>webapiurl : {{ webapiurl }}</span>
     ```
     
     ```  
     export class AppComponent {
           title = 'sample-app';
           webapiurl = environment.webapiurl;
     }
     ```
* Update outputPath in build section of angular.json with `"outputPath": "dist"`
* Now build your angular project again and verify you are able to see the webapiurl as http://localhost:8080/api when you open the app in browser. If everything is       working well then you can go to next step of doing the cloud build.
     
## Cloud Build
* Assumption is you know basics of docker, gcloud sdk, cloud builds and app engine. If not please refer following documentations.
  https://docs.docker.com/engine/reference/commandline/run/
  https://cloud.google.com/sdk/docs
  https://cloud.google.com/build/docs
  https://cloud.google.com/appengine
* There could be many ways of doing cloud build for any application. For simplicity of this tutorial we will use just output `dist` folder of sample app.
* Add `Dockerfile, cloudbuild.yaml, app.yaml and nginx` files under `dist` folder and copy the following contents.
  - Dockerfile 
  
    ```
    # The standard nginx container just runs nginx. The configuration file added
    # below will be used by nginx.
    FROM nginx

    # Copy the nginx configuration file. This sets up the behavior of nginx, most
    # importantly, it ensure nginx listens on port 8080. Google App Engine expects
    # the runtime to respond to HTTP requests at port 8080.
    COPY nginx.conf /etc/nginx/nginx.conf

    # create log dir configured in nginx.conf
    RUN mkdir -p /var/log/app_engine

    # Create a simple file to handle heath checks. Health checking can be disabled
    # in app.yaml, but is highly recommended. Google App Engine will send an HTTP
    # request to /_ah/health and any 2xx or 404 response is considered healthy.
    # Because 404 responses are considered healthy, this could actually be left
    # out as nginx will return 404 if the file isn't found. However, it is better
    # to be explicit.
    RUN mkdir -p /usr/share/nginx/www/_ah && \
        echo "healthy" > /usr/share/nginx/www/_ah/health

    # Finally, all static assets.
    ADD dist/ /usr/share/nginx/www/sampleapp

    CMD ["/bin/sh",  "-c",  "envsubst < /usr/share/nginx/www/sampleapp/assets/env.template.js > /usr/share/nginx/www/sampleapp/assets/env.js && exec nginx -g 'daemon off;'"]
    ```
  - nginx
  
    ```
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
    ```
  - cloudbuld.yaml
  
    ```
    steps:
    - name: 'gcr.io/cloud-builders/docker'
      args: ['build', '-t', 'us.gcr.io/$PROJECT_ID/angular-nginx-container', '.']
    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'us.gcr.io/$PROJECT_ID/angular-nginx-container']
    images: ['us.gcr.io/$PROJECT_ID/angular-nginx-container']
    ```
  - app.yaml
  
    ```
    runtime: custom
    env: flex
    service: angular-ui-dev
    threadsafe: true

    env_variables:
      API_URL: "https://webapi-dev.appname.com"
    ```
* At this point you can just use docker commands if you want to verify on your local docker. To do that run following two commands on dist folder and verify on      http://localhost:8080, if everything works. To make this work you have to comment out `listen 8080;` from nginx.

  ```
  docker build -t sampleapp .
  docker run --env API_URL="https://webapi-dev.appname.com" -dp 8080:80 sampleapp
  ```
* You can directly use above four files to deploy your app in app engine using gcloud sdk. For that run following commands
  - `gcloud builds submit` This will create the docker image on the specified path in cloudbuild.yaml file. Once done verify you have a container image created at https://console.cloud.google.com/gcr/images/yourprojectid?project=yourprojectid
  - `gcloud app deploy --image-url us.gcr.io/yourprojectid/angular-nginx-container` This will deploy your image to app engine with the service name you have provided in app.yaml.
* Your UI will looks like this once you access it using version url of the service.
![image](https://user-images.githubusercontent.com/13769236/111413008-724b5000-86ab-11eb-9b9f-5845b11d0e5a.png)
* After following this tutorial you will be able to deploy angular ui in app engine using cloud build, nginx and docker. Using this you can have dynamic api urls or configuration directly defined in app.yaml so you can use same docker image and deploy it in different environments like dev, testing, staging or prod. All you have to do is have separate app.yaml per environment. 
* This can be easily integrated in GitLab CI/CD pipelines as separated build steps of `build (angular ui using ng build)`, `publish (using cloud build)` and `deploy (using gcloud app deploy)`
