---
title: How to Prepare a Node.js Development Environment
description: Learn how to prepare your computer for Node.js development, including development on Google Cloud Platform.
author: jmdobry
tags: Node.js
date_published: 12/14/2016
---
This tutorial shows how to prepare your computer for [Node.js][nodejs]
development, including development on Google Cloud Platform. Follow this
tutorial to install Node.js and relevant tools.

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Objectives

* Install Node Version Manager (NVM)
* Install Node.js and NPM
* (Optional) install Yarn
* Install an editor
* Install the Google Cloud SDK
* Install the Google Cloud Client Library for Node.js
* Install other useful tools

## Install Node Version Manager (NVM)

[Node Version Manager][nvm] (NVM) is a simple bash script for managing installations
of Node.js and NPM. NVM does not support Windows, check out
[nvm-windows][nvm-windows] for managing your Node.js installation on Windows.

Installing NVM is simple, check out the [installation instructions][nvm-install]
for details on installing NVM on your platform.

## Install Node.js and NPM

Once NVM is installed you can install Node.js and NPM. To install Node.js the
latest stable version of Node.js you would run:

    nvm install stable

To it the default version run the following:

    nvm alias default stable

You can check what version of Node.js you're running with:

    node -v

NPM is the Node Package Manager for Node.js should have been installed alongside
Node.js. You use NPM to install Node.js packages from the NPM repository, for
example:

    npm install --save express

For additional reading, read [Run Express.js on Google Cloud Platform][express].

## (Optional) install Yarn

[Yarn][yarn] is an alternative Node.js package manager that boasts faster
install times and reliably reproducible builds. Install Yarn is simple, check
out the [installation instructions][yarn-install] for details on installing Yarn
on your platform.

The following command uses Yarn to install the `express` package:

    yarn add express

Yarn automatically updates your `package.json` file and produces a `yarn.lock`
(a list of installed dependencies and transitive dependencies) file which should
be committed to version control.

## Install an editor

Popular editors (in no particular order) used to develop Node.js applications
include, but are not limited to:

* [Sublime Text][subl] by Jon Skinner
* [Atom][atom] by GitHub
* [Visual Studio Code][vscode] by Microsoft
* [IntelliJ IDEA and/or Webstorm][intellij] by JetBrains

These editors (sometimes with the help of plugins) give you everything from
syntax highlighting, intelli-sense, and code completion to fully integrated
debugging capabilities, maximizing your Node.js development efficacy.

## Install the Google Cloud SDK

The [Google Cloud SDK][sdk] is a set of tools for Cloud Platform. It contains
`gcloud`, `gsutil`, and `bq`, which you can use to access Google Compute Engine,
Google Cloud Storage, Google BigQuery, and other products and services from the
command-line. You can run these tools interactively or in your automated
scripts.

As an example, here is a simple command that will deploy any Node.js web
application to Google App Engine flexible environment (after deployment it App
Engine attempt to start the application with `npm start`):

    gcloud app deploy

## Install the Google Cloud Client Library for Node.js

The [Google Cloud Client Library for Node.js][gcloud-node] is the idiomatic way
for Node.js developers to integrate with Google Cloud Platform services, like
Cloud Datastore and Cloud Storage. You can install the entire suite of libraries
with:

    npm install google-cloud

or you can install the package for an individual API, like Cloud Storage for
example:

    npm install @google-cloud/storage

### Authentication

During local development, your Node.js application must authenticate itself in
order to interact Google Cloud Platform APIs. The easiest way to get started is
to run the following command after installing the Google Cloud SDK:

    gcloud beta auth application-default login

This is save credentials to your machine that the Cloud Client Library will
automatically use to authenticate. Read more about [authentication][auth],
including how authentication is handled once your application is deployed.

You'll also want to tell the Cloud Client Library which Google Platform Project
to use. You do this by setting the `GCLOUD_PROJECT` environment variable to your
project ID, or by passing a `projectId` option to the library in your code.

## Install other useful tools

For a comprehensive list of amazing Node.js tools and libraries, check out the
curated [Awesome Node.js list][awesome].

[nodejs]: https://nodejs.org/
[nodejs-gcp]: running-nodejs-on-google-cloud
[nvm]: https://github.com/creationix/nvm
[nvm-windows]: https://github.com/coreybutler/nvm-windows
[nvm-install]: https://github.com/creationix/nvm#installation
[express]: run-expressjs-on-google-app-engine
[yarn]: https://yarnpkg.com/
[yarn-install]: https://yarnpkg.com/en/docs/install
[subl]: https://www.sublimetext.com/
[atom]: https://atom.io/
[vscode]: https://code.visualstudio.com/
[intellij]: https://www.jetbrains.com/idea/
[sdk]: https://cloud.google.com/sdk/
[gcloud-node]: https://googlecloudplatform.github.io/google-cloud-node/#/
[auth]: https://cloud.google.com/docs/authentication#getting_credentials_for_server-centric_flow
[awesome]: https://github.com/sindresorhus/awesome-nodejs
