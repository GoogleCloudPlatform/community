<!DOCTYPE HTML>
<%@ page import="com.example.appengine.pusher.ChatServlet" %>
<%@ page import="com.example.appengine.pusher.PusherService" %>
<%@ page import="java.util.Date" %>
<%--
 Copyright 2017 Google Inc.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
--%>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="../../static/chat.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
    <script src="https://js.pusher.com/4.1/pusher.min.js"></script>
</head>
<body>
<div id="chat_widget_container">
    <div id="chat_widget_main_container">
        <div id="chat_widget_messages_container">
            <div id="chat_widget_messages">
            </div>
        </div>
        <div id="chat_widget_online">
            <p>Room(<span id="chat_room_name"></span>)</p>
            <p>Online (<span id="chat_widget_counter">0</span>)</p>
            <ul id="chat_widget_online_list">
                <li></li>
            </ul>
        </div>
        <div class="clear"></div>
        <div id="chat_widget_input_container">
            <form method="post" id="chat_widget_form">
                <input type="text" id="chat_widget_input"/>
                <input type="submit" value="Chat" id="chat_widget_button"/>
            </form>
        </div>
    </div>
</div>
<script>

    <% String room = (String) request.getAttribute("room");
    if (room == null || room.length() == 0 || room.equals("null")) {
      room = "chat-" + String.valueOf(Math.round(new Date().getTime() + (Math.random() * 100)));
      request.setAttribute("room", room);
    }
    %>
    var room = '<%= (String)request.getAttribute("room")%>';
    var roomLink = '<%= ChatServlet.getUriWithChatRoom(request, (String)request.getAttribute("room")) %>';
    $('#chat_room_name').html("<a href=\"" + roomLink + "\">" + room + "<a>");

    var socket_id = null;
    // add presence prefix for authenticated presence channels.
    var channel_name = "presence-" + room;
    function updateOnlineCount() {
        $('#chat_widget_counter').html($('.chat_widget_member').length);
    }

    // Connect to Pusher with auth endpoint on your server for private/presence channels
    // (default auth endpoint : /pusher/auth)
    var pusher = new Pusher('<%= PusherService.APP_KEY %>', {
        cluster: '<%= PusherService.CLUSTER %>',
        authEndpoint: '/authorize',
        encrypted: true
    });

    // Subscribe to the chat room presence channel, eg. "presence-my-room"
    var channel = pusher.subscribe(channel_name);

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

        function handleMessage(data) {
            $('#chat_widget_messages').append(data.message + '<br />');
        }

        // subscribe to new messages in the chat application
        channel.bind('new_message', function (data) {
            handleMessage(data);
        });

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
    });
</script>
</body>
</html>
