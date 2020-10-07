---
title: Webpack on App Engine flexible environment
description: Learn how to bundle frontend assets for an Express.js app in the Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Express.js, Node.js, Webpack
date_published: 2017-02-16
---

This tutorial shows a sample Node.js app built with [Express.js][express] that
uses Webpack to bundle frontend assets on deployment to the App Engine
flexible environment.

[Webpack][webpack] is a module bundler. Webpack takes modules with dependencies
and generates static assets representing those modules.

This tutorial gets you going fast by deploying a simple Webpack.js app. This
tutorial assumes that you are familiar with Node.js programming and that you
have installed Node.js.

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

[express]: http://expressjs.com
[webpack]: https://webpack.github.io/
[nodejs-gcp]: running-nodejs-on-google-cloud

## Objectives

1. Create a Node.js app that uses Webpack to bundle the app's frontend assets.
1. Run the Node.js app locally.
1. Deploy the Node.js app to App Engine flexible environment.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- App Engine flexible environment

Use the [pricing calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  Enable billing for your project.
1.  Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Preparing the app

1.  Download the sample [`server.js`][server] file.
1.  Prepare the `package.json` file:

    1.  Create a `package.json` file with `npm`:

            npm init

    1.  Install dependencies with `npm`:

            npm install --save webpack express pug

        Webpack must be listed in the `dependencies` of the `package.json`
        file because by default `devDependencies` are not installed when the app is
        deployed to App Engine.

    1.  Add the following `scripts` section to the `package.json` file:

            "scripts": {
              "bundle": "webpack --config webpack.config.js",
              "prestart": "npm run bundle"
            }

        The `bundle` script will run Webpack and bundle the app's frontend
        assets. The `prestart` script is automatically executed before the `start`
        script. Note that the default `start` script is `node server.js`.

        Make sure that your `package.json` file is valid JSON.

1.  Create a `webpack.config.js` file with the following contents:

        'use strict';

        module.exports = {
          entry: './public/app.js',
          output: {
            filename: './dist/bundle.js'
          }
        };

    The bundled assets will be placed in a directory named `dist`.

1.  Prepare the frontend assets:

    1.  Create a new directory named `public`:

            mkdir public

    1.  Create a file in the `public` directory named `app.js` with the
        following contents:

            'use strict';

            import foo from './foo';

            document.getElementById('module-name').innerText = foo.name;

    1.  Create a file in the `public` directory named `foo.js` with the
        following contents:

            'use strict';

            export default {
              name: 'foo'
            };

    `app.js` imports and uses `foo.js`, but these files will be bundled and deployed as
    one file.

1.  Prepare the app's views:

    1.  Create a new directory named `views`:

            mkdir views

    1.  Download the sample [`index.pug`][index] file into the `views` directory.

At this point your directory structure should look like this:

* `public/`
  * `app.js`
  * `foo.js`
* `views/`
  * `index.pug`
* `package.json`
* `server.js`
* `webpack.config.js`

## Running the app

1.  Start the app with `npm`:

        npm start

    The `prestart` and `bundle` scripts will be executed automatically, bundling
    the frontend assets before the app starts.

1.  Visit [http://localhost:8080](http://localhost:8080) to see the running app.

1.  Press Control+C to stop the app.

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

        runtime: nodejs
        env: flex

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://[YOUR_PROJECT_ID].appspot.com` to see the deployed app.

    Replace `[YOUR_PROJECT_ID]` with your Google Cloud project ID.

[server]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-nodejs-webpack/server.js
[index]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-nodejs-webpack/views/index.pug
