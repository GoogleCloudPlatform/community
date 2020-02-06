---
title: App Engine quickstart using Python
description: Learn how to deploy a Python sample app to App Engine.
author: jscud
tags: App Engine
date_published: 2019-03-22
---

# App Engine quickstart using Python

<!-- {% setvar repo_url "https://github.com/GoogleCloudPlatform/python-docs-samples" %} -->
<!-- {% setvar repo_dir "python-docs-samples/appengine/standard_python37/hello_world" %} -->

<!-- {% setvar project_gae_url "<your-project>.appspot.com" %} -->

<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=python_gae_quickstart)

</walkthrough-alt>

## Introduction

This tutorial shows you how to deploy a sample [Python](https://python.org/)
application to App Engine using the `gcloud` command.

Here are the steps you will be taking.

*   **Create a project**

    Projects bundle code, VMs, and other resources together for easier
    development and monitoring.

*   **Build and run your "Hello World!" app**

    You will learn how to run your app using Cloud Shell, right in your
    browser. At the end, you'll deploy your app to the web using the `gcloud`
    command.

*   **After the tutorial...**

    Your app will be real and you'll be able to experiment with it after you
    deploy, or you can remove it and start fresh.

["Python" and the Python logos are trademarks or registered trademarks of the
Python Software Foundation.](walkthrough://footnote)

## Project setup

GCP organizes resources into projects, which collect all of the related resources for a single
application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-devshell-precreate></walkthrough-devshell-precreate>

<walkthrough-project-setup></walkthrough-project-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Using Cloud Shell

Cloud Shell is a built-in command-line tool for the console. We're going to use
Cloud Shell to deploy our app.

### Open Cloud Shell

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Clone the sample code

Use Cloud Shell to clone and navigate to the "Hello World" code. The sample code
is cloned from your project repository to the Cloud Shell.

Note: If the directory already exists, remove the previous files before cloning.

In Cloud Shell, enter the following:

```bash
git clone https://github.com/GoogleCloudPlatform/python-docs-samples
```

Then, switch to the tutorial directory:

```bash
cd python-docs-samples/appengine/standard_python37/hello_world
```

## Configuring your deployment

You are now in the main directory for the sample code. We'll look at the files
that configure your application.

### Exploring the application

Enter the following command to view your application code:

```bash
cat main.py
```

The application is a simple Python application that uses the
[Flask](http://flask.pocoo.org/) web framework. This Python app responds to a
request with an HTTP header and the message `Hello World!`.

### Exploring your configuration

App Engine uses YAML files to specify a deployment's configuration.
`app.yaml` files contain information about your application, like the runtime
environment, environment variables, and more.

Enter the following command to view your configuration file:

```bash
cat app.yaml
```

This file contains the minimal amount of configuration required for a Python 3
application. The `runtime` field specifies the `python37` run-time environment.

The syntax of this file is [YAML](http://www.yaml.org). For a complete list of
configuration options, see the [`app.yaml`][app-yaml-ref] reference.

## Testing your app

### Test your app on Cloud Shell

Cloud Shell lets you test your app before deploying to make sure it's running as
intended, just like debugging on your local machine.

To test your app, first create an isolated virtual environment. This ensures
that your app does not interfere with other Python applications that may be
available on your system.

```bash
virtualenv --python python3 ~/envs/hello_world
```

Activate your newly created virtual environment:

```bash
source ~/envs/hello_world/bin/activate
```

Use `pip` to install project dependencies. This "Hello World" app depends on the
Flask microframework:

```bash
pip install -r requirements.txt
```

Finally, run your app in Cloud Shell using the Flask development server:

```bash
python main.py
```

### Preview your app with "Web preview"

Your app is now running on Cloud Shell. You can access the app by clicking the 
[**Web preview**][spotlight-web-preview]
<walkthrough-web-preview-icon></walkthrough-web-preview-icon> button at the top of the Cloud Shell pane and choosing **Preview on port 8080**.

### Terminating the preview instance

Terminate the instance of the application by pressing `Ctrl+C` in the Cloud
Shell.

## Deploying to App Engine

### Create an application

In order to deploy your app, you need to create an app in a region:

```bash
gcloud app create
```

Note: If you already created an app, you can skip this step.

### Deploying with Cloud Shell

You can use Cloud Shell to deploy your app. To deploy your app enter the following:

```bash
gcloud app deploy app.yaml --project {{project_id}}
```

### Visit your app

Congratulations! Your app has been deployed.
The default URL of your app is a subdomain on appspot.com that starts with your project's ID:
[{{project_gae_url}}](http://{{project_gae_url}}).

Try visiting your deployed application.

## View your app's status

You can check in on your app by monitoring its status on the App Engine
dashboard.

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console.

Then, select the **App Engine** section.

<walkthrough-menu-navigation sectionId="APPENGINE_SECTION"></walkthrough-menu-navigation>

## Disable your project

1.  Go to the [**Settings**][spotlight-gae-settings] page.
1.  Click [**Disable Application**][spotlight-disable-app].

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You have successfully deployed an App Engine application!

Here are some next steps:

**Download the Google Cloud SDK and develop locally**

Install the [Google Cloud SDK][cloud-sdk-installer] on your local machine.

**Build your next application**

Learn how to use App Engine with other GCP products:

<walkthrough-tutorial-card url="https://cloud.google.com/python/django/appengine"
  icon="APPENGINE_SECTION" label="django">
  **Run Django.**
  Develop Django apps running on App Engine.
</walkthrough-tutorial-card><walkthrough-alt>Learn more in [Django on App Engine](https://cloud.google.com/python/django/appengine).</walkthrough-alt>

<walkthrough-tutorial-card url="https://cloud.google.com/appengine/docs/standard/python3/building-app/"
  icon="APPENGINE_SECTION" label="building-app">
  **Build a web app.**
  Learn the basics of creating Python web services on App Engine.
</walkthrough-tutorial-card><walkthrough-alt>Learn more in [Building a Python 3.7 app on App Engine](https://cloud.google.com/appengine/docs/standard/python3/building-app/).</walkthrough-alt>

[app-yaml-ref]: https://cloud.google.com/appengine/docs/standard/python3/config/appref
[cloud-sdk-installer]: https://cloud.google.com/sdk/downloads#interactive
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-web-preview]: walkthrough://spotlight-pointer?spotlightId=devshell-web-preview-button
[spotlight-gae-settings]: walkthrough://spotlight-pointer?cssSelector=#cfctest-section-nav-item-settings
[spotlight-disable-app]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-show-disable-app-modal-button
