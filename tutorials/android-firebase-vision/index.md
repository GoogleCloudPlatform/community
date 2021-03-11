---
title: Adding computer vision to your Android app
description: Learn how to use Firebase storage with Cloud Functions to access the Vision API from Android apps.
author: gguuss
tags: Android, Vision, Firebase, Storage, Firebase Datastore
date_published: 2017-12-05
---

Gus Class | Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Sara Robinson has authored an excellent post explaining one approach
to [Adding computer vision to your app](https://medium.com/@srobtweets/adding-computer-vision-to-your-ios-app-66d6f540cdd2).

In the post, she introduces the following pattern:

* Use Firebase Auth native client to upload to Firebase Storage.
* Use Cloud Functions to access Vision API and store the result in Firestore.
* Access Cloud Firestore from device to retrieve the API Result.

Sara uses iPhone X in her application, but you can get similar results with Android. 
This tutorial, based on the Firebase storage quickstart for
Android, provides a quick proof of concept.

Start by checking out a short demo of how the proof of concept works.

First, you upload an image to Firebase storage from your Android device:

![Firebase storage sample app Upload button](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/firebase-storage-updload.png)

![Upload selector with pug selected](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/firebase-image-picker.png)

After the image is uploaded, a link to the uploaded file is presented in the
app, exactly the same as in the sample app. Then the app retrieves the
detected labels for the image and presents them.

![The image download link and labels are presented](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/firebase-image-detections.png)

Now take a closer look at how each of the steps is performed.

If you want to follow along, start by getting the Firebase quickstart samples.

    git clone https://github.com/firebase/quickstart-android

The storage sample is in the `quickstart-android/storage` folder, and you can find
the instructions for configuring it on [the Firebase Cloud Storage site](https://firebase.google.com/docs/storage/android/start).

You also need to initialize the project sources folder by installing the
Firebase SDK and calling `firebase init` with Storage, Functions, and
Firestore.

## Step 1: Upload a file to Firebase Storage

This step uses the functionality of the sample app. In the sample
app, a service named `MyUploadService` is implemented to upload a file outside of the
main application thread. 

The [`uploadFromUri` function in the sample app](https://github.com/firebase/quickstart-android/blob/f6e021c2bf4ddd3d06908480c909da0ac8175371/storage/app/src/main/java/com/google/firebase/quickstart/firebasestorage/java/MainActivity.java#L178)
illustrates the bulk of the operations performed by the provided service.

After the file is uploaded, the `fileUri` is passed in an **Intent** so that
the `MainActivity` class can retrieve the file data. This is done in the sample
app in the [`MyUploadService` activity's `broadcastUploadFinished` method](https://github.com/firebase/quickstart-android/blob/f6e021c2bf4ddd3d06908480c909da0ac8175371/storage/app/src/main/java/com/google/firebase/quickstart/firebasestorage/java/MyUploadService.java#L151).

You can verify that the storage operation
works by visiting the Firebase console for storage and seeing the uploaded
files:

![Files in Firebase Storage](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/firebase-storage-console.png)


## Step 2: Analyze the image and publish label data to Firestore

Now that the files are successfully uploading to Firebase Storage, it's time
to process the file using a Cloud Functions call. This operation is virtually
identical to the Cloud Functions API call made by Sara in her post, but retrieves
only the label data, instead of the label and web annotation data.

The following code, specified in `index.js` in the functions folder, loads the
required libraries for Firebase and Google Cloud Vision, and then transfers the
API call result to Firestore.

[![Code for step 2](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/code2.png)](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/android-firebase-vision/code-step-2.txt)

You can see the
results in the Firestore section of the console:

![Firestore console showing detected labels](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/firebase-firestore-console.png)

Of note, you can now see the indexed label data on the right-most column of the
console.


## Step 3: Manually retrieve the label data from Firestore

This tutorial reuses and relabels the **Download** button from the Firebase Storage sample
app to manually trigger the retrieval of the `Label` data from Firestore. To do
this, the button name is changed to `button_detections` in the app resources
and the UI strings are replaced as appropriate. A new method named
`retrieveMetadata` is added to the click handler for the button.

[![Code for step 3a](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/code3a.png)](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/android-firebase-vision/code-step-3a.txt)

The following code shows how to retrieve the metadata for the last uploaded image by using the Firestore API:

[![Code for step 3b](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/code3b.png)](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/android-firebase-vision/code-step-3b.txt)

It might be best to do this in a separate service, but for the
purposes of this proof of concept, this should be sufficient. Also, this replaces
the proto-style object characters with JSON-style object characters because of
manually filtering the result data in `UpdateUI`.

When `UpdateUI` is called, the sample app checks the stored member variable
`mResponse` and then filters the label description strings from the result
data.

[![Code for step 3c](https://storage.googleapis.com/gcp-community/tutorials/android-firebase-vision/code3c.png)](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/android-firebase-vision/code-step-3c.txt)

With the help of Sara's blog post, it was incredibly easy to update the
Firebase Storage sample app to work with the Vision API and return results to
an Android device. This approach to accessing the
Google Cloud Machine Learning features is not restricted to the Vision
API. For example, if you wanted to use the translation API with the NMT model,
you could employ a similar approach but by storing text data instead of photo
data.

## Next steps

If you want to prepare this app for production, think about the following items:

* Fix all the UI - Create label bubbles instead of just formatted text.
* Enable user auth to prevent abuse of your API quota.
* Move the operations done with Firestore to a separate service.
* Eliminate data polling for Firestore data.

See the following sites for more information:

* [Kotlin example app using Firebase with Cloud Functions for Computer Vision](https://github.com/joaobiriba/ARCalories)
* [Adding Computer Vision to your iOS App](https://medium.com/@srobtweets/adding-computer-vision-to-your-ios-app-66d6f540cdd2)

