---
title: Using Yarn on App Engine
description: Learn how to use Yarn to manage dependencies for Node.js applications on App Engine flexible environment.
author: justinbeckwith
tags: App Engine, Yarn, Node.js, npm
date_published: 2017-03-16
---

Justin Beckwith | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Yarn](https://yarnpkg.com/) is a package management tool that makes it easy and fast to install [npm](https://www.npmjs.com/) modules for
[Node.js](https://nodejs.org).

You can use Yarn to manage your Node.js dependencies on App Engine flexible environment. This tutorials provides a quick demonstration.

## Objectives

1.  Install Yarn.
1.  Manage Node.js dependencies with Yarn.
1.  Use Yarn to install dependencies during deployment to App Engine.

## Costs

This tutorial uses billable components of Google Cloud, including:

- App Engine flexible environment

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Cloud Console][console].
1.  Enable billing for your project.
1.  Install the [Cloud SDK][cloud-sdk].

[console]: https://console.cloud.google.com/
[cloud-sdk]: https://cloud.google.com/sdk/

## Getting started

1.  Install Yarn by following the [installation instructions](https://yarnpkg.com/en/docs/install).

1.  To install a package and automatically save it to your `package.json` run:

        yarn add PACKAGE

    For example, to install and save the `google-cloud` package:

        yarn add google-cloud

    Running this command will save the dependency into your `package.json`, and
    create a `yarn.lock` file in the current directory. Don't delete this file!
    It will track the exact version of every package you need to run your
    application.

![yarn add google-cloud](https://storage.googleapis.com/gcp-community/tutorials/appengine-yarn/yarnAdd.gif)

## Deploying to App Engine

To use Yarn for your deployments to App Engine flexible environment, all you
need is a `yarn.lock` in your application directory. Then, just deploy:

    gcloud app deploy

If App Engine finds a `yarn.lock` in the application directory, Yarn will be
used to perform the npm installation. Learn more about the [Node.js runtime for App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/nodejs/runtime).

![gcloud app deploy](https://storage.googleapis.com/gcp-community/tutorials/appengine-yarn/appDeploy.gif)

And that's it!
