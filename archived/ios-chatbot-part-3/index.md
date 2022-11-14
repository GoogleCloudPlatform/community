---
title: How to build a conversational app using Cloud Machine Learning APIs - part 3 of 3
description: How to extend this app to the Google Assistant-supported devices, such as Google Home, eligible Android phones and iPhones, and Android Wear.
author: PokerChang
tags: Cloud Functions, Dialogflow, API.AI, Webhooks, Localization, Chatbot, Machine Learning API, Translation, Vision, Speech
date_published: 2018-06-19
---

Chang Luo | Software Engineer | Google 

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In [Part 1] and [Part 2] of this series, we showed you how to build a conversational tour guide app with API.AI and Google Cloud Machine Learning APIs. In this final part, you'll learn how to extend this app to the Google Assistant-supported devices (Google Home, eligible Android phones and iPhones, and Android Wear). And we'll build this on top of the existing API.AI agent created in parts 1 and 2.

[![The Google Assistant / Google Home Demo](https://img.youtube.com/vi/_x5rlkpZiyc/0.jpg)](https://youtu.be/_x5rlkpZiyc)

## New intents for Actions on Google

In [Part 1], we discussed the app's input and output context relationships.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-3.png "Contexts without the Assistant")

The `where` context requires the user to upload an image, which is not supported by the Google Assistant. We can modify the context relationship as below.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-8.png "Contexts with the Assistant")

We will add three new intents, `hours-no-context, ticket-no-context` and `map-no-context`. Each intent will set `location` as the output context so that other intents can use the _location_ as an input parameter.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-5.png "Contexts Screenshot")

### Enable Actions on Google integration

Now we'll enable Actions on Google to support the Google Assistant.

1. Open your API.AI console. Under the **Integrations** Tab, turn on the _Actions on Google_ integration.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-1.png "Enable Actions on Google Integration")

2. In the popup dialog under **Additional triggering intents**, add all intents  you want to support on the Google Assistant. The system will automatically set the **Welcome Intent** to **Default Welcome Intent**. You can also click **SETTINGS** under Actions on Google to bring up this settings dialog in the future. Note that the _inquiry.where_ intent requires uploading an image and won't work on the Google Assistant, so you should not  add that intent to the triggering intents list.

3. After you're done adding all the intents that we want to support on Google on Actions (for example, `hours-no-context` intent) to the additional triggering intents list, click **UPDATE DRAFT** on the bottom. It will generate a green box. Click **VIEW** to go to the Actions on Google Web Simulator.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-4.png "Actions on Google Intents")

If this is your first time on Actions on Google console, it will prompt you to turn on **Device Information** and **Voice & Audio Activity** on your **Activity controls** center.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-2.png "Actions on Google Simulator")

By default these settings are off. If you already turned them on, you won't see the prompt.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-7.png "Device Information and Voice & Audio Activity Screenshot")

4. Go back to the simulator after turning on these two settings. Now we are ready to test the integration on the simulator! Start by typing or saying "Talk to my test app". The simulator will respond with the texts from the **Default Welcome Intent**. Afterward, you can test the app as if you were in the API.AI test console.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-3/conversational-app-p3-9.png "Actions on Google Test Console")

### Difference between `tell()` and `ask()` APIs

As we mentioned in Part 2, there is a subtle difference between [`tell()`](https://developers.google.com/actions/reference/nodejs/ActionsSdkApp#tell) and [`ask()`](https://developers.google.com/actions/reference/nodejs/ActionsSdkApp#ask) APIs when we implement the Cloud Function with the Actions on Google SDK. This doesn't make much of a difference in Part 1 and Part 2, but it does in Part 3 when we integrate Actions on Google. `tell()` will end the conversation and close the mic, while `ask()` will keep the conversation open and wait for the next user input.

You can test out the difference in the simulator. If you use `tell()` in the Cloud Functions, you'll need to  say "talk to my test app" again once you've triggered the intents with the Cloud Functions webhook such as the inquiry.parades intent "Are there any parades today?". If you use `ask()`, you will still be in the test app conversation and won't need to say "talk to my test app" again.

## Next steps

We hope this example demonstrates how to build a simple app powered by machine learning. For more getting started info, you might also want to try:

*   [Cloud Speech API Quickstart](https://cloud.google.com/speech/docs/getting-started)
*   [Cloud Vision API Quickstart](https://cloud.google.com/vision/docs/quickstart)
*   [Cloud Translation API Quickstart](https://cloud.google.com/translate/docs/getting-started)
*   [API.AI Quickstart](https://api.ai/docs/getting-started/basics)

You can download the [source code](https://github.com/google/ios-chatbot) from GitHub.

[Part 1]: https://cloud.google.com/community/tutorials/ios-chatbot/index.html
[Part 2]: https://cloud.google.com/community/tutorials/ios-chatbot-part-2/

