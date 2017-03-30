---
title: Call the Cloud Vision API from Java 
description: Learn how to call the Cloud Vision API from a Java program without using the client libraries
author: lauriewhite
tags: Cloud Vision API, Java, education 
date_published: 11/03/2016
---
## The Cloud Vision API

The [Cloud Vision API](http://cloud.google.com/vision) is a powerful and potentially fun pretrained Machine Learning model that can analyze images.  You can use it directly from the overview page or adjust parameters using the API Explorer in the [Quickstart](http://cloud.google.com/vision/docs/quickstart).  But if you want to call it from a program, it becomes a little bit more complicated.

The two major considerations you need to make are:
- How will you authenticate the request?
- How will you access the API?



## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Ensure the Vision API is enabled by going to the [API manager](https://console.cloud.google.com/apis/) from the main GCP menu.

## Authentication

Since there is a [charge to use the Vision API](https://cloud.google.com/vision/pricing) (although it's less than 1 cent per image and the first 1000 requests are free), programs that use it must be authenticated.  The two options are to use an API key or to set up a service account.  Details can be found at [this page](https://cloud.google.com/vision/docs/common/auth).  From that page: 

> When accessing a Google Cloud Platform API, we recommend that you 
> [set up an API key](https://cloud.google.com/vision/docs/common/auth#set_up_an_api_key) 
> for testing purposes, and 
> [set up a service account](https://cloud.google.com/vision/docs/common/auth#set_up_a_service_account) 
> for production usage.

Creating an API key is simple from the Credentials section of the API manager, so that is the method used in this tutorial.

### Action: Generate an API key for your project.


## Accessing the API

The Vision API can be accessed directly using [an HTTP POST request](https://cloud.google.com/vision/reference/rest/v1/images/annotate).  There are also API libraries created for C#, Go, Java, Node.js, and Python.  In order to keep this tutorial simple and as general as possible, it will use HTTP requests.

You can find details on how to use the API libraries (including those to provide access) in the [label detection](https://cloud.google.com/vision/docs/label-tutorial) and [face detection](https://cloud.google.com/vision/docs/face-tutorial) tutorials.


## Providing the Image

You can either send the actual image to be analyzed to the API or you can send the source of the image.  Again, rather than deal with the complexities of base64 encoding an image for this first example, we'll upload the image to Google Cloud Storage.

### Action: Create a bucket in [Google Cloud Storage](https://console.cloud.google.com/storage) by going to Storage from the main GCP menu and then selecting Create Bucket. 

### Action: Upload an image to the bucket.  First, open the bucket and then select Upload Files.  Ensure the image is shared publicly.

## Check it out

Once you've done the preliminaries, you can check your work by making a `curl` call:

```	
curl -X POST -H "Content-Type: application/json" \
  -d '{"requests":  [{ "features":  [ {"type": "LABEL_DETECTION"}], "image": {"source": { "gcsImageUri": "gs://your-bucket-name/your-file-name"}}}]}' \
  https://vision.googleapis.com/v1/images:annotate?key=your-key
```
where:
* `your-bucket-name` is the name of the bucket you created 
* `your-file-name` is the name of the file you uploaded
* `your-key` is your API key
* `LABEL_DETECTION` may be any one of 
  * `FACE_DETECTION` Run face detection.
  * `LANDMARK_DETECTION` Run landmark detection.
  * `LOGO_DETECTION` Run logo detection.
  * `LABEL_DETECTION` Run label detection.
  * `TEXT_DETECTION` Run OCR.
  * `SAFE_SEARCH_DETECTION` Run various computer vision models to compute image safe-search properties.
  * `IMAGE_PROPERTIES` Compute a set of properties about the image (such as the image's dominant colors).

This information was from this [reference document](https://cloud.google.com/vision/reference/rest/v1/images/annotate#Feature).
  
So the command below would do label detection on a picture of kittens:
	
```
curl -X POST -H "Content-Type: application/json" \
  -d '{"requests":  [{ "features":  [ {"type": "LABEL_DETECTION"}], "image": {"source": { "gcsImageUri": "gs://vision-sample-images/4_Kittens.jpg"}}}]}' \
  https://vision.googleapis.com/v1/images:annotate?key=your-key
````

(You still need to enter your own API key.)

This should give you a response similar to the following:

```
{
  "responses": [
    {
      "labelAnnotations": [
        {
          "mid": "/m/01yrx",
          "description": "cat",
          "score": 0.994864
        },
        {
          "mid": "/m/04rky",
          "description": "mammal",

          "score": 0.94777352
        },
        {
          "mid": "/m/09686",
          "description": "vertebrate",
          "score": 0.93461305
        },
        {
          "mid": "/m/0307l",
          "description": "cat like mammal",
          "score": 0.85113752
        },
        {
          "mid": "/m/0k8hs",
          "description": "domestic long haired cat",
          "score": 0.84654677
        }
      ]
    }
  ]
}
```

(Image from [Wikimedia](https://commons.wikimedia.org/wiki/File:4_Kittens.jpg).)

Details are available about the response [here](https://cloud.google.com/vision/reference/rest/v1/images/annotate#EntityAnnotation).  The "mid" field is an opaque entity ID, which will be ignored for the rest of this tutorial.  The "score" is a value in the range [0, 1] and reflects the likelihood the response is correct.

## Doing this in Java

Once the framework is in place, the problem is reduced to how to make POST requests in Java. While there are specialized libraries for doing HTTP requests in Java, in the name of simplicity, this example will show how to do them using just the `java.` libraries.

First, create constants for the API key and URL:
	
```
private static final String TARGET_URL = 
               "https://vision.googleapis.com/v1/images:annotate?";
private static final String API_KEY = 
               "key=your key here";
```

Next, create a URL object with the target URL and create a connection to that URL:

```
URL serverUrl = new URL(TARGET_URL + API_KEY);
URLConnection urlConnection = serverUrl.openConnection();
HttpURLConnection httpConnection = (HttpURLConnection)urlConnection;
```

Set the method and Content-Type of the connection:

```
httpConnection.setRequestMethod("POST");
httpConnection.setRequestProperty("Content-Type", "application/json");
```

And then prepare the connection to be written to to enable creation of the data portion of the request:

```
httpConnection.setDoOutput(true);
```

Create a writer and use it to write the data portion of the request:	

```
BufferedWriter httpRequestBodyWriter = new BufferedWriter(new 
                   OutputStreamWriter(httpConnection.getOutputStream()));
httpRequestBodyWriter.write
    ("{\"requests\":  [{ \"features\":  [ {\"type\": \"LABEL_DETECTION\"" 
    +"}], \"image\": {\"source\": { \"gcsImageUri\":"
    +" \"gs://vision-sample-images/4_Kittens.jpg\"}}}]}");
httpRequestBodyWriter.close();
```

Finally, make the request and get the response:

```
String response = httpConnection.getResponseMessage();
```

The returned data is sent in an input stream.  Print the result and build a string containing it.

```
if (httpConnection.getInputStream() == null) {
   System.out.println("No stream");
   return;
}
			
Scanner httpResponseScanner = new Scanner (httpConnection.getInputStream());
String resp = "";
while (httpResponseScanner.hasNext()) {
   String line = httpResponseScanner.nextLine();
   resp += line;
   System.out.println(line);  //  alternatively, print the line of response
}
httpResponseScanner.close();
```


## Summary

Let's summarize:

*  You'll need a Google Cloud Platform project created to use the Cloud Vision API.
*  You'll have to have an API key and a bucket with an image in that project.
*  A post request can be made using just the `java.` libraries.
*  The response to the request will be returned as an input stream.
	
## Building on this

There's a lot more that can be done after doing this tutorial.  Some future directions include:
	
* sending any image of the user's choice using base64 encoding
* parsing the resulting JSON 
* doing something interesting with the resulting JSON (like perhaps replacing all faces with cat faces?)

For inspiration of how the Cloud Vision API can classify a large collection of images, see the [Vision Explorer](http://vision-explorer.reactive.ai). 

