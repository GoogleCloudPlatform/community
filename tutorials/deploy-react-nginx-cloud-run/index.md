---
title: Deploy React and Nginx to Cloud Run
description: Learn how to integrate a front-end app that runs on a customized runtime, with Cloud Run.
author: FelipeLujan
tags: Cloud Run, React, Front-end, NGinx
date_published: 2020-01-01
---

In this tutorial, you'll learn how to run a Create React App (CRA) with Nginx and deploy it to Cloud Run. Although other 
services in Google Cloud can easily serve similar web applications, Cloud Run is a good option in cases where some
customization is needed to the underlying runtime.

## Before you begin

Before you begin this tutorial, you'll need the following:

* A Google Cloud project with billing enabled. You can use an existing project or
  [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) for this tutorial. 
* The [Google Cloud SDK](https://cloud.google.com/sdk/install) installed on your computer.
* [Git](https://git-scm.com/downloads) installed on your computer.
* A code editor installed on your computer.

This tutorial presumes a basic understanding of single-page applications (SPAs). 

## Get the React code

1.  Clone the GitHub repository for this tutorial by running the following command:

        git clone https://github.com/GoogleCloudPlatform/community
        
1.  Open the pre-configured React app file `tutorials/deploy-react-nginx-cloud-run/src/App.js` with your preferred
    code editor.

    Notice the use of `react-router-dom` to create three routes (`/`, `/users`, and `/about`) and some links to browse
    between them.

## Enable the necessary APIs in the Cloud Console

1.  Go to the [**API Library**](http://console.cloud.google.com/apis/library) page in the Cloud Console.
1.  Search for and enable the following APIs:

    * Cloud Run API
    * Google Container Registry API
    * Cloud Build API

## Runtime configuration

Create a file in the root of the project named `nginx.conf` and add the following configuration:

    server {
         listen       $PORT;
         server_name  localhost;
         
         location / {
             root   /usr/share/nginx/html;
             index  index.html index.htm;
             try_files $uri /index.html;
         }
         
         gzip on;
         gzip_vary on;
         gzip_min_length 10240;
         gzip_proxied expired no-cache no-store private auth;
         gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml;
         gzip_disable "MSIE [1-6]\.";
         
    }
    
By creating this file, you provide the `$PORT` environment variable that Cloud Run expects your application to listen on. 
  
This file customizes Nginx so that `react-router-dom` always responds with the proper route. This configuarion enables gzip
compression, which makes the web application lightweight and fast. 

## Build a Docker image

Create a file named `Dockerfile` in the root folder of the project and paste the following content:
 
    # build environment
    FROM node:8-alpine as react-build
    WORKDIR /app
    COPY . ./
    RUN yarn
    RUN yarn build
    
    # server environment
    FROM nginx:alpine
    COPY nginx.conf /etc/nginx/conf.d/configfile.template
    ENV PORT 8080
    ENV HOST 0.0.0.0
    RUN sh -c "envsubst '\$PORT'  < /etc/nginx/conf.d/configfile.template > /etc/nginx/conf.d/default.conf"
    COPY --from=react-build /app/build /usr/share/nginx/html
    EXPOSE 8080
    CMD ["nginx", "-g", "daemon off;"]
    
This configuration defines two environments: one where the web application is built and one where the web application 
will run.
 
## Upload and deploy

Open the Google Cloud SDK and change the working directory to the root of your project. For example:
  
    cd C:\tutorials\react-cloud-run\
  
**Note:** Make sure that you have logged in and selected a working project in the Google Cloud SDK. For more information,
see, [this page](https://cloud.google.com/sdk/gcloud/reference/config/set).
 
### Build the Docker container

Run the following command to submit all of the code and have your container built by the Cloud Build API. Replace 
`[YOUR_PROJECT_ID]` with your
[project ID](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects).
  
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/cra-cloud-run
     
After a couple of minutes, a new image will be in the container registry in your Google Cloud project. To see it, go to the 
[**Container Registry > Images**](http://console.cloud.google.com/gcr/images) page in the Cloud Console.

### Deploy to Cloud Run
  
Run the following command:

    gcloud  beta run deploy --image gcr.io/ID_OF_YOUR_PROJECT/cra-cloud-run --platform managed 

When asked, select a zone, give the service a name, and allow unauthenticated invocations. After the deployment is complete, 
go to the URL provided in the Google Cloud SDK command line. You'll see the latest version of `cra-cloud-run` deployed to 
Cloud Run.

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete
the project that you created for the tutorial.

1.  In the Cloud Console, go to the [**Projects** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
