---
title: Deploy React and Nginx to Google Cloud Run
description: Learn how to integrate a front-end app that runs on a customized runtime, with Google Cloud Run.
author: Felipe Lujan
tags: Cloud Run, React, Front-end, NGinx
date_published: 2020-01-01
---

#Deploy React and Nginx to Google Cloud Run.

In this tutorial you'll learn how to run a Create-React-App (CRA) with Nginx and deploy it to Google Cloud Run.
Although other services in Google Cloud Platform can easily serve similar web applications, Google Cloud Run is a good option in cases where some customization is needed to the underlying runtime.

## Before you begin.
You'll need
1.  A project created in the Google Cloud Console with billing enabled.
1.  The Google Cloud SDK and GIT installed on your computer.
1.  A code editor installed on your computer.

Basic understanding of single page applications(SPA) is also desired. 

##Obtaining the React code base

Clone the pre-configured React App to your computer by running the following command.

    git clone https://github.com/GoogleCloudPlatform/community

Open open the file ``tutorials/deploy-react-nginx-cloud-run/src/App.js`` with your preferred code editor. Notice the use of react-router-dom to create 3 routes ``/``, ``/users``, ``/about``,  and some links to browse between them.

## Enable the necessary APIs in the Google Cloud Platform Console
Log in to the Google Cloud Platform Console and open the navigation menu, located in the top left portion of the page. 
Click **API & Services > Library**  search for and enable the following APIs:
* Cloud Run API
* Google Container Registry API
* Cloud Build API



## Runtime configuration

Create a file in the root of the project named ``nginx.conf`` and add the following configuration:

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
    
  By creating this file you'll provided the **$PORT** environment variable, Google Cloud Run expects your application to listen on it. 
  
  Additionally you're customizing Nginx so the react-router-dom always respond with the proper route, as well as implementing Gzip compression, which will make the web application lightweight and fast. 

 
 ## Build a docker image
  Create a file named `Dockerfile` in the root folder of the project and paste the following content.
 
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
    
 This configuration defines 2 environments, one in which the web application is build and a second one where its going to run.
 Note that in the server environment
 
 ## Upload and deploy.
 Open the Google Cloud SDK and change the working directory to the root of your project. Type ``cd`` followed by its route. For example:
  
      cd C:\tutorials\react-cloud-run\
  
   **Note:** Make sure you have logged in and selected a working project in the Google Cloud SDK, more information  [in this link](https://cloud.google.com/sdk/gcloud/reference/config/set "Gcloud config set").
 
 ###Building the Docker container
 
  
  Run the following command to submit all the code and have your container built by the Google Cloud Platform Cloud Build API. Dont forget to replace the id of your project.
  
     gcloud build submit --tag gcr.io/ID_OF_YOUR_PROJECT/cra-cloud-run
     
  After a couple of minutes a new image containing will be in the container registry in your Google Cloud Platform project. Check it out in the Google Cloud Console by clicking in the navigation menu and clicking **Container Registry > Images**
     
     
  ### Deploying to Google Cloud Run
  
  Run the following command
  
      gcloud  beta run deploy --image gcr.io/ID_OF_YOUR_PROJECT/cra-cloud-run --platform managed 
   
   When asked, select a zone, give the service a name and allow unauthenticated invocations.
   Once it's finished, browse to the URL provided in the Google Cloud SDK command line.
   You'll see the latest version of ``cra-cloud-run`` deployed to Google Cloud Run.
     
