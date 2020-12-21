---
title: How to build a conversational app using Cloud Machine Learning APIs - part 1 of 3
description: Overview, architecture, API.AI intents and API.AI contexts.
author: PokerChang
tags: Cloud Functions, Dialogflow, API.AI, Webhooks, Localization, Chatbot, Machine Learning API, Translation, Vision, Speech
date_published: 2018-06-19
---

Chang Luo | Software Engineer | Google 

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

For consumers, conversational apps (such as chatbots) are among the most visible examples of machine learning in action. For developers, building a 
conversational app is instructive for understanding the value that machine-learning APIs bring to the process of creating completely new user experiences.

In this three-part post, we will show you how to build an example [tour guide](https://youtu.be/qDAP3ZFjO48) app for Apple iOS that can see, listen, talk and 
translate via [API.AI](https://api.ai/) (a developer platform for creating conversational experiences) and
[Google Cloud ML APIs for Speech, Vision and Translate](https://cloud.google.com/products/machine-learning/). You will also see how easy it is to support 
multiple languages on these platforms.

[![English Demo](https://img.youtube.com/vi/qDAP3ZFjO48/0.jpg)](https://youtu.be/qDAP3ZFjO48)

The three parts will focus on the following topics:

Part 1

*   Overview
*   Architecture
*   API.AI intents
*   API.AI contexts

[Part 2]

*   API.AI webhook with [Cloud Functions](https://cloud.google.com/functions/)
*   [Cloud Vision API](https://cloud.google.com/vision/)
*   [Cloud Speech API](https://cloud.google.com/speech/)
*   [Cloud Translation API](https://cloud.google.com/translate/)
*   Support for multiple languages

[Part 3]

*   Support the Google Assistant through Actions on Google integration

## Architecture

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot/chatbots-8.png "Architecture")

## Using API.AI

API.AI is a platform for building natural and rich conversational experiences. For our example, it will handle all core conversation flows in the tour guide app.
(Note that API.AI provides great [documentation and a sample app](https://github.com/api-ai/apiai-ios-client) for its iOS SDK. SDKs for
[other platforms](https://docs.api.ai/docs/sdks) are also available, so you could easily extend this tour guide app to support Android.)

### Create agent

The first step is to create a **Tour Guide Agent**.

### Create intents

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot/chatbots-3.png "Create Intents Screenshot")

To engage users in a conversation, we first need to understand what users are saying to the agent, and we do that with intents and entities. Intents map what 
your users say to what your conversational experience should do. Entities extract parameter values from user queries.

Each intent contains a set of examples of user input and the desired automated response. To do that, you need to predict what users will say to open the conversation, and then enter those phrases in the "Add user expression" box. This list doesn't need to be comprehensive. API.AI uses Machine Learning to train the agent to understand more variations of these examples. Later on, you can train the API.AI agent to understand more variations. For example, go to the Default Welcome Intent and add some user expressions "how are you", "hello", "hi" to open the conversation.

The next step after that is to add some more text responses.

![Default Welcome Intent Screenshot](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot/chatbots-6.png "Default Welcome Intent Screenshot")

Next, it's time to work on contexts.

### Contexts

_[Contexts](https://docs.api.ai/docs/concept-contexts)_ represent the current context of a user's request. They are helpful for differentiating phrases that may be vague or have different meanings depending on the user's preferences or geographic location, the current page in an app, or the topic of conversation. Let's look at an example.

_User: Where am I?_

_Bot: Please upload a nearby picture and I can help find out where you are._

_[User uploads a picture of Golden Gate Bridge.]_

_Bot: You are near Golden Gate Bridge._

_User: How much is the ticket?_

_Bot: Golden Gate Bridge is free to visit._

_User: When does it close today?_

_Bot: Golden Gate Bridge is open 24 hours a day, 7 days a week._

_User: How do I get there?_

_[Bot shows a map to Golden Gate Bridge.]_

In the above conversation, when the user asks "How much is the ticket?" and "When does it close today?" or "How do I get there?", the bot understands that the context is around Golden Gate Bridge.

The next thing to do is to weave intents and contexts together. For our example, each box in the diagram below is an intent and a context; the arrows indicate the relationships between them.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot/chatbots-7.png "Contexts Relationship")

### Output contexts

Contexts are tied to user sessions (a session ID that you pass in API calls). If a user expression is matched to an intent, the intent can then set an output 
context to be shared by this expression in the future. You can also add a context when you send the user request to your API.AI agent. In our example, the 
`where` intent sets the `where` output context so that _location_ intent will be matched in the future.

### Input contexts

Input contexts limit intents to be matched only when certain contexts are set. In our example, location's input context is set to where. The `location` intent is matched only when we are under `where` context.

Here are the steps to generate these intents and contexts:

1.  Create `where` intent and add `where` output context. This is the root in the context tree and has no input context.

    ![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot/chatbots-2.png "Contexts Screenshot")
    
1.  Create `location` intent.
        1.  Add `where` input context.
        1.  Reset `where` output context and add `location` output context.
	
    **Note**: In our tour guide app, the input context of `location` is `where`. When the `location` intent is detected, the `where` context needs to be reset so
    that any subsequent conversation won't trigger this context again. This is done by setting the lifespan of the output context `where` to 0 request. By 
    default, a context has a lifespan of 5 requests or 10 minutes.
    
    ![alt_text](https://storage.googleapis.com/gcp-community/tutorials/chatbots-5.png "Location Screenshot")
    
1. Create `ticket` intent.
	1. Add `location` input context.
	1. Add `location` output `context` so that `hours` and `map` intents can continue to use the `location` context as input context.

You can pass the parameter from the input context with the format of `#context.parameter`; e.g., pass the location string from intent `inquiry-where-location` to `inquiry.where.location.ticket` in the format `#inquiry-where-location.location.`

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot/chatbots-1.png "Ticket Screenshot")

Finally, create `hours` and `map` intents similar to `ticket` intent.

**Next time**

In [Part 2], we'll cover how to use [Webhook](https://docs.api.ai/docs/webhook) integrations in API.AI to pass information from a matched intent into a [Cloud Functions](https://cloud.google.com/functions/) web service and then get a result. Finally, we'll cover how to integrate Cloud Vision/Speech/Translation API, including support for Chinese language.

In [Part 3], we'll cover how to support the Google Assistant via Actions on Google integration.

You can download the [source code](https://github.com/google/ios-chatbot) from GitHub.

[Part 2]: https://cloud.google.com/community/tutorials/ios-chatbot-part-2/
[Part 3]: https://cloud.google.com/community/tutorials/ios-chatbot-part-3/
