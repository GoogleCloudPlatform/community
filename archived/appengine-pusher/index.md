---
title: Using Pusher on Google App Engine
description: Learn how to use Pusher in place of the deprecated Channels API on App Engine standard Java 7 environment.
author: jabubake
tags: App Engine, Pusher, Channels API, Java
date_published: 2017-08-09
---

Jisha Abubaker | Developer Relations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to use [Pusher](https://pusher.com) on [Google App Engine](/appengine/docs/standard/java/).
Pusher is a hosted API for sending real-time, bi-directional messages through WebSockets to apps and
other internet-connected devices.

Pusher's real-time functionality is useful for applications that send information in real time,
such as collaborative applications, multi-player games, and chat rooms.

Using Pusher is a better choice than polling in situations where updates can't be predicted or
scripted, such as when relaying information between human users, or when events aren't generated
systematically.

Using WebSockets, Pusher is able to deliver server-side events to clients.
Pusher also offers REST API-based, server-side SDKs to enable sending events from a server
to a public or secured channel

In this tutorial you’ll learn how to complete the following tasks on the server:
-  Set up your server to use the Pusher service
-  Authenticate subscriptions to secure channels
-  Send messages over the channel

You'll also learn how to complete the following tasks in the web browser:
-  Set up your client to use the Pusher service
-  Subscribe to Pusher events
-  Subscribe to channels
-  Send messages to the server so they can be passed on to remote clients.

## Before you begin

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  Install the [Cloud SDK](/sdk/) and run:

		    gcloud init

1.  If this is your first time creating an App Engine application, run the following command
	  to create a new application:

        gcloud app create

The following sections walk you through setting up Pusher.

## Setting up a Pusher account

To set up a Pusher account, perform these steps:

1. [Create a Pusher account](https://pusher.com/signup).
1. Once signed in, you are directed to a [dashboard](https://dashboard.pusher.com/).
   The dashboard provides a convenient way to retrieve application settings, view errors
   and a console to debug calls to your application. From the dashboard's left panel,
   click Your apps to create a new application. Copy the cluster, application ID, key,
   and secret for later use
1. Update [appengine-web.xml](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-pusher/java/src/main/webapp/WEB-INF/appengine-web.xml) with your Pusher
   account credentials.

## Pusher SDKs

Pusher provides a [range of libraries in different languages](https://pusher.com/docs/libraries):

- Pusher's REST SDKs provide the ability to authenticate clients and publish HTTP events from your server.
- Pusher's WebSocket SDKs handle subscription.

## Channels

A [channel](https://pusher.com/docs/client_api_guide/client_channels) is automatically created
when an application publishes or subscribes to the channel by name.
They do not need to be explicitly created or deleted.

There are three types of channels:

- **Public**: Anyone can join the channel without authentication using the channel name
- **Private**: Server-side authentication is enforced, channel names must be prefixed with `private-`
- **Presence**: Server-side authentication is enforced, channel names must be prefixed with `presence-`,
   and all members can view who have connected/disconnected from the channel.

## Events

An [Event](https://pusher.com/docs/client_api_guide/client_events) is a  message with a named type.
Custom event handlers can be attached to a given event type.
This allows for efficient event routing in the clients.
**Note**: A subscriber will receive all messages published over a channel.

Events may be triggered by the user or Pusher.
In case of Pusher-triggered events on a channel, the event name is
prefixed with `pusher:`, such as `pusher:subscription-succeeded`.

## Chat application

The sample application demonstrates presence channels in Pusher for a chat application.
View complete source code [here](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/appengine-pusher/java).

The [Java server-side SDK](https://github.com/pusher/pusher-http-java) is used for authorizing
Pusher subscriptions and publishing events to the channel, and the
[JavaScript WebSocket SDK](https://github.com/pusher/pusher-js) is used to
subscribe to the events.

All users subscribed to the channel receive updates when users connect or disconnect from the channel.

## Using Pusher on your server

The server-side REST SDK is used to initialize a Pusher instance,
authorize secure presence channels, and provide clients an endpoint to trigger events.

### Connecting to Pusher

The following code provides examples of initializing and connecting to Pusher.
Use the credentials from the application you created to initialize and connect to Pusher,
as shown in this example.

**Note**: It is important to provide the cluster information if not using the default `mt1` (`us-east-1`) cluster.
You can encrypt messages sent over Pusher.

[embedmd]:# (java/src/main/java/com/example/appengine/pusher/PusherService.java /public abstract/ $)
```java
public abstract class PusherService {

  public static final String APP_KEY = System.getenv("PUSHER_APP_KEY");
  public static final String CLUSTER = System.getenv("PUSHER_CLUSTER");

  private static final String APP_ID = System.getenv("PUSHER_APP_ID");
  private static final String APP_SECRET = System.getenv("PUSHER_APP_SECRET");

  private static Pusher instance;

  static Pusher getDefaultInstance() {
	if (instance != null) {
	  return instance;
	} // Instantiate a pusher
	Pusher pusher = new Pusher(APP_ID, APP_KEY, APP_SECRET);
	pusher.setCluster(CLUSTER); // required, if not default mt1 (us-east-1)
	pusher.setEncrypted(true); // optional, ensure subscriber also matches these settings
	instance = pusher;
	return pusher;
  }
}
```

### Authorize client subscriptions for secure channels

Clients connecting to private or presence channels require server-side authentication.
The authentication endpoint can be implemented in your server as shown in this example.
The REST SDK provides methods to retrieve the required authentication JSON.

**Note**: Private channels do not require user information to be provided as part of the authentication.
To learn more about authentication in Pusher, refer to Pusher's
[Authenticating users](https://pusher.com/docs/authenticating_users) documentation.

[embedmd]:# (java/src/main/java/com/example/appengine/pusher/AuthorizeServlet.java /public class/ $)
```java
public class AuthorizeServlet extends HttpServlet {

  @Override
  public void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {

	// Instantiate a pusher connection
	Pusher pusher = PusherService.getDefaultInstance();
	// Get current logged in user credentials
	User user = UserServiceFactory.getUserService().getCurrentUser();

	// redirect to homepage if user is not authorized
	if (user == null) {
	  response.sendRedirect("/");
	  return;
	}
	String currentUserId = user.getUserId();
	String displayName = user.getNickname().replaceFirst("@.*", "");

	String query = CharStreams.toString(request.getReader());
	// socket_id, channel_name parameters are automatically set in the POST body of the request
	// eg.socket_id=1232.12&channel_name=presence-my-channel
	Map<String, String> data = splitQuery(query);
	String socketId = data.get("socket_id");
	String channelId = data.get("channel_name");

	// Presence channels (presence-*) require user identification for authentication
	Map<String, String> userInfo = new HashMap<>();
	userInfo.put("displayName", displayName);

	// Inject custom authentication code for your application here to allow/deny current request

	String auth =
		pusher.authenticate(socketId, channelId, new PresenceUser(currentUserId, userInfo));
	// if successful, returns authorization in the format
	//    {
	//      "auth":"49e26cb8e9dde3dfc009:a8cf1d3deefbb1bdc6a9d1547640d49d94b4b512320e2597c257a740edd1788f",
	//      "channel_data":"{\"user_id\":\"23423435252\",\"user_info\":{\"displayName\":\"John Doe\"}}"
	//    }

	response.getWriter().append(auth);
  }

  private static Map<String, String> splitQuery(String query) throws UnsupportedEncodingException {
	Map<String, String> query_pairs = new HashMap<>();
	String[] pairs = query.split("&");
	for (String pair : pairs) {
	  int idx = pair.indexOf("=");
	  query_pairs.put(
		  URLDecoder.decode(pair.substring(0, idx), "UTF-8"),
		  URLDecoder.decode(pair.substring(idx + 1), "UTF-8"));
	}
	return query_pairs;
  }
}
```

### Send messages over a channel

Authenticated clients can submit messages to the channel over HTTP using a server-side endpoint
as shown in the following example.

The sender can be [excluded](https://pusher.com/docs/server_api_guide/server_excluding_recipients)
from receiving the broadcast message by passing in its own socket ID when triggering an event.
Individual messages are limited to 10KB in size.

For more on publishing messages to multiple channels or batching multiple messages,
refer to Pusher's
[Publishing events](https://pusher.com/docs/server_api_guide/interact_rest_api#publishing-events)
documentation.

[embedmd]:# (java/src/main/java/com/example/appengine/pusher/SendMessageServlet.java /public class/ $)
```java
public class SendMessageServlet extends HttpServlet {

  private Gson gson = new GsonBuilder().create();
  private TypeReference<Map<String, String>> typeReference =
	  new TypeReference<Map<String, String>>() {};

  @Override
  public void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
	// Parse POST request body received in the format:
	// [{"message": "my-message", "socket_id": "1232.24", "channel": "presence-my-channel"}]

	String body = CharStreams.readLines(request.getReader()).toString();
	String json = body.replaceFirst("^\\[", "").replaceFirst("\\]$", "");
	Map<String, String> data = gson.fromJson(json, typeReference.getType());
	String message = data.get("message");
	String socketId = data.get("socket_id");
	String channelId = data.get("channel_id");

	User user = UserServiceFactory.getUserService().getCurrentUser();
	// User email prefix as display name for currently authenticated user
	String displayName = user.getNickname().replaceFirst("@.*", "");

	// Create a message including the user email prefix to display in the chat window
	String taggedMessage = "<strong><" + displayName + "></strong> " + message;
	Map<String, String> messageData = new HashMap<>();
	messageData.put("message", taggedMessage);

	// Send a message over the Pusher channel (maximum size of a message is 10KB)
	Result result =
		PusherService.getDefaultInstance()
			.trigger(
				channelId,
				"new_message", // name of event
				messageData,
				socketId); // (Optional) Use client socket_id to exclude the sender from receiving the message

	// result.getStatus() == SUCCESS indicates successful transmission
	messageData.put("status", result.getStatus().name());

	response.getWriter().println(gson.toJson(messageData));
  }
}
```

## Using Pusher on your client

The following sections explain how to subscribe to Pusher channels on your client using the
JavaScript Websocket SDK.

### Connecting to Pusher

Client connections require an application key. If the client is subscribing
to private or presence channels, a server-side authentication endpoint must be provided as well.
The client attempts to use `/pusher/auth` path for the endpoint if one is not explicitly provided.

The following example illustrates how to instantiate a Pusher connection using a custom authentication
endpoint. For more information about connections, refer to Pusher's
[Connection](https://pusher.com/docs/client_api_guide/client_connect) documentation.

[embedmd]:# (java/src/main/webapp/WEB-INF/view/chat.jsp /\/\/ Connect to Pusher/ /}\);/)
```jsp
// Connect to Pusher with auth endpoint on your server for private/presence channels
	// (default auth endpoint : /pusher/auth)
	var pusher = new Pusher('<%= PusherService.APP_KEY %>', {
		cluster: '<%= PusherService.CLUSTER %>',
		authEndpoint: '/authorize',
		encrypted: true
	});
```

### Subscribe to a channel

A client can subscribe to multiple channels. A subscription to a private or presence channel auto-triggers the
authentication endpoint.

The following example illustrates subscribing to a channel:

[embedmd]:# (java/src/main/webapp/WEB-INF/view/chat.jsp /\/\/ subscribe to the chat room/ /\);/)
```jsp
// Subscribe to the chat room presence channel, eg. "presence-my-room"
	var channel = pusher.subscribe(channel_name);
```

### Bind to Pusher events

On subscription success/error, Pusher sends events that a client can easily attach
to an event handler.

In the case of presence channels, Pusher sends additional events when a user connects
or disconnects from the channel.

The following code snippets show to bind event handlers to Pusher events:

[embedmd]:# (java/src/main/webapp/WEB-INF/view/chat.jsp /\/\/ bind to successful Pusher connection/ /}\);\n\n/)
```js
// bind to successful Pusher connection
pusher.connection.bind('connected', function () {

	// show chat window once logged in and successfully connected
	$('#chat_widget_main_container').show();
	// ...
	// bind to successful subscription
	channel.bind('pusher:subscription_succeeded', function (members) {
		// receive list of members on this channel
		var whosonline_html = '';
		members.each(function (member) {
			whosonline_html += '<li class="chat_widget_member" id="chat_widget_member_'
				+
				member.id + '">' + member.info.displayName + '</li>';
		});
		$('#chat_widget_online_list').html(whosonline_html);
		updateOnlineCount();
	});
	// presence channel receive events when members are added / removed
	channel.bind('pusher:member_added', function (member) {
		// track member additions to channel
		$('#chat_widget_online_list').append('<li class="chat_widget_member" ' +
			'id="chat_widget_member_' + member.id + '">'
			+ member.info.displayName + '</li>');
		updateOnlineCount();
	});
	channel.bind('pusher:member_removed', function (member) {
		// track member removals from channel
		$('#chat_widget_member_' + member.id).remove();
		updateOnlineCount();
	});
});
```

### Receive events

Clients can receive events triggered over a channel by
[binding](https://pusher.com/docs/client_api_guide/client_events#bind-events) to the channel
using the event name and attaching an event handler that is triggered on receiving the event.

The following example demonstrates attaching an event callback to a user-triggered event.
In the case of the chat application, the event callback is used to update the messages
displayed by the chat application.

[embedmd]:# (java/src/main/webapp/WEB-INF/view/chat.jsp /\/\/ bind to successful subscription/ /}\);/)
```js
// bind to successful subscription
channel.bind('pusher:subscription_succeeded', function (members) {
	// receive list of members on this channel
	var whosonline_html = '';
	members.each(function (member) {
		whosonline_html += '<li class="chat_widget_member" id="chat_widget_member_'
			+
			member.id + '">' + member.info.displayName + '</li>';
	});
});
```


### Trigger server-side endpoint to send messages

Now you can use a server-side endpoint as described earlier to trigger an event on a chat message.
The client can be excluded from receiving the broadcast message by providing the socket ID.

[embedmd]:# (java/src/main/webapp/WEB-INF/view/chat.jsp /\/\/ track socket_id/ /false;\n.*}\);/)
```js
// track socket_id to exclude recipient in subscription
socket_id = pusher.connection.socket_id;

// submit the message to /chat
$('#chat_widget_form').submit(function () {
	var chat_widget_input = $('#chat_widget_input'),
		chat_widget_button = $('#chat_widget_button'),
		message = chat_widget_input.val(); //get the value from the text input
	var data = JSON.stringify({
		message: message,
		channel_id: channel_name,
		socket_id: socket_id
	});
	// trigger a server-side endpoint to send the message via Pusher
	$.post('/message', data,
		function (msg) {
			chat_widget_button.show(); //show the chat button
			if (msg.status == "SUCCESS") {
				chat_widget_input.val('');
				handleMessage(msg); //display the message
			} else {
				alert("Error sending chat message : " + msg.status);
			}
		}, "json");

	return false;
});
```

## Disconnecting from Pusher

Pusher automatically closes connections when a user navigates to another web page or closes their
web browser.
If you need to close a client connection manually, refer to Pusher's
[Disconnecting from Pusher](https://pusher.com/docs/client_api_guide/client_connect#disconnecting) documentation.

## Running the application locally

The application uses the [App Engine Maven Plugin](/appengine/docs/standard/java/tools/using-maven)
to test and deploy to the Google Cloud App Engine Standard environment.

    mvn clean appengine:run

Access [http://localhost:8080](http://localhost:8080) via the browser, login, and join the chat room.

The chat window will contain a link you can use to join the room as a different user in another browser.

You should now be able to view both the users within the chat application window and send messages to one another.

## Deploying

- Deploy the application to the project:

		mvn clean appengine:deploy

- Access `https://YOUR_PROJECT_ID.appspot.com`

### Additional resources

- [Java on Google App Engine](/appengine/docs/java/)
- [Channels API deprecation](/appengine/docs/deprecations/channel)
- [Pusher tutorials](https://pusher.com/tutorials)
