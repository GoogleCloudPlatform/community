# Cloud Storage Quickstart

## Welcome to Google Cloud Storage!

<walkthrough-tutorial-url url="https://cloud.google.com/storage/docs/quickstart-console"></walkthrough-tutorial-url>

Google Cloud Storage is a powerful and cost-effective storage solution for
unstructured objects, perfect for everything from hosting live web content to
storing data for analytics to archiving and backup.

In this tutorial, we'll show you how easy it is to start storing objects in
Cloud Storage. Here's what you'll do:

  *  **Create a bucket**

     Buckets hold the objects (any type of file) you want to store in Cloud
Storage.

  *  **Upload and share objects**

     Start using your bucket by uploading an object and making it publicly
available.

  *  **Clean up**

     As a final step, you'll delete the bucket and object you created for this
tutorial.

Since you'll be deleting your bucket and object at the end, don't worry about
getting charged for trying this tutorial.

## Project Setup

Cloud Storage needs a project to create resources.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Create a bucket

In Cloud Storage, you store your objects in buckets. To create a bucket, you
need to go to the Cloud Storage browser.

Open the [menu][spotlight-menu] on the left side of the console.

Then, select the **Storage** section.

<walkthrough-menu-navigation sectionId="STORAGE_SECTION"></walkthrough-menu-navigation>

## Create a bucket

Before you can start uploading objects, you need to create a "bucket" to store
them in. Buckets help you organize your objects and control access to them.

  1. Click [Create bucket][spotlight-create-bucket]

  1. On the bucket creation page, specify the bucket's properties. Here are some
    things to keep in mind:

     *  **Name:** Think of something unique. You'll see an error if you enter a
    name that's the same as another bucket's name in Cloud Storage.
     *  **Default storage class:** This is the storage class assigned to your
    bucket's objects by default. Your choice depends mainly on how
    frequently you expect the objects to be accessed and whether you're
    serving the data worldwide. The storage class affects your cost.
     *  **Location:** You'll want to keep your data close to the applications
    and users accessing it. The available choices depend on your storage
    class selection.

For this trial run, any storage class and location will do, as you'll be
deleting the bucket at the end.

  1. Click [Create][spotlight-create-button]

## Upload an object

Now that you have a bucket, you can start uploading objects.

  1. At the top of the page, click [Upload files][spotlight-upload-file]

  1. Select a file to upload. You can upload any type of file.

     Don't have a file? [Create a sample file][create-sample-file], then click
[Refresh Bucket][spotlight-refresh-bucket] at the top of the page to see it
in your bucket. (Tip: You can also upload objects by dragging and dropping
them onto the space below your bucket name.)

## Delete the bucket

Now let's delete the bucket you just created. Deleting a bucket also deletes its
contents.

  1. At the top of the table, click [Buckets][spotlight-buckets-link] to go back
    to the list of buckets.

  1. Check the box next to your bucket. If there are other buckets in this
    project and you need help finding yours, use the search bar to filter the
    bucket list.

  1. At the top of the page, click [Delete][spotlight-delete-buckets] and confirm
    your deletion.

## Conclusion

<walkthrough-conclusion-trophy/>

Congratulations!

Now that you know how to start storing objects in Cloud Storage, you may want to
learn about putting it to real-world use by [hosting a static
website](https://cloud.google.com/storage/docs/hosting-static-website).

Or learn to use Cloud Storage with [the gsutil command-line
tool](https://cloud.google.com/storage/docs/quickstart-gsutil).

Learn how you can start using Cloud Storage and other GCP services for
[free](https://cloud.google.com/free).

[create-sample-file]: walkthrough://create-sample-storage-file
[spotlight-buckets-link]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-path-link
[spotlight-create-bucket]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-cloudstorage-create-first-bucket-button,#p6n-cloudstorage-create-bucket
[spotlight-create-button]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-gcs-create-bucket-button
[spotlight-delete-buckets]: walkthrough://spotlight-pointer?spotlightId=gcs-action-bar-delete-bucket
[spotlight-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-public-link]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-browser-public-label
[spotlight-refresh-bucket]: walkthrough://spotlight-pointer?spotlightId=gcs-action-bar-refresh-objects
[spotlight-share-public]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-browser-public-checkbox
[spotlight-upload-file]: walkthrough://spotlight-pointer?spotlightId=gcs-action-bar-upload-file
