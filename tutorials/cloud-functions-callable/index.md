---
title: Calling Google Cloud APIs from your mobile app
description: Learn how to use Cloud Functions and Firebase Authentication to call Cloud APIs from your Android or iOS app.
author: samtstern
tags: firebase, functions, callable
date_published: 2020-11-10
---

Sam Stern | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Many Google Cloud APIs—such as the [Translation](https://cloud.google.com/translate) and [Vision AI](https://cloud.google.com/vision) APIs—provide useful 
features for mobile apps but no simple way to access these features directly. To call these APIs from your Android or iOS app, you generally need to create an 
intermediate REST API that handles authorization and protects secret values such as API keys. You then need to write code in your mobile app to authenticate to 
and communicate with this intermediate service.

By using Cloud Functions with Firebase Authentication, you can create managed, serverless gateways to Google Cloud APIs that handle authentication and can be
called from your mobile app with pre-built SDKs.

This tutorial uses the Cloud Translation API as an example, but this technique is valid with any Google Cloud API that you want to call from your mobile app.

## Objectives

*   Create a Cloud Function to authenticate your users with Firebase Authentication.
*   Create a Cloud Function to call the Translation API.
*   Sign in with Firebase Authentication in your mobile app.
*   Use the Cloud Functions for Firebase SDK to call your function securely from your app.

## Costs

This tutorial uses billable components of Google Cloud and Firebase, including the following:

  * Cloud Functions: [no fixed cost, usage-based pricing](https://cloud.google.com/functions)
  * Firebase Authentication: [free for unlimited use](https://firebase.google.com/pricing)
  * Cloud Translation: [no fixed cost, usage-based pricing](https://cloud.google.com/translate)
  
    The Cloud Translation API is used for the purposes of this example but is not essential to the technique presented.

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

To follow this tutorial, you need to have a few things set up:

1.  Create a Google Cloud project in the [Cloud Console](https://console.cloud.google.com/).
1.  Link your project to [Firebase](https://console.firebase.google.com/).
1.  Upgrade your Firebase project to the [Blaze billing plan](https://firebase.google.com/support/faq#pricing-right-plan).
1.  Enable the required APIs in your project:

    * [IAM Service Account Credentials API](https://console.developers.google.com/apis/api/iamcredentials.googleapis.com/)
    * [Cloud Build API](https://console.developers.google.com/apis/api/cloudbuild.googleapis.com/)
    * [Cloud Translation API](https://console.developers.google.com/apis/api/translate.googleapis.com/overview)

1.  Install [Node.js](https://nodejs.org/en/download/) version 10 or higher.
1.  Install the [`gcloud` command-line tool](https://cloud.google.com/sdk/docs/install).
1.  Install either [Android Studio](https://developer.android.com/studio/install) or [XCode](https://developer.android.com/studio/install), and open an existing
    app or create a new one.

## Create your first Cloud Function

In this section, you write a Cloud Function that issues Firebase Authentication tokens to users of your mobile app.

### Set up a source directory

1.  Create a new directory:

        mkdir cloud-functions-callable

1.  Go to the new directory:

        cd cloud-functions-callable

1.  Create a basic `package.json` file:

        npm init

    For the purposes of this tutorial, you can give any answer to the prompts from `npm init`.

### Set the Google Cloud project

Configure the `gcloud` tool to use your Google Cloud project for all future commands:

    gcloud config set project "YOUR_PROJECT_ID"

### Authorize the service account

1.  In the [IAM & Admin](https://console.cloud.google.com/iam-admin/iam) section of the Cloud Console, find the `YOUR_PROJECT_ID@appspot.gserviceaccount.com`
    service account.
1.  Edit that service account to grant it the following roles:

    *  Service Account Token Creator
    *  Cloud Translation API User

### Install dependencies for the Cloud Function

1.  Install the [Node.js client library](https://cloud.google.com/translate/docs/reference/libraries/v3/nodejs) for the Google Cloud Translation API:

        npm install --save @google-cloud/translate

1.  Install the [Firebase Functions SDK](https://firebase.google.com/docs/reference/functions):

        npm install --save firebase-functions
        
1.  Install the [Firebase Node.js Admin SDK](https://firebase.google.com/docs/admin/setup):

        npm install --save firebase-admin

### Write the function

In a new file called `index.js`, add the following code and change the `PROJECT_ID` value at the top to your real project ID:

    const functions = require('firebase-functions');
    const admin = require('firebase-admin');

    const PROJECT_ID = 'YOUR_PROJECT_ID';

    // Initialize the Firebase Admin SDK using Application Default credentials
    
    admin.initializeApp({
      projectId: PROJECT_ID,
      credential: admin.credential.applicationDefault()
    });

    exports.getAuthToken = functions.https.onCall(async (data, context) => {
    
      // For the purposes of this example, you have the user specify their
      // own UID as part of the request. This is obviously insecure, and in
      // a real app you should get the user's identity from your own backend.
      
      const uid = data.uid;

      // Create a custom auth token with the UID and some claims. Claims
      // can be used to add any user-specific information to the token;
      // they have no fixed schema.
      
      const token = await admin.auth().createCustomToken(uid, {
        allowTranslationAPI: true
      });

      return { token };
    });
    
This function responds to HTTP requests with Firebase [Custom Authentication](https://firebase.google.com/docs/auth/admin/create-custom-tokens) tokens, which you
use later in your mobile app.

## Create a secure Cloud Function to make API calls

In this section, you write a Cloud Function that calls the Translation API and is protected by Firebase Authentication.

### Initialize the Translation client library

At the top of your `index.js` file, add the following lines to import and initialize the Translation client library:

    const { TranslationServiceClient } = require('@google-cloud/translate');

    const translationClient = new TranslationServiceClient();

### Add a new Cloud Function to call the API

At the end of your `index.js` file, add the following new Cloud Function:

    exports.translateText = functions.https.onCall(async (data, context) => {
    
      // Ensure that the user is authenticated and that they have the
      // custom claim made in the previous step
      
      if (!context.auth || !context.auth.token.allowTranslationAPI) {
        throw new functions.https.HttpsError(
          "permission-denied", 
          "The calling user does not have permission to use this function"
        );
      }

      // Get the text to translate from the request
      
      const text = data.text;

      // Translate from English to Spanish
      
      const request = {
        parent: `projects/${PROJECT_ID}/locations/global`,
        contents: [text],
        mimeType: 'text/plain',
        sourceLanguageCode: 'en',
        targetLanguageCode: 'es'
      };
      const [response] = await translationClient.translateText(request);

      // Get the top translation
      
      const translation = response.translations[0].translatedText;

      // Return translations to the caller
      
      return { translation };
    });

## Deploy Cloud Functions

In this section, you deploy the Cloud Functions so that they are available to call from your mobile app.

### Deploy using `gcloud`

1.  Deploy the Cloud Function that gets the authentication token:

        gcloud functions deploy getAuthToken --runtime nodejs10 --trigger-http --allow-unauthenticated

1.  Deploy the Cloud Function that translates the text:

        gcloud functions deploy translateText --runtime nodejs10 --trigger-http --allow-unauthenticated

1.  Confirm that the functions have been deployed:

        gcloud functions describe getAuthToken
        gcloud functions describe translateText

    The `httpsTrigger.url` in the result gives you the URL. 

1.  Validate that the function behaves as described using `curl`. For example:

        curl \
        --header "Content-Type: application/json" \
        --request POST \
        --data '{ "data": {"uid": "uid1234" } }'
        https://us-central1-YOUR-PROJECT-ID.cloudfunctions.net/getAuthToken

    The result should be something like the following:

        {"result":{"token":"eyJhbGciOiJSUzI [...] 2rA"}}

## Add Firebase to your app

In this section, you add the Firebase Authentication and Firebase Functions SDKs to your mobile app in order to call them.

### Add your app to your Firebase project

Follow one of these guides to add Firebase to your app:

*  [Add Firebase to your Android project](https://firebase.google.com/docs/android/setup)
*  [Add Firebase to your iOS project](https://firebase.google.com/docs/iOS/setup)

### Add the Firebase SDK to your app

Add the Firebase Authentication and Firebase Functions SDKs to your app using the following instructions for Android or iOS.

#### Android

In your `app/build.gradle`, file add these dependencies:

    dependencies {
      // Import the Firebase BoM. See the release notes for the latest version:
      // https://firebase.google.com/support/release-notes/android
      implementation platform('com.google.firebase:firebase-bom:25.12.0')

      // Add specific Firebase dependencies
      implementation 'com.google.firebase:firebase-auth'
      implementation 'com.google.firebase:firebase-functions'
    }


#### iOS

In your `Podfile`, add these dependencies:

    pod 'Firebase/Auth'
    pod 'Firebase/Functions'

## Sign in using Firebase Authentication

In this section, you use the `getAuthToken` Cloud Function to retrieve an authentication token and use Firebase Authentication to sign in.

### Call the function

Use the Firebase Functions SDK to call the function. The Firebase Functions SDK makes it simple for you to call functions by name without having to write any 
HTTP request code or parse results yourself.

#### Android (Kotlin)

    val functions = FirebaseFunctions.getInstance()
    val auth = FirebaseAuth.getInstance()

    // You should replace the UID. See the note in the function source code.
    
    val uid = "uid1234"
    val data = hashMapOf(
        "uid" to uid
    )

    functions
      .getHttpsCallable("getAuthToken")
      .call(data)
      .continueWith { task ->
          val result = task.result?.data as Map<String,String>
          val token = result["token"]!!

          // Retrieve the custom authentication token and sign in. See
          // https://firebase.google.com/docs/auth/android/custom-auth
          
          auth.signInWithCustomToken(token)
            .addOnCompleteListener{ task ->
                if (!task.isSuccessful) {
                  // Handle error if necessary
                  // ...
                }

                // You are now signed in with Firebase Authentication!
                // ...
            }
      }

#### iOS (Swift)

    lazy var functions = Functions.functions()
    lazy var auth = Auth.auth()

    // You should replace the UID. See the note in the function source code.
    
    var uid = "uid1234";

    functions.httpsCallable("getAuthToken").call(["uid": uid]) { (result, error) in
      if let error = error as NSError? {
        if error.domain == FunctionsErrorDomain {
          let code = FunctionsErrorCode(rawValue: error.code)
          let message = error.localizedDescription
          let details = error.userInfo[FunctionsErrorDetailsKey]
        }
        // Handle error in your app 
        // ...
      }

      // Retrieve the custom authentication token and sign in. See
      // https://firebase.google.com/docs/auth/ios/custom-auth
      
      if let token = (result?.data as? [String: Any])?["token"] as? String {
        auth.signIn(withCustomToken: token) { (user, error) in
          // Handle error if necessary, otherwise you are now signed in with
          // Firebase Authentication!
          // ...
        }
      }
    }

## Call the Translation API through Cloud Functions

When you are signed in with Firebase Authentication, all future API calls using the Firebase Functions SDK automatically provide authentication context, which 
is available inside the Cloud Function as `context.auth`.

### Call the function

In this section, as in the previous section, you use the Firebase Functions SDK to call the `translateText` function by name.

#### Android (Kotlin)

    val functions = FirebaseFunctions.getInstance()

    val text = "Hello, World!"
    val data = hashMapOf(
        "text" to text
    )

    functions
      .getHttpsCallable("translateText")
      .call(data)
      .continueWith { task ->
          val result = task.result?.data as Map<String,Object>
          val translation = result["translation"]!!

          // Display the translation in your app
          // ...
      }

#### iOS (Swift)

    lazy var functions = Functions.functions()

    var text = "Hello, World!";

    functions.httpsCallable("translateText").call(["text": text]) { (result, error) in
      if let error = error as NSError? {
        if error.domain == FunctionsErrorDomain {
          let code = FunctionsErrorCode(rawValue: error.code)
          let message = error.localizedDescription
          let details = error.userInfo[FunctionsErrorDetailsKey]
        }
        // Handle error in your app
        // ...
      }

      if let translation = (result?.data as? [String: Any])?["translation"] as? String {
        // Display the translation in your app
        // ...
      }
    }

## Cleaning up

### Option 1: Delete Cloud Functions

None of the products used in this tutorial have any ongoing fixed costs. However, it's a good practice to clean up these unused Cloud Functions, which are 
currently exposed on the internet.

To delete the functions, use these `gcloud` commands:

    gcloud functions delete getAuthToken
    gcloud functions delete translateText

### Option 2: Delete the project

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [callable Cloud Functions](https://firebase.google.com/docs/functions/callable).
- Learn more about [Firebase Authentication](https://firebase.google.com/docs/auth).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
