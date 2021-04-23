---
title: On Beyond Magpie 0 - Setup and API Exploration
description: An introduction to the Cloud Natural Language API, aimed at Advanced Placement Computer Science classes who have worked on the Magpie lab, but suitable for most people starting with the Cloud Natural Language API. Demonstrates how to access the Cloud Natural Language API interactively and create credentials for use with later tutorials in this sequence.
author: Annie29
tags: Cloud Natural Language API, APCS, REST, Magpie, education
date_published: 2017-03-28
---

Laurie White | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

The Advanced Placement Computer Science A program provides
the [Magpie lab](http://media.collegeboard.com/digitalServices/pdf/ap/ap-compscia-magpie-lab-student-guide.pdf) for students to practice using basic control structures to parse user input as part of a chatbot. This tutorial is designed to be an additional enrichment exercise (typically used after the AP exam) to go beyond  basic parsing and instead use [Google's Cloud Natural Language API][nlp], a pretrained machine learning model that will do text analysis for the user. The lab demonstrates how to use the Cloud Natural Language API to extend the Magpie lab.

This tutorial is written for an audience of CS teachers who are exposing their students to REST-ful APIs in general and the Cloud Natural Language API specifically, but should be usable by any interested party.

The NLP API provides a variety of functionalities that can be used in different ways:

* Sentiment analysis:  This is perhaps the easiest to add to Magpie: given text, the API will return its sentiment and the strength of that sentiment. The Magpie can then respond if a user's comments seem exceptionally positive or negative.
* Entity analysis: The API will analyze the text for known entities (like France, Paris,or Eiffel Tower) and provide links to appropriate Wikipedia articles. Make the Magpie exceptionally smart using the [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page) to find out much more about entities.
* Syntax analysis: Magpie does very simple syntax analysis. The Cloud Natural Language API does full analysis of sentences.

This exercise shows you how to prepare to use the Cloud Natural Language API for use in programs and illustrates how to introduce it to a class using web-based tools. If you are only going to use the web-based tools, you can skip the Prerequisites and Authentication sections.


## Prerequisites

1. Create a project in the [Cloud Console][console].
1. Enable billing for your project.
1. Ensure the Cloud Natural Language API is enabled by going to the [API manager][manager] from
the main Google Cloud menu.

## Authentication

Since there is a [charge to use the Cloud Natural Language API][pricing] although it's less
than one cent per text record (1,000 Unicode characters) and the first 5000 requests are free, programs that use
it must be authenticated. Read [the instructions for creating an API key][auth]. A single key can be used for your entire class, but be careful to delete it after the class has used it to ensure they don't use it for other purposes.


### Action

Generate an API key for your project.

## Accessing the API interactively

If you are not familiar with the Cloud Natural Language API, first examine its abilities using the interactive feature in the ["Try the API"][nlp] section of the overview. Notice it can extract entities, detect sentiment, and parse syntax.

### Entity Detection

While entity detection may seem to be a simple task, there's actually some significant processing going on. Try using the sentence "The Eiffel Tower is one of many highlights in Paris, France." and examine the entities it extracts. These should include "Paris" and "France." While this may seem obvious, change the sentence to "The Eiffel Tower is one of many highlights in Paris, Texas." The API no longer finds the entity "Paris" (the city in France). Instead, it just finds the city "Paris, Texas."

### Syntax analysis
Syntax analysis can handle some very complicated sentences. Try something like the first sentence of [Alice in Wonderland][alice]:
>Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, ‘and what is the use of a book,’ thought Alice ‘without pictures or conversations?’

Not only does it recognize that "was" is a verb, it returns the base verb "be" and the mood, number, person, and tense of the verb.

### Sentiment analysis
Sentiment analysis returns a score from -1.0 (for negative) to 1.0 (for positive) sentiment. The magnitude is the strength of the sentiment. If the text consists of more than one sentence, there will be a score for the entire text and each individual sentence. Encourage students to try to create sentences with high magnitude.

## Accessing the API with the API Explorer

The interactive feature of the WWW page does not show the JSON value returned by the API. To see the returned JSON, use the [API Explorer][explorer]. You can select to analyze any one item (entities, sentiment, or syntax) or all three ([annotateText][annotate]).

This provides a way to introduce students to HTTP calls. The details of the call parameters can be found [online][annotateapi]
In the API explorer, the context menu will show the properties that can be used. As a minimum, in the `Request` body:

* Add a `document` property. Within the `document` property.
  * Add a `type` property with the value  `PLAIN_TEXT`.
  * Add a `content` property with the text to be examined.
* Add an `encodingType` property with the value `UTF8`.
* Add a `features` property. Within the `features` property.
  * Add at least one of the properties `extractDocumentSentiment`, `extractEntities` and `extractSyntax` and check the box to set the property to true.

Use the `Execute` button to execute the API call.

The `Response` data will appear below the call in JSON format.

## Summary

* If you want to use the Cloud Natural Language API in a program, you will need to:

  * Create a Google Cloud project.
  * Enable the API
  * Arrange for authentication (in this case using an API key).

* From the web interface, you can use the Cloud Natural Language API to analyze sentiment, extract entities, and parse the syntax of text.
* You can also call the Cloud Natural Language API from the API Explorer.

## Next steps

To use the different features of the Cloud Natural Language, see the following Community articles:
* [On Beyond Magpie: Part 1, Sentiment Analysis][magpie1]
* [On Beyond Magpie: Part 2, Entity Analysis][magpie2]


[alice]:https://www.gutenberg.org/files/11/11-h/11-h.htm
[annotate]:https://apis-explorer.appspot.com/apis-explorer/#search/natural/language/v1/language.documents.annotateText
[annotateapi]:https://cloud.google.com/natural-language/docs/reference/rest/v1/documents/annotateText
[auth]:https://cloud.google.com/natural-language/docs/common/auth
[console]:https://console.cloud.google.com/
[explorer]:https://apis-explorer.appspot.com/apis-explorer/#search/natural/language/v1/
[magpie1]:https://cloud.google.com/community/tutorials/on-beyond-magpie1
[magpie2]:https://cloud.google.com/community/tutorials/on-beyond-magpie2
[manager]:https://console.cloud.google.com/apis/
[nlp]:https://cloud.google.com/natural-language/
[pricing]: https://cloud.google.com/natural-language/pricing


