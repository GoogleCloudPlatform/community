/*
 * Copyright 2019 Google LLC
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

import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.function.Consumer;
import java.util.function.Supplier;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.Message;
import reactor.core.publisher.EmitterProcessor;
import reactor.core.publisher.Flux;

/**
 *
 */
@SpringBootApplication
public class App {


	public static void main(String[] args) {
		SpringApplication.run(App.class, args);
	}

	@Bean
	public EmitterProcessor<Message<String>> frontEndListener() {
		return EmitterProcessor.create();
	}

	// This will automatically send all data from the internal queue to the Pub/Sub topic configured
	// in application.properties.
	@Bean
	Supplier<Flux<Message<String>>> sendMessagesForDeduplication(final EmitterProcessor<Message<String>> frontEndListener) {
		return () -> frontEndListener;
	}


	@Bean
	Consumer<Message<String>> receiveDedupedMessagesFromDataflow() {
		return msg -> {
			System.out.println("\tDE-DUPED message: \"" + msg.getPayload() + "\".");
		};
	}


}
