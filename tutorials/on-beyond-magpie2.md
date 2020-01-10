---
title: On Beyond Magpie 2 - entity analysis
description: An introduction to the Cloud Natural Language API, aimed at Advanced Placement Computer Science classes who have worked on the Magpie lab, but suitable for most people starting with the Cloud Natural Language API. Demonstrates how to parse JSON results from the  Cloud Natural Language API.
author: Annie29
tags: Cloud Natural Language API, APCS, JSON, Magpie, education
date_published: 2017-03-28
---

The Advanced Placement Computer Science A program provides the [Magpie lab](http://media.collegeboard.com/digitalServices/pdf/ap/ap-compscia-magpie-lab-student-guide.pdf) for students to practice using basic control structures to parse user input as part of a chatbot. This tutorial is designed to be an additional enrichment exercise (typically used after the AP exam) to go beyond  basic parsing and instead use Google's [Cloud Natural Language API][nlp], a pretrained machine learning model that will do text analysis for the user. The lab demonstrates how to use the Cloud Natural Language API to extract entities from user input.

The major new skill covered in this lab is how to parse JSON results in Java.

This tutorial is written for an audience of CS teachers who are exposing their students to the Cloud Natural Language API, but should be usable by any interested individual.

## Prerequisites

If you've completed [On Beyond Magpie, Part 0][magpie0], you should have all of the prerequisites completed. Otherwise,

1. Create a project in the [Google Cloud Platform Console][console].
1. Enable billing for your project.
1. Ensure the Cloud Natural Language API is enabled by going to the [API manager][manager] from the main GCP menu.
1. Generate an API key for your project.

Sample code for a complete chatbot and full description of the steps involved in making a POST call in Java are included in [On Beyond Magpie: Part 1, Sentiment Analysis][magpie1].


## Accessing the API

The Cloud Natural Language API can be accessed directly using an [HTTP POST request][restdocs]. There are also client libraries created for C#, Go, Java, Node.js, PHP, Python, and Ruby. In order to keep this tutorial simple and as general as possible, it will make its own HTTP requests. Details on how to use the client libraries are available in the Cloud Natural Language API Docs.

## Making the HTTP request with Java

For simplicity, this example shows how to make an HTTP request using just the core Java libraries. This should be put in the `getResponse` method of the Magpie class. A full explanation of the code below is in [On Beyond Magpie: Part 1, Sentiment Analysis][magpie1].

The complete code to call the API and put the results in a string is below:

	final String TARGET_URL = "https://language.googleapis.com/v1/documents:analyzeEntities?";
	final String API_KEY = "key=your key";
	URL serverUrl = new URL(TARGET_URL + API_KEY);
	URLConnection urlConnection = serverUrl.openConnection();
	HttpURLConnection httpConnection = (HttpURLConnection) urlConnection;

	httpConnection.setRequestMethod("POST");
	httpConnection.setRequestProperty("Content-Type", "application/json");

	httpConnection.setDoOutput(true);
	BufferedWriter httpRequestBodyWriter = new BufferedWriter(
			new OutputStreamWriter(httpConnection.getOutputStream()));
	httpRequestBodyWriter.write("{\"document\":  { \"type\": \"PLAIN_TEXT\", \"content\":\""
							+ statement + "\"}, \"encodingType\": \"UTF8\"}");
	httpRequestBodyWriter.close();
	httpConnection.getResponseMessage();

	String results = "";

	if (httpConnection.getInputStream() != null) {

		Scanner httpResponseScanner = new Scanner(httpConnection.getInputStream());
		while (httpResponseScanner.hasNext()) {
			String line = httpResponseScanner.nextLine();
			results += line;
		}
		httpResponseScanner.close();
	}


### Parsing the JSON results

The results of the POST call are returned using JSON format. There are numerous libraries which will do JSON parsing in Java but currently there is no standard library. This tutorial will use the GSON library, available at [Github] (https://github.com/google/gson) and for [download as a jar file](https://repo1.maven.org/maven2/com/google/code/gson/gson/2.6.2/).

Once a string representing the JSON data is created, it can be sent to the GSON library, which will return an object that represents the data. You will need to create a class that represents the data you are interested in, based on the return types of the [Cloud Natural Language API](https://cloud.google.com/natural-language/docs/reference/rest/v1beta1/documents/analyzeEntities). This object is an instance of the class  `AnalyzeEntitiesResponse`, shown below. You will need to define this class in your `Magpie` class.

```java
public class AnalyzeEntitiesResponse {
	private Entity [] entities;
	public Entity [] getEntities () {
		return entities;
	}
}
```


Notice that even though there is another field in the response (the language), since this example doesn't need it, it does not have to be included in the class.

This example is concerned with entities though, so it needs to define a class that represents an entity:

```java
public class Entity {
	private String name;
	private String type;
		//  Currently type is one of UNKNOWN, PERSON, LOCATION, ORGANIZATION, EVENT, WORK_OF_ART, CONSUMER_GOOD, OTHER

	private Map<String, String> metadata;

	public String getName() {
		return name;
	}

	public String getType() {
		return type;
	}

	public Map<String, String> getMetadata() {
		return metadata;
	}
}
```

Additional information returned about an entity (such as mentions and salience) are not included since this example does not need them. Once the classes that represent the results you want are defined, you can create a `Gson` object and use it to parse the string you have created as shown below. In this example, it will just return a list of the entities in the user input.

```java
private List<String> getEntities (String jsonString) {
	List<String> result = new ArrayList<String>();
	Gson gson = new GsonBuilder().create();

	AnalyzeEntitiesResponse json = (AnalyzeEntitiesResponse)gson.fromJson(jsonString, AnalyzeEntitiesResponse.class);

	if (json != null)  {
			for (Entity entity:json.getEntities()) {
				result.add (entity.getName());
			}
		}
	return result;
}
```

At this point, you can call this method and use the results to have your chatbot respond to the entities in user statements. A simple response would be to react to the first entity it finds.

```java
List<String> entities = getEntities(results);

if (entities.size() > 0) {
	// Pick the first entity and ask about it
	response = "I've always been interested in " + entities.get(0)
			+ ". Can you tell me more about it?";
}
else if (statement.indexOf("cats") >= 0) { ...
```

## Going beyond the basics

While this tutorial just finds the first entity, there is so much more your chatbot can do. Some things to try out:
* Instead of selecting the first entity, select a random one.
* Prioritize the type of entities your chatbot will respond to. Perhaps look for any WORK_OF_ART first. If one isn't found, try EVENT, then LOCATION, etc..
* For entities which have Wikipedia links, learn more about the [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page) and include information from Wikipedia in your response.

## Summary

* You can use the Cloud Natural Language API to analyze the entities in a string.
* You'll need to provide a Java class (or classes) that represent the information you want from the JSON result of an API call.
* You can get the type of these entities and additional information like Wikipedia links if you want to make your chatbot more responsive.


[console]:https://console.cloud.google.com/
[magpie0]:https://cloud.google.com/community/tutorials/on-beyond-magpie0
[magpie1]:https://cloud.google.com/community/tutorials/on-beyond-magpie1
[manager]:https://console.cloud.google.com/apis/
[nlp]:https://cloud.google.com/natural-language/
[restdocs]:https://cloud.google.com/natural-language/docs/reference/rest/
