/*
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.google.example;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.integration.support.MessageBuilder;
import org.springframework.messaging.Message;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.view.RedirectView;
import reactor.core.publisher.EmitterProcessor;

/**
 * REST Controller for users to send messages.
 */
@RestController
public class DataEntryController {

  @Autowired
  private EmitterProcessor<Message<String>> frontEndListener;

  @PostMapping("/sendData")
  public RedirectView mainPage(
    @RequestParam("data") String data, @RequestParam("key") String key) {
    System.out.println("Sending data: " + data + " of key " + key + "..");

    // Headers become Pub/Sub message attributes.
    Message<String> message = MessageBuilder
      .withPayload(data)
      .setHeader("key", key)
      .build();

    // Send a message to a local processing queue (to be sent to Pub/Sub).
    this.frontEndListener.onNext(message);

    return new RedirectView("/");
  }
}
