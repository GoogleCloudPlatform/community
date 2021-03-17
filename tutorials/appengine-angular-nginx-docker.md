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
* Once you have a project created and verified that it's working on localhost
* Here we are also going to learn how to use environment variable of app engine to use dynamic API urls in UI application. For that follow below steps
  - Under src/assets folder add env.js and env.template.js files
  - Copy this content in env.js
    ```
    (function(window) {
          window["env"] = window["env"] || {};

          // Environment variables
          window["env"]["apiurl"] = "https://localhost";
    })(this);
    ```
   - Similar way copy this content in env.template.js
     ```
     (function(window) {
           window.env = window.env || {};

           // Environment variables
           window["env"]["apiurl"] = "${API_URL}";           
     })(this);
     ```
   - Add reference of env.js file in index.html
   - Remove `/` from index.html <base href="">. This will be useful when you want to use dispatch.yaml later.
   - Update environment.ts with this
     ```
     export const environment = {
          production: false,
          webapiurl: (window as any)["env"]["apiurl"] || "default"                   
     };
     ```
    - For testing whether API_URL working or not add usage of this environment.webapiurl anywhere in the application. For example I have added that in app.componennt.html and         app.component.ts
      ```
       <span>webapiurl : {{ webapiurl }}</span>
       
       export class AppComponent {
           title = 'sample-app';
           webapiurl = environment.webapiurl;
       }
       ```

## Cloud Build
