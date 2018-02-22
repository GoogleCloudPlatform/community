/**
 * Copyright 2017 Google LLC
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

package com.google.cloud.solutions.rtdp;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

/** Command line options for the MQTT example. */
public class MqttOptions {
  public String projectId;
  public String registryId;
  public String deviceId;
  public String privateKeyFile;
  public String algorithm;
  public String lat;
  public String lng;
  public String cloudRegion = "us-central1";
  public int numMessages = 100;
  public String mqttBridgeHostname = "mqtt.googleapis.com";
  public short mqttBridgePort = 8883;

  /** Construct an MqttExampleOptions class from command line flags. */
  public static MqttOptions fromFlags(String[] args) {
    Options options = new Options();
    // Required arguments
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("project_id")
            .hasArg()
            .desc("GCP cloud project name.")
            .required()
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("registry_id")
            .hasArg()
            .desc("Cloud IoT registry id.")
            .required()
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("device_id")
            .hasArg()
            .desc("Cloud IoT device id.")
            .required()
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("private_key_file")
            .hasArg()
            .desc("Path to private key file.")
            .required()
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("algorithm")
            .hasArg()
            .desc("Encryption algorithm to use to generate the JWT. Either 'RS256' or 'ES256'.")
            .required()
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("lat")
            .hasArg()
            .desc("Base lattitude")
            .required()
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("lng")
            .hasArg()
            .desc("Base longitude")
            .required()
            .build());

    // Optional arguments.
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("cloud_region")
            .hasArg()
            .desc("GCP cloud region.")
            .build());
    options.addOption(
        Option.builder()
            .type(Number.class)
            .longOpt("num_messages")
            .hasArg()
            .desc("Number of messages to publish.")
            .build());
    options.addOption(
        Option.builder()
            .type(String.class)
            .longOpt("mqtt_bridge_hostname")
            .hasArg()
            .desc("MQTT bridge hostname.")
            .build());
    options.addOption(
        Option.builder()
            .type(Number.class)
            .longOpt("mqtt_bridge_port")
            .hasArg()
            .desc("MQTT bridge port.")
            .build());

    CommandLineParser parser = new DefaultParser();
    CommandLine commandLine;
    try {
      commandLine = parser.parse(options, args);
      MqttOptions opts = new MqttOptions();

      opts.projectId = commandLine.getOptionValue("project_id");
      opts.registryId = commandLine.getOptionValue("registry_id");
      opts.deviceId = commandLine.getOptionValue("device_id");
      opts.privateKeyFile = commandLine.getOptionValue("private_key_file");
      opts.algorithm = commandLine.getOptionValue("algorithm");
      opts.lat = commandLine.getOptionValue("lat");
      opts.lng = commandLine.getOptionValue("lng");
      if (commandLine.hasOption("cloud_region")) {
        opts.cloudRegion = commandLine.getOptionValue("cloud_region");
      }
      if (commandLine.hasOption("num_messages")) {
        opts.numMessages = ((Number) commandLine.getParsedOptionValue("num_messages")).intValue();
      }
      if (commandLine.hasOption("mqtt_bridge_hostname")) {
        opts.mqttBridgeHostname = commandLine.getOptionValue("mqtt_bridge_hostname");
      }
      if (commandLine.hasOption("mqtt_bridge_port")) {
        opts.mqttBridgePort =
            ((Number) commandLine.getParsedOptionValue("mqtt_bridge_port")).shortValue();
      }
      return opts;
    } catch (ParseException e) {
      System.err.println(e.getMessage());
      return null;
    }
  }
}
