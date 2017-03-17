---
title: Using Yarn on App Engine
description: Learn how to use Yarn to manage dependencies for Node.js applications on Google App Engine flexible environment.
author: justinbeckwith
tags: App Engine, Yarn, Node.js, NPM
date_published: 2017-03-16
---

[Yarn](https://yarnpkg.com/) is a package management tool that makes it easy and fast to install [NPM](https://www.npmjs.com/) modules for [Node.js](https://nodejs.org).

You can use Yarn to manage your Node.js dependencies on App Engine flexible environment. This tutorials provides a quick demonstration.

## Getting started

1.  Install Yarn by following the [installation instructions](https://yarnpkg.com/en/docs/install).

1.  To install a package and automatically save it to your `package.json` run:

        yarn add PACKAGE

    For example, to install and save the `google-cloud` package:

        yarn add google-cloud

    Running this command will save the dependency into your `package.json`, and create a `yarn.lock` file in the current directory. Don't delete this file! It will track the exact version of every package you need to run your application. 

![yarn add google-cloud](https://storage.googleapis.com/gcp-community/tutorials/appengine-yarn/yarnAdd.gif)

## Deploying to App Engine

To use Yarn for your deployments to App Engine flexible environment, all you need is a `yarn.lock` in your application directory. Then, just deploy:

    gcloud app deploy

If App Engine finds a `yarn.lock` in the application directory, Yarn will be used to perform the npm installation.  

![gcloud app deploy](https://storage.googleapis.com/gcp-community/tutorials/appengine-yarn/appDeploy.gif)

And that's it! If you have any other questions about Node.js on Google Cloud Platform, be sure to [join us](https://gcp-slack.appspot.com) on our [Slack channel](https://googlecloud-community.slack.com/messages/nodejs/).
