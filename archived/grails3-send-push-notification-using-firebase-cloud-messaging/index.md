---
title: Grails 3 sending push notification using Firebase Cloud Messaging
description: Step by step tutorial on how to send push notification using Grails 3 and Firebase Cloud Messaging.
author: didinj
tags: Firebase, Firebase Cloud Messaging, FCM, Grails, Grails 3, Push Notification
date_published: 2017-08-23
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows how to send push notification using
[Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging)
and [Grails 3 Framework](https://grails.org/) web application.

## Objectives

- Configure Firebase to send push notifications with a web application
- Create a new Grails 3.3.0 web application
- Create function for sending push notification on Grails 3.3.0

## Before you begin

The following is required for this tutorial:

- Terminal or command line
- Text editor or IDE ([Atom](https://atom.io/), [Netbeans](https://netbeans.org/))
- [Java Development Kit 8](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html)
- Grails 3.3.0 SDK (https://grails.org/download.html)
- Google or Gmail account for accessing Firebase dashboard

## Costs

This tutorial uses Firebase Cloud Messaging service which is free for limited features and capacities.

## Configure Firebase Cloud Messaging

1.  Open your browser then go to [Firebase](https://firebase.google.com/).
1.  Login using your Gmail account then click Go to Console button.
1.  Click add project button then give it a name. For this tutorial name it
    "GrailsFCM" then click Create Project button.
1.  It will redirect to the Project dashboard. Click the gear icon in the left
    menu and select Project Settings.
1.  Click the Cloud Messaging tab and copy the Server Key to your
    notepad. You will use it later in the Grails web application.
1.  Next, configuration your app for
    [Android](https://firebase.google.com/docs/cloud-messaging/android/client)
    or [iOS](https://firebase.google.com/docs/cloud-messaging/ios/client).

## Create new Grails 3.3.0 web application

After installing JDK 8 and Grails 3.3.0 and updating your environment path, you
can create the new Grails 3.3.0 application.

1.  Open terminal or command line then go to your projects folder.
1.  Run this command:

        grails create-app grails-fcm

1.  Go to the newly created Grails 3 application folder:

        cd grails-fcm

1.  Enter Grails 3 interactive console by type this command:

        grails

1.  In the Grails interactive console, you will see the following:

        | Resolving Dependencies. Please wait...

        CONFIGURE SUCCESSFUL

        | Enter a command name to run. Use TAB for completion:
        grails>

1.  Test your Grails web application by typing this command in the Grails
    interactive console:

        run-app

## Add Grails datastore REST client dependency

To access Firebase using REST API, add the Grails Datastore Client Rest
dependency to the Grails 3 application.

1.  Open and edit `build.gradle`.

1.  Add the Grails Datastore Client Rest dependency inside the dependencies
    section. There are two dependencies, one inside buildscript and the other
    outside buildscript:

        dependencies {
            ...
            compile "org.hibernate:hibernate-core:5.1.2.Final"
            compile "org.hibernate:hibernate-ehcache:5.1.2.Final"
            compile 'org.grails:grails-datastore-rest-client:5.0.0.RC2'
            console "org.grails:grails-console"
            profile "org.grails.profiles:web"
            runtime "com.bertramlabs.plugins:asset-pipeline-grails:2.11.6"
            ...
        }

1.  Compile the Grails 3 application by typing this command in the Grails
    interactive console:

        compile

## Create Grails controller and view for sending push notifications

Run the following steps:

1.  Create controller by running this command:

        create-controller Fcm

1.  Add import to the file `grails-app/controllers/grails/fcm/FcmController.groovy`:

        import grails.plugins.rest.client.RestBuilder

1.  Create a method to FcmController, so it will looks like this.

    ```groovy
    package grails.fcm

    import grails.plugins.rest.client.RestBuilder

    class FcmController {

      def index() { }

      def sendPushNotification() {
        def regid = params.regid
        def title = params.title
        def body = params.body

        def rest = new RestBuilder(connectTimeout:1000, readTimeout:20000)
        def resp = rest.post("https://fcm.googleapis.com/fcm/send") {
          header 'Content-Type', 'application/json'
          header 'Authorization', 'key=AIza*****'
          json {
            notification = {
              title = title
              body = body
              sound = "default"
              click_action = "FCM_PLUGIN_ACTIVITY"
              icon = "fcm_push_icon"
            }
            to = regid
          }
        }

        flash.message = "Notification sent"
        redirect action: "index"
      }
    }
    ```

    Enter the Legacy Server key you saved from your project dashboard in the
    line that begins with 'key=':

        header 'Authorization', 'key=AIza*****'


1.  Create a view file `grails-app/views/fcm/index.gsp` with the content from
    [index.gsp]((https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/grails3-send-push-notification-using-firebase-cloud-messaging/index.gsp).

1.  Run and test push notification from the browser.

## Cleaning up

After you have finished this tutorial, clean up your Firebase project because
you can only have 3 projects in the free tier. Just do the following:

1.  Go to Firebase Console again.
1.  Choose the project that you want to remove.
1.  Click gear icon on the left menu then click Project Settings menu.
1.  Scroll down the you will find delete project button.

## Learn more

Visit [Grails Guides](http://guides.grails.org/) to learn more on official
Grails guides or if you want different tutorial style you can find
[here](https://www.djamware.com/post-sub-category/585b3fa380aca73b19a2efd4/groovy-and-grails).

View the source code for this tutorial [on GitHub](https://github.com/didinj/grails3-fcm-push-notification.git).
