/*
 * Copyright 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.example.appengine.pusher;

import com.fasterxml.jackson.core.type.TypeReference;
import com.google.appengine.api.users.User;
import com.google.appengine.api.users.UserServiceFactory;
import com.google.common.io.CharStreams;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.pusher.rest.data.Result;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Submit a chat message over a channel. Note : we use socket_id to exclude the sender from
 * receiving the message // {@see
 * <ahref="https://pusher.com/docs/server_api_guide/server_excluding_recipients">Excluding
 * Recipients</ahref>}
 */
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
    // User email prefix as display name for current currently authenticated user
    String displayName = user.getNickname().replaceFirst("@.*", "");

    // Create a message including the user email prefix to display in the chat window
    String taggedMessage = "<strong>&lt;" + displayName + "&gt;</strong> " + message;
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
