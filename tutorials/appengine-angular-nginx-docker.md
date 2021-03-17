---
title: App Engine with angular, nginx, docker
description: Learn how to deploy a sample angular application to App Engine using nginx docker container with just one cloud build.
author: Sandeep Parmar
tags: App Engine
date_published: 2021-03-16
---

# App Engine quickstart using angular, nginx, docker, cloud build in custom flex environment

## Introduction

This tutorial shows you how to deploy a sample angular application to App Engine using the `gcloud` command.

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
* Once you have a project created and verify that it's working on localhost:4200 as per above guide
* Here we are also going to learn how to use environment variable of app engine to use dynamic API urls in UI application. For that follow below steps
  - Under src/assets folder add env.js and env.template.js files
  - Copy this content in env.js
    ```
    (function(window) {
          window["env"] = window["env"] || {};

          // Environment variables
          window["env"]["apiurl"] = "http://localhost";
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
       
       export class AppComponent {
           title = 'sample-app';
           webapiurl = environment.webapiurl;
       }
       ```
* Update outputPath in build section of angular.json with `"outputPath": "dist"`
* Now build your angular project again and verify you are able to see the http://localhost when you open the app in browser. If everything is working well then you can go      to next step of doing the cloud build.
     
## Cloud Build
* Assumption is you know basics of docker, gcloud sdk, cloud builds and app engine. If not please refer https://docs.docker.com/engine/reference/commandline/run/, https://cloud.google.com/sdk/docs, https://cloud.google.com/build/docs and https://cloud.google.com/appengine
* There could be many ways of doing cloud build for any application. For simplicity of this tutorial we will use just output `dist` folder of sample app
* Add `Dockerfile, cloudbuild.yaml, app.yaml and nginx` files under dist folder and copy the following contents
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
    
* 
