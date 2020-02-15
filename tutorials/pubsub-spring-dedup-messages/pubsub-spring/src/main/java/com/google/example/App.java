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

import java.util.function.Consumer;
import java.util.function.Supplier;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.Message;
import reactor.core.publisher.EmitterProcessor;
import reactor.core.publisher.Flux;

/**
 * Spring Boot application that uses Pub/Sub as a message broker.
 *
 * This class bootstraps the application. The Supplier bean sends data from an
 * internal queue to a Pub/Sub topic; the Consumer bean returns data from
 * Pub/Sub to the application; the EmitterProcessor bean establishes
 * communication between DataEntryController and a Spring Cloud Stream source.
 *
 */
@SpringBootApplication
public class App {

  public static void main(String[] args) {
    SpringApplication.run(App.class, args);
  }

  // This acts as a bridge between the frontend and a Spring Cloud Stream source.
  @Bean
  public EmitterProcessor<Message<String>> frontEndListener() {
    return EmitterProcessor.create();
  }

  // The Supplier Bean makes the function a valid Spring Cloud Stream source. It
  // sends messages to a Pub/Sub topic configured with the binding name
  // `sendMessagesForDeduplication-out-0` in application.properties.
  @Bean
  Supplier<Flux<Message<String>>> sendMessagesForDeduplication(
    final EmitterProcessor<Message<String>> frontEndListener) {
    return () -> frontEndListener;
  }

  // The Consumer Bean makes the function a valid Spring Cloud Stream sink. It
  // receives messages from a Pub/Sub subscription configured with the binding
  // name `receiveDedupedMessagesFromDataflow-in-0` in application.properties.
  @Bean
  Consumer<Message<String>> receiveDedupedMessagesFromDataflow() {
    return msg -> {
      System.out.println("\tReceived message: \"" + msg.getPayload() + "\".");
    };
  }
}
