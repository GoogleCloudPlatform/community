---
title: Make an HTTP request to the Cloud Vision API from Java
description: Learn how to make an HTTP request to the Cloud Vision API from a Java program.
author: annie29
tags: Cloud Vision API, Java, education
date_published: 2016-11-03
---

Laurie White | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

The [Cloud Vision API][vision] is a powerful and potentially fun
pre-trained machine learning model that can analyze images. You can use it
directly from the overview page or adjust parameters using the API Explorer in
the [quickstart][quickstart]. This tutorial shows how to make an HTTP request to
the Cloud Vision API from a Java program.

The two major considerations you need to make:

- How will you authenticate the request?
- How will you access the API?

## Prerequisites

1. Create a project in the [Cloud Console][console].
1. Enable billing for your project.
1. Ensure that the Vision API is enabled by going to the [API manager][manager] from
the main Google Cloud menu.

## Authentication

Since there is a [charge to use the Vision API][pricing] (although it's less
than one cent per image and the first 1000 requests are free), programs that use
it must be authenticated. Read [the instructions for creating an API key][auth].

### Action

Generate an API key for your project.

## Accessing the API

The Cloud Vision API can be accessed directly using
[an HTTP POST request][annotate]. There are also client libraries created for
C#, Go, Java, Node.js, PHP, Python, and Ruby. In order to keep this tutorial
simple and as general as possible, it will make its own HTTP requests.

You can find details on how to use the client libraries in the
[label detection][label-tutorial] and [face detection][face-tutorial] tutorials.

## Providing the image

You can either send the actual image to be analyzed to the API or you can send
the source url of the image. Again, rather than deal with the complexities of
base64 encoding an image for this first example, we'll upload the image to
Google Cloud Storage and let the Cloud Vision API access it from there.

### Action

Create a bucket in [Google Cloud Storage][storage-console] by going to Storage
from the main Console menu and then clicking Create Bucket.

### Action

Upload an image to the bucket. First, open the bucket and then select Upload
Files. Check the box to share the image publicly.

## Making the HTTP request with cURL

Once you've done the preliminaries, you can check your work by running the
following `curl` command:

```sh
curl -X POST -H "Content-Type: application/json" \
  -d '{"requests":  [{ "features":  [ {"type": "LABEL_DETECTION"}], "image": {"source": { "gcsImageUri": "gs://YOUR_BUCKET_NAME/YOUR_FILE_NAME"}}}]}' \
  https://vision.googleapis.com/v1/images:annotate?key=YOUR_API_KEY
```

where:

* `YOUR_BUCKET_NAME` is the name of the bucket you created
* `YOUR_FILE_NAME` is the name of the file you uploaded
* `YOUR_API_KEY` is your API key
* `LABEL_DETECTION` may be any one of
  * `FACE_DETECTION` Run face detection.
  * `LANDMARK_DETECTION` Run landmark detection.
  * `LOGO_DETECTION` Run logo detection.
  * `LABEL_DETECTION` Run label detection.
  * `TEXT_DETECTION` Run OCR.
  * `SAFE_SEARCH_DETECTION` Run various computer vision models to compute image
  safe-search properties.
  * `IMAGE_PROPERTIES` Compute a set of properties about the image (such as the
  image's dominant colors).

Read more about [annotation features][features].

The following command performs label detection on a picture of kittens (you
still need to enter your own API key):

```sh
curl -X POST -H "Content-Type: application/json" \
  -d '{"requests":  [{ "features":  [ {"type": "LABEL_DETECTION"}], "image": {"source": { "gcsImageUri": "gs://vision-sample-images/4_Kittens.jpg"}}}]}' \
  https://vision.googleapis.com/v1/images:annotate?key=YOUR_API_KEY
```

This should give you a response similar to the following:

```json
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

Read more about the [response format][response]. The "mid" field is an opaque
entity ID, which will be ignored for the rest of this tutorial. The "score" is a
value in the range [0, 1] and reflects the likelihood the response is correct.

## Making the HTTP request with Java

For simplicity, this example shows how to make an HTTP request using just the
core Java libraries.

First, create constants for the API key and URL:

```java
private static final String TARGET_URL =
                "https://vision.googleapis.com/v1/images:annotate?";
private static final String API_KEY =
                "key=YOUR_API_KEY";
```

Next, create a URL object with the target URL and create a connection to that
URL:

```java
URL serverUrl = new URL(TARGET_URL + API_KEY);
URLConnection urlConnection = serverUrl.openConnection();
HttpURLConnection httpConnection = (HttpURLConnection)urlConnection;
```

Set the method and Content-Type of the connection:

```java
httpConnection.setRequestMethod("POST");
httpConnection.setRequestProperty("Content-Type", "application/json");
```

And then prepare the connection to be written to to enable creation of the data
portion of the request:

```java
httpConnection.setDoOutput(true);
```

Create a writer and use it to write the data portion of the request:

```java
BufferedWriter httpRequestBodyWriter = new BufferedWriter(new
                    OutputStreamWriter(httpConnection.getOutputStream()));
httpRequestBodyWriter.write
    ("{\"requests\":  [{ \"features\":  [ {\"type\": \"LABEL_DETECTION\""
    +"}], \"image\": {\"source\": { \"gcsImageUri\":"
    +" \"gs://vision-sample-images/4_Kittens.jpg\"}}}]}");
httpRequestBodyWriter.close();
```

Finally, make the request and get the response:

```java
String response = httpConnection.getResponseMessage();
```

The returned data is sent in an input stream. Print the result and build a
string containing it.

```java
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

*  You need a Google Cloud project to use the Cloud Vision API.
*  You need an API key and a storage bucket with an image in that project.
*  A HTTP POST request can be made using just the core Java libraries.
*  The response to the request will be returned as an input stream.

## Next steps

There's a lot more that can be done after doing this tutorial. Some future
directions include:

* Sending any image of the user's choice using base64 encoding.
* Parsing the resulting JSON.
* Doing something interesting with the resulting JSON (like perhaps replacing
all faces with cat faces?)

For inspiration of how the Cloud Vision API can classify a large collection of
images, see the [Vision Explorer](http://vision-explorer.reactive.ai).

[vision]: http://cloud.google.com/vision
[quickstart]: http://cloud.google.com/vision/docs/quickstart
[console]: https://console.cloud.google.com/
[manager]: https://console.cloud.google.com/apis/
[pricing]: https://cloud.google.com/vision/pricing
[auth]: https://cloud.google.com/vision/docs/common/auth
[annotate]: https://cloud.google.com/vision/reference/rest/v1/images/annotate
[label-tutorial]: https://cloud.google.com/vision/docs/label-tutorial
[face-tutorial]: https://cloud.google.com/vision/docs/face-tutorial
[storage-console]: https://console.cloud.google.com/storage
[features]: https://cloud.google.com/vision/reference/rest/v1/images/annotate#Feature
[response]: https://cloud.google.com/vision/reference/rest/v1/images/annotate#EntityAnnotation
