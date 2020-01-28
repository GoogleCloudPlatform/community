---
title: App Engine quickstart using Java
description: Learn how to deploy a Java sample app to App Engine.
author: jscud
tags: App Engine
date_published: 2019-03-22
---

# App Engine quickstart using Java

<walkthrough-test-start-page url="/getting-started?tutorial=java_gae_quickstart_2"/>

<walkthrough-tutorial-url url="https://cloud.google.com/appengine/docs/java/quickstart"/>

<!-- {% setvar repo_url "https://github.com/GoogleCloudPlatform/appengine-try-java" %} -->

<!-- {% setvar repo_name "appengine-try-java" %} -->

<!-- {% setvar project_gae_url "<your-project>.appspot.com" %} -->

<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=java_gae_quickstart)

</walkthrough-alt>

## Introduction

This tutorial shows you how to deploy a sample [Java][java] application to
App Engine using the App Engine Maven plugin.

Here are the steps you will be taking.

*   **Create a project**

    Projects bundle code, VMs, and other resources together for easier
    development and monitoring.

*  **Build and run your "Hello, world!" app**

   You will learn how to run your app using Cloud Shell, right in your
   browser. At the end, you'll deploy your app to the web using the App Engine
   Maven plugin.

*  **After the tutorial...**

   Your app will be real and you'll be able to experiment with it after you
   deploy, or you can remove it and start fresh.

[Java is a registered trademark of Oracle and/or its affiliates.](walkthrough://footnote)

## Project setup

GCP organizes resources into projects, which collect all of the related resources for a single
application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-devshell-precreate/>

<walkthrough-project-setup></walkthrough-project-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Using Cloud Shell

Cloud Shell is a built-in command-line tool for the console. You're going to
use Cloud Shell to deploy your app.

### Open Cloud Shell

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Clone the sample code

Use Cloud Shell to clone and navigate to the "Hello World" code. The sample
code is cloned from your project repository to the Cloud Shell.

Note: If the directory already exists, remove the previous files before cloning:

```bash
rm -rf appengine-try-java
```

In Cloud Shell enter the following:

```bash
git clone https://github.com/GoogleCloudPlatform/appengine-try-java
```

Then, switch to the tutorial directory:

```bash
cd appengine-try-java
```

## Configuring your deployment

You are now in the main directory for the sample code. You'll look at the
files that configure your application.

### Exploring the application

Enter the following command to view your application code:

```bash
cat src/main/java/myapp/DemoServlet.java
```

This servlet responds to any request by sending a response containing the
message `Hello, world!`.

### Exploring your configuration

For Java, App Engine uses XML files to specify a deployment's
configuration.

Enter the following command to view your configuration file:

```bash
cat pom.xml
```

The `helloworld` app uses Maven, which means you must specify a Project Object
Model, or POM, which contains information about the project and configuration
details used by Maven to build the project.

## Testing your app

### Test your app on Cloud Shell

Cloud Shell lets you test your app before deploying to make sure it's running
as intended, just like debugging on your local machine.

To test your app enter the following:

```bash
mvn appengine:run
```

<walkthrough-test-code-output
  text="module .* running at|Dev App Server is now running" />

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

Note: If you already created an app, you can skip this step.

### Deploying with Cloud Shell

Now you can use Cloud Shell to deploy your app.

First, set which project to use:

```bash
gcloud config set project {{project_id}}
```

Then deploy your app:

```bash
mvn appengine:deploy
```

<walkthrough-test-code-output text="Deployed (module|service)" />

### Visit your app

Congratulations! Your app has been deployed.

The default URL of your app is a subdomain on appspot.com that starts with your project's ID:
[{{project_gae_url}}](http://{{project_gae_url}}).

Try visiting your deployed application.

### View your app's status

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

**Download the Google Cloud SDK and develop locally.**

Install the [Google Cloud SDK][cloud-sdk-installer] on your local machine.

**Build your next application**

Learn how to use App Engine with other Google Cloud Platform products:

<walkthrough-tutorial-card url="https://cloud.google.com/appengine/docs/standard/java/datastore/" icon="DATASTORE_SECTION" label="datastore">
**Learn to use Cloud Datastore.** Cloud Datastore is a highly-scalable NoSQL database for your applications.</walkthrough-tutorial-card>
<walkthrough-alt>Learn more in the [Cloud Datastore documentation](https://cloud.google.com/appengine/docs/standard/java/datastore/).</walkthrough-alt>

<walkthrough-tutorial-card url="https://cloud.google.com/appengine/docs/standard/java/googlecloudstorageclient/setting-up-cloud-storage" icon="STORAGE_SECTION" label="cloudStorage">
**Learn to use Cloud Storage.** Cloud Storage is a powerful and simple object storage service.
</walkthrough-tutorial-card><walkthrough-alt>Check out the [Cloud Storage documentation](https://cloud.google.com/appengine/docs/standard/java/googlecloudstorageclient/setting-up-cloud-storage) for more details.</walkthrough-alt>

[java]: https://java.com/
[cloud-sdk-installer]: https://cloud.google.com/sdk/downloads#interactive
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-web-preview]: walkthrough://spotlight-pointer?spotlightId=devshell-web-preview-button
[spotlight-gae-settings]: walkthrough://spotlight-pointer?cssSelector=#cfctest-section-nav-item-settings
[spotlight-disable-app]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-show-disable-app-modal-button
