---
title: App Engine quickstart using Go
description: Learn how to deploy a Go sample app to App Engine.
author: jscud
tags: App Engine
date_published: 2019-01-19
---

# App Engine quickstart

<walkthrough-tutorial-url url="https://cloud.google.com/appengine/docs/go/quickstart"></walkthrough-tutorial-url>
<!-- {% setvar repo_url "https://github.com/GoogleCloudPlatform/golang-samples" %} -->
<!-- {% setvar repo_dir "golang-samples/appengine/go11x/helloworld" %} -->
<!-- {% setvar project_gae_url "<your-project>.appspot.com" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?tutorial=go_gae_quickstart)

</walkthrough-alt>

## Introduction

This tutorial shows you how to deploy a sample application to App Engine using the `gcloud` command.

Here are the steps you will be taking.

*   **Create a project**

    Projects bundle code, VMs, and other resources together for easier
    development and monitoring.

*   **Build and run your "Hello, world!" app**

    You will learn how to run your app using Cloud Shell, right in your
    browser. At the end, you'll deploy your app to the web using the `gcloud`
    command.

*   **After the tutorial...**

    Your app will be real and you'll be able to experiment with it after you
    deploy, or you can remove it and start fresh.

## Project setup

Google Cloud organizes resources into projects, which collect all of the related resources for a single
application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Using Cloud Shell

Cloud Shell is a built-in command-line tool for the console. We're going to use Cloud Shell to deploy our app.

### Open Cloud Shell

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Clone the sample code

Use Cloud Shell to clone and navigate to the "Hello World" code. The sample code is cloned from your project repository to
the Cloud Shell.

Note: If the directory already exists, remove the previous files before cloning.

```bash
git clone {{repo_url}}
```

Then, switch to the tutorial directory:

```bash
cd {{repo_dir}}
```

## Configuring your deployment

You are now in the main directory for the sample code. We'll look at the files that configure your application.

### Exploring the application

Enter the following command to view your application code:

```bash
cat helloworld.go
```

### Exploring your configuration

App Engine uses YAML files to specify a deployment's configuration. `app.yaml` files contain information about your 
application, like the runtime environment, URL handlers, and more.

Enter the following command to view your configuration file:

```bash
cat app.yaml
```

The syntax of this file is [YAML](http://www.yaml.org). For a complete list of
configuration options, see the [`app.yaml`][app-yaml-ref] reference.

## Testing your app

### Test your app on Cloud Shell

Cloud Shell lets you test your app before deploying to make sure it's running as
intended, just like debugging on your local machine.

To test your app enter the following:

```bash
go run .
```

### Preview your app with "Web preview"

Your app is now running on Cloud Shell. You can access the app by clicking the
[**Web preview**][spotlight-web-preview]
<walkthrough-web-preview-icon></walkthrough-web-preview-icon> button at the top
of the Cloud Shell pane and choosing **Preview on port 8080**.

### Terminating the preview instance

Terminate the instance of the application by pressing `Ctrl+C` in the Cloud Shell.

## Deploying to App Engine

### Create an application

To deploy your app, you need to create an app in a region:

```bash
gcloud app create
```

**Note:** If you already created an app, you can skip this step.

### Deploying with Cloud Shell

You can use Cloud Shell to deploy your app. To deploy your app enter the following:

```bash
gcloud app deploy
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

Here are some next steps for building your next application and learning to use App Engine with other GCP products:

**Download the Cloud SDK and develop locally.**

Install the [Cloud SDK][cloud-sdk-installer] on your local machine.

<walkthrough-tutorial-card url="appengine/docs/go/datastore/" icon="DATASTORE_SECTION" label="datastore">
**Learn to use Datastore.** Datastore is a highly-scalable NoSQL database for your applications.</walkthrough-tutorial-card>
<walkthrough-alt>Learn more in the [Datastore documentation](https://cloud.google.com/appengine/docs/standard/java/datastore/).</walkthrough-alt>

<walkthrough-tutorial-card url="appengine/docs/go/googlecloudstorageclient/setting-up-cloud-storage" icon="STORAGE_SECTION" label="cloudStorage">
**Learn to use Cloud Storage.** Cloud Storage is a powerful and simple object storage service.
</walkthrough-tutorial-card><walkthrough-alt>Check out the [Cloud Storage documentation](https://cloud.google.com/appengine/docs/standard/java/googlecloudstorageclient/setting-up-cloud-storage) for more details.</walkthrough-alt>

[app-yaml-ref]: https://cloud.google.com/appengine/docs/standard/go/config/appref
[cloud-sdk-installer]: https://cloud.google.com/sdk/downloads#interactive
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-web-preview]: walkthrough://spotlight-pointer?spotlightId=devshell-web-preview-button
[spotlight-gae-settings]: walkthrough://spotlight-pointer?cssSelector=#cfctest-section-nav-item-settings
[spotlight-disable-app]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-show-disable-app-modal-button
