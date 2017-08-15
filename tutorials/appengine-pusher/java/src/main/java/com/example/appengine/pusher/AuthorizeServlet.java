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

import com.google.appengine.api.users.User;
import com.google.appengine.api.users.UserServiceFactory;
import com.google.common.io.CharStreams;
import com.pusher.rest.Pusher;
import com.pusher.rest.data.PresenceUser;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.util.HashMap;
import java.util.Map;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Authorization endpoint that is automatically triggered on `Pusher.subscribe` for private,
 * presence channels. Successful authentication returns valid authorization token with user
 * information.
 *
 * @see <a href="https://pusher.com/docs/authenticating_users">Pusher Authentication Docs</a>
 */
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
