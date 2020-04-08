---
title: How to build a conversational app using Cloud Machine Learning APIs Part 2 of 3
description: We'll discuss an advanced API.AI topic, namely webhook with Cloud Functions. We'll also show you how to use Cloud Machine Learning APIs (Vision, Speech and Translation) and how to support a second language.
author: PokerChang
tags: Cloud Functions, Dialogflow, API.AI, Webhooks, Localization, Chatbot, Machine Learning API, Translation, Vision, Speech
date_published: 2018-06-19
---

Author: [Chang Luo](https://www.linkedin.com/in/changluo)

In [Part 1](https://cloud.google.com/community/tutorials/ios-chatbot) of this series, we gave you an overview of what a conversational tour guide iOS app might look like built on Cloud Machine Learning APIs and API.AI. We also demonstrated how to create API.AI intents and contexts. In part 2, we'll discuss an advanced API.AI topic — webhook with Cloud Functions. We'll also show you how to use Cloud Machine Learning APIs (Vision, Speech, and Translation) and how to support a second language.


# Webhooks via Cloud Functions

In API.AI, [webhook](https://docs.api.ai/docs/webhook) integrations allow you to pass information from a matched intent into a web service and get a result from it. Read on to learn how to request parade info from Cloud Functions.



1.  Go to [Google Cloud Platform Console](console.cloud.google.com). Log in with your own account and create a new project.

1. Once you've created a new project, navigate to that project.

1. Enable the Cloud Functions API.
![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-8.png "Enable Billing Screenshot")
1. Create a function. For the purposes of this guide, we'll call the function "parades".

1. Select the "HTTP" trigger option, then select "inline" editor.
![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-10.png "Cloud Function Screenshot")
Don't forget to specify the function to execute to "parades".
1. You'll also need to create a "stage bucket". Click on "browse" —  you'll see the browser, but no buckets will exist yet.
![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-4.png "Bucket Screenshot")
    1. Click on the "+" button to create the bucket.
    1. Specify a unique name for the bucket (you can use your project name, for instance), select "regional" storage, and keep the default region (us-central1).
    1.  Click back on the "select" button in the previous window.
    1.  Click the "create" button to create the function.
The function will be created and deployed:
![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-5.png "Cloud Function Deploy Screenshot")
1. Click the "parades" function line. In the **Source** tab, you'll see the sources.

Now it's time to code our function! We'll need two files: the `index.js` file will contain the JavaScript / Node.JS logic, and the `package.json` file contains the Node package definition, including the dependencies we'll need in our function.

Here's our `package.json` file. This is dependent on the `actions-on-google` NPM module to ease the integration with API.AI and the Actions on Google platform that allows you to extend the Google Assistant with your own extensions (usable from Google Home):


```json
{
  "name": "parades",
  "version": "0.0.1",
  "main": "index.js",
  "dependencies": {
    "actions-on-google": "^1.1.1"
  }
}
```


In the `index.js` file, here's our code:


```js
const ApiAiApp = require('actions-on-google').ApiAiApp;
function parade(app) {
  app.ask(`Chinese New Year Parade in Chinatown from 6pm to 9pm.`);
}
exports.parades = function(request, response) {
    var app = new ApiAiApp({request: request, response: response});
    var actionMap = new Map();
    actionMap.set("inquiry.parades", parade);
    app.handleRequest(actionMap);
};
```


In the code snippet above:

1.  We require the actions-on-google NPM module.
1.  We use the `ask()` method to let the assistant send a result back to the user.
1.  We export a function where we're using the actions-on-google module's `ApiAiApp` class to handle the incoming request.
1.  We create a map that maps "intents" from API.AI to a JavaScript function.
1.  Then, we call the `handleRequest()` to handle the request.
1.  Once done, don't forget to click the "create" function button. It will deploy the function in the cloud.

There is a subtle difference between [`tell()`](https://developers.google.com/actions/reference/nodejs/ActionsSdkApp#tell) 
and [`ask()`](https://developers.google.com/actions/reference/nodejs/ActionsSdkApp#ask) APIs. `tell()` will end the 
conversation and close the mic, while `ask()` will not. This difference doesn't matter for API.AI projects like the one we 
demonstrate here in [Part 1](https://cloud.google.com/community/tutorials/ios-chatbot) and Part 2 of this series. When we 
integrate Actions on Google in Part 3, we'll explain this difference in more detail.

As shown below, the **Testing** tab invokes your function, the **General** tab shows statistics, and the **Trigger** tab reveals the HTTP URL created for your function:


![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-7.png "Cloud Function Trigger Screenshot")


Your final step is to go to the API.AI console, then click the **Fulfillment** tab. Enable webhook and paste the URL above into the URL field.


![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-3.png "Fullfill Screenshot")

With API.AI, we've built a chatbot that can converse with a human by text. Next, let's give the bot "ears" to listen with Cloud Speech API, "eyes" to see with Cloud Vision API, a "mouth" to talk with the iOS text-to-speech SDK, and "brains" for translating languages with Cloud Translation API.


## Using Cloud Speech API


Cloud Speech API includes an iOS [sample](https://github.com/GoogleCloudPlatform/ios-docs-samples/tree/master/speech/Objective-C) app. It's quite straightforward to integrate the [gRPC non-streaming sample app](https://github.com/GoogleCloudPlatform/ios-docs-samples/tree/master/speech/Objective-C/Speech-gRPC-Nonstreaming) into our chatbot app. You'll need to acquire an [API key](https://cloud.google.com/storage/docs/json_api/v1/how-tos/authorizing#APIKey) from Google Cloud Console and replace this [line](https://github.com/GoogleCloudPlatform/ios-docs-samples/blob/master/speech/Objective-C/Speech-gRPC-Nonstreaming/Speech/SpeechRecognitionService.m#L23) in `SpeechRecognitionService.m` with your API key.

```
#define API_KEY @"YOUR_API_KEY"
```

## Landmark Detection

Follow this [example](https://github.com/GoogleCloudPlatform/cloud-vision/tree/master/ios) to use Cloud Vision API on iOS. You'll need to replace the label and face detection with landmark detection as shown below.



```m
NSDictionary *paramsDictionary =
@{@"requests":@[
      @{@"image":
          @{@"content":binaryImageData},
        @"features":@[
            @{@"type":@"LANDMARK_DETECTION", @"maxResults":@1}]}]};
```


You can use the same API key you used for Cloud Speech API.


## Text to Speech

iOS 7+ has a built-in text-to-speech SDK, [`AVSpeechSynthesizer`](https://developer.apple.com/reference/avfoundation/avspeechsynthesizer?language=objc). The code below is all you need to convert text to speech.


```m
#import <AVFoundation/AVFoundation.h>
AVSpeechUtterance *utterance = [[AVSpeechUtterance alloc] initWithString:message];
AVSpeechSynthesizer *synthesizer = [[AVSpeechSynthesizer alloc] init];
[synthesizer speakUtterance:utterance];
```



## Supporting Multiple Languages



[![Chinese Demo](https://img.youtube.com/vi/Oy4oNNd1aGw/0.jpg)](https://youtu.be/Oy4oNNd1aGw)

Supporting additional languages in Cloud Speech API is a one-line change on the iOS client side. (Currently, there is no support for mixed languages.) For [Chinese](https://youtu.be/Oy4oNNd1aGw), replace [this](https://github.com/google/ios-chatbot/blob/master/ChatBot/ChatBot/SpeechRecognitionService.m#L73) line in [SpeechRecognitionService.m](https://github.com/google/ios-chatbot/blob/master/ChatBot/ChatBot/SpeechRecognitionService.m):


```m
recognitionConfig.languageCode = @"en-US";
```


with


```m
recognitionConfig.languageCode = @"zh-Hans";
```


To support additional text-to-speech languages, add this line to the code:


```m
#import <AVFoundation/AVFoundation.h>
AVSpeechUtterance *utterance = [[AVSpeechUtterance alloc] initWithString:message];
utterance.voice = [AVSpeechSynthesisVoice voiceWithLanguage:@"zh-Hans"];
AVSpeechSynthesizer *synthesizer = [[AVSpeechSynthesizer alloc] init];
[synthesizer speakUtterance:utterance];
```


Both Cloud Speech API and Apple's [AVSpeechSynthesisVoice](https://developer.apple.com/documentation/avfoundation/avspeechsynthesisvoice/1619698-language?language=objc) support [BCP-47 language code](https://tools.ietf.org/html/bcp47).

Cloud Vision API landmark detection currently only supports English, so you'll need to use the [Cloud Translation API](https://cloud.google.com/translate/) to translate to your desired language after receiving the English-language landmark description. (You would use Cloud Translation API similarly to Cloud Vision and Speech APIs.)

On the API.AI side, you'll need to create a new agent and [set its language to Chinese](https://api.ai/docs/agents#agent-settings). One agent can support only one language. If you try to use the same agent for a second language, machine learning won't work for that language.



![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-6.png "Chinese Screenshot")


You'll also need to create all intents and entities in Chinese.


![alt_text](https://storage.googleapis.com/gcp-community/tutorials/ios-chatbot-part-2/conversational-app-12.png "Chinese Screenshot")



---


And you're done! You've just built a simple "tour guide" chatbot that supports English and Chinese.

**Next time**

We hope this example has demonstrated how simple it is to build an app powered by machine learning. For more getting-started info, you might also want to try:



*   [Cloud Speech API Quickstart](https://cloud.google.com/speech/docs/getting-started)
*   [Cloud Vision API Quickstart](https://cloud.google.com/vision/docs/quickstart)
*   [Cloud Translation API Quickstart](https://cloud.google.com/translate/docs/getting-started)
*   [API.AI Quickstart](https://api.ai/docs/getting-started/basics)

You can download the [source code](https://github.com/google/ios-chatbot) from Github.

In [Part 3](https://cloud.google.com/community/tutorials/ios-chatbot-part-3/), we'll cover how to build this app on the Google Assistant with Actions on Google integration.
