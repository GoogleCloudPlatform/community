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

import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.options.StreamingOptions;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.Validation.Required;
import org.apache.beam.sdk.Pipeline;

import java.io.IOException;

public class DedupPubSub {

  public interface PubSubToGCSOptions extends PipelineOptions, StreamingOptions {
    @Description(
        "The Pub/Sub topic to read from."
            + "The name should be in the format of "
            + "projects/<project-id>/topics/<input-topic-name>.")
    @Required
    String getInputTopic();

    void setInputTopic(String inputTopic);

    @Description(
        "The Pub/Sub topic to publish to."
            + "The name should be in the format of"
            + "projects/<project-id>/topics/<output-topic-name>.")
    @Required
    String getOutputTopic();

    void setOutputTopic(String outputTopic);

    @Description("The field used by Dataflow's PubsubIO to deduplicate messages.")
    @Required
    String getIdAttribute();

    void setIdAttribute(String idAttribute);
  }

  public static void main(String[] args) throws IOException {

    PubSubToGCSOptions options =
        PipelineOptionsFactory.fromArgs(args).withValidation().as(PubSubToGCSOptions.class);

    options.setStreaming(true);

    Pipeline pipeline = Pipeline.create(options);

    pipeline
        // 1) Read string messages with attributes from a Pub/Sub topic.
        .apply(
            "Read from PubSub",
            PubsubIO.readStrings()
                .fromTopic(options.getInputTopic())
                .withIdAttribute(options.getIdAttribute()))
        // 2) Write string messages to another Pub/Sub topic.
        .apply("Write to PubSub", PubsubIO.writeStrings().to(options.getOutputTopic()));

    // Execute the pipeline.
    pipeline.run().waitUntilFinish();
  }
}
