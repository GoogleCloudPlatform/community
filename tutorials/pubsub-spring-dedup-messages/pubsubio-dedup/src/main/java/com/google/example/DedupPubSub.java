package com.google.example;

import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.*;
import org.apache.beam.sdk.options.Validation.Required;
import org.apache.beam.sdk.Pipeline;

import java.io.IOException;

public class DedupPubSub {
  public interface PubSubToGCSOptions extends PipelineOptions, StreamingOptions {
    @Description("The Cloud Pub/Sub topic to read from."
      + "The name should be in the format of "
      + "projects/<project-id>/topics/<input-topic-name>.")
    @Required
    String getInputTopic();
    void setInputTopic(String inputTopic);

    @Description(
      "The Cloud Pub/Sub topic to publish to."
        + "The name should be in the format of"
        + "projects/<project-id>/topics/<output-topic-name>.")
    @Validation.Required
    String getOutputTopic();
    void setOutputTopic(String outputTopic);

    @Description(
      "The field used by Dataflow to deduplicate messages.")
    @Validation.Required
    String getIdAttribute();
    void setIdAttribute(String idAttribute);
  }

  public static void main(String[] args) throws IOException {

    PubSubToGCSOptions options = PipelineOptionsFactory
      .fromArgs(args)
      .withValidation()
      .as(PubSubToGCSOptions.class);

    options.setStreaming(true);

    Pipeline pipeline = Pipeline.create(options);

    pipeline
      // 1) Read string messages from a Pub/Sub topic.
      .apply("Read from PubSub",
        PubsubIO
          .readStrings()
          .fromTopic(options.getInputTopic())
          .withIdAttribute(options.getIdAttribute())
      )
      // 2) Write string messages to a Pub/Sub topic.
      .apply("Write to PubSub", PubsubIO.writeStrings().to(options.getOutputTopic()));

    // Execute the pipeline and wait until it finishes running.
    pipeline.run().waitUntilFinish();
  }
}
