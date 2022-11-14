---
title: On Beyond Magpie 1 - Sentiment Analysis
description: An introduction to the Cloud Natural Language API, aimed at Advanced Placement Computer Science classes who have worked on the Magpie lab, but suitable for most people starting with the Cloud Natural Language API. Demonstrates how to make a POST request in Java to access the Cloud Natural Language API and make simple use of the results.
author: Annie29
tags: Cloud Natural Language API, APCS, REST, Magpie, education
date_published: 2017-03-28
---

Laurie White | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

The Advanced Placement Computer Science A program provides the [Magpie lab](http://media.collegeboard.com/digitalServices/pdf/ap/ap-compscia-magpie-lab-student-guide.pdf) for students to practice using basic control structures to parse user input as part of a chatbot. This tutorial is designed to be an additional enrichment exercise (typically used after the AP exam) to go beyond  basic parsing and instead use Google's [Cloud Natural Language API][nlp], a pretrained machine learning model that will do text analysis for the user. The lab demonstrates how to use the Cloud Natural Language API to determine the user sentiment.

The major new skill covered in this lab is how to make HTTP POST requests from Java.

This tutorial is written for an audience of CS teachers who are exposing their students to the Cloud Natural Language API, but should be usable by any interested individual.

## Prerequisites

If you've completed [On Beyond Magpie, Part 0][magpie0], you should have all of the prerequisites completed. Otherwise,

1. Create a project in the [Cloud Console][console].
1. Enable billing for your project.
1. Ensure the Cloud Natural Language API is enabled by going to the [API manager][manager] from the main Google Cloud menu.
1. Generate an API key for your project.

## A simple chatbot

Students who have used the Magpie lab already should have a chatbot with which they can work. Otherwise, the following Java code provides a simple (but not very interesting) chatbot.

### Magpie runner

```java
import java.util.Scanner;

/**
	* A simple class to run the Magpie class.
	*/
public class MagpieRunner
{

	/**
		* Create a Magpie, give it user input, and print its replies.
		*/
	public static void main(String[] args)
	{
		Magpie maggie = new Magpie();

		Scanner in = new Scanner (System.in);
		String statement = in.nextLine();

		while (!statement.equals("Bye"))
		{
			System.out.println (maggie.getResponse(statement));
			statement = in.nextLine();
		}
	}
}
```

### Magpie class

```java
public class Magpie
{
	/**
		* Gives a response to a user statement
		*
		* @param statement
		*            the user statement
		* @return a response based on the rules given
		*/
	public String getResponse(String statement)
	{
		String response = "";
		if (statement.indexOf("cats") >= 0)
		{
			response = "I love cats!  Tell me more about cats!";
		}
		else
		{
			response = getRandomResponse();
		}
		return response;
	}

	/**
		* Pick a default response to use if nothing else fits.
		*/
	private String getRandomResponse()
	{
		return "Hmmm";
	}
}
```

## Accessing the API

The Cloud Natural Language API can be accessed directly using an [HTTP POST request][restdocs]. There are also client libraries created for C#, Go, Java, Node.js, PHP, Python, and Ruby. In order to keep this tutorial simple and as general as possible, it will make its own HTTP requests. Details on how to use the client libraries are available in the Cloud Natural Language API Docs.

## Making the HTTP request with Java

For simplicity, this example shows how to make an HTTP request using just the core Java libraries. This should be put in the `getResponse` method of the Magpie class.

First, create constants for the API key and URL. Be sure to put your API key in the place indicated.

```java
final String TARGET_URL =
					"https://language.googleapis.com/v1/documents:analyzeSentiment?";
final String API_KEY =
					"key=YOUR_API_KEY";
```

Next, create a URL object with the target URL and create a connection to that URL:

```java
URL serverUrl = new URL(TARGET_URL + API_KEY);
URLConnection urlConnection = serverUrl.openConnection();
HttpURLConnection httpConnection = (HttpURLConnection)urlConnection;
```

This will require the `java.net.HttpURLConnection`, `java.net.URL`, and `java.net.URLConnection` libraries be imported.

The URL constructor may throw a `MalformedURLException`. You can handle this with either a try/catch block or adding `throws MalformedURLException` to the method header and importing the exception. Different teachers may have different preferences; either works. Similarly, the `openConnection` may throw an `IOException` that should be handled before moving on. If you opt to throw the error, be sure to also handle it in the runner.

Set the method and Content-Type of the connection:

```java
httpConnection.setRequestMethod("POST");
httpConnection.setRequestProperty("Content-Type", "application/json");
```

And then prepare the connection to be written to to enable creation of the data portion of the request:

```java
httpConnection.setDoOutput(true);
```

Create a writer and use it to write the data portion of the request:

```java
BufferedWriter httpRequestBodyWriter = new BufferedWriter(new
				OutputStreamWriter(httpConnection.getOutputStream()));
httpRequestBodyWriter.write("{\"document\":  { \"type\": \"PLAIN_TEXT\", \"content\":\""
						+ statement + "\"}, \"encodingType\": \"UTF8\"}");
httpRequestBodyWriter.close();
```

This will require importing `java.io.BufferedWriter` and `java.io.OutputStreamWriter`. Notice the line being written is the same as the data provided to the API Explorer in [Part 0][magpie0].

Finally, make the request and get the response:

```java
httpConnection.getResponseMessage();
```

The returned data is sent in an input stream. Build a string containing it.

```java
String results = "";
if (httpConnection.getInputStream() != null)
{
  Scanner httpResponseScanner = new Scanner (httpConnection.getInputStream());
	while (httpResponseScanner.hasNext()) {
		String line = httpResponseScanner.nextLine();
		results += line;
	}
	httpResponseScanner.close();
}
```

Yes, you'll need to import `java.util.Scanner`.

Once you have the results in a single string, you can access parts of it to determine the score and potentially the magnitude. (Parsing the JSON is covered in the [next part of this tutorial][magpie2]). Recall, if there are multiple sentences, there will be multiple scores. A simple solution to get the first score is below.

```java
int psn = results.indexOf("\"score\":");
double score = 0.0;
if (psn >= 0)
{
	int bracePsn = results.indexOf('}', psn);  //  Find the closing brace
	String scoreStr = results.substring(psn+8, bracePsn).trim();
	score = Double.parseDouble(scoreStr);
}
```

You can then use the score in creating your response to the user. If you've done part 0, you should have ideas about what thresholds to use. Otherwise, work with the values for score to find reasonable values. You can also use them in conjunction with other clauses in determining the response. Now that you can tell the sentiment of the user, it's up to you to find creative ways to use it!

```java
String response = "";
if (score > 0.5) {
	response = "Wow, that sounds great!";
}
else if (score < -0.5)
{
	response = "Ugh, that's too bad";
}
else if (statement.indexOf("cats") >= 0) {...
```

## Summary

* If you do not want to use the Java client library, you can make an HTTP POST call the Cloud Natural Language API in a program.
* Making a POST call requires set the method and content type and writing the data section
* The results of the call come back in JSON format that can be concatenated into a single string. For simple cases, this text can just be searched to find the properties of interest.

## Next steps
To use the different features of the Cloud Natural Language API, see the following Community articles:

* [On Beyond Magpie: Part 2, Entity Analysis][magpie2]


[annotate]:https://apis-explorer.appspot.com/apis-explorer/#search/natural/language/v1/language.documents.annotateText
[annotateapi]:https://cloud.google.com/natural-language/docs/reference/rest/v1beta1/documents/annotateText
[console]:https://console.cloud.google.com/
[explorer]:https://apis-explorer.appspot.com/apis-explorer/#search/natural/language/v1/
[manager]:https://console.cloud.google.com/apis/
[magpie0]:https://cloud.google.com/community/tutorials/on-beyond-magpie0
[magpie2]:https://cloud.google.com/community/tutorials/on-beyond-magpie2
[nlp]:https://cloud.google.com/natural-language/
[restdocs]:https://cloud.google.com/natural-language/docs/reference/rest/

