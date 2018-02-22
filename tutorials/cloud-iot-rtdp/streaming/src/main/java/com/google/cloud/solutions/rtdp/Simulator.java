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

import io.jsonwebtoken.JwtBuilder;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Random;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.MqttPersistenceException;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.joda.time.DateTime;

/*
 * Simulator emulates multiple MQTT clients and establishes sessions to Cloud IoT Core.
 * It randomly chooses MQTT sessions and sends a specified number of messages repeatedly.
 */
public class Simulator implements MqttCallback {
  public static final int NUM_DEVICES = 30;

  private static PrivateKey loadKeyFile(String filename, String algorithm) throws Exception {
    byte[] keyBytes = Files.readAllBytes(Paths.get(filename));
    PKCS8EncodedKeySpec spec = new PKCS8EncodedKeySpec(keyBytes);
    KeyFactory kf = KeyFactory.getInstance(algorithm);
    return kf.generatePrivate(spec);
  }

  private static String createJwt(String projectId, String privateKeyFile, String algorithm)
      throws Exception {
    DateTime now = new DateTime();
    JwtBuilder jwtBuilder =
        Jwts.builder()
            .setIssuedAt(now.toDate())
            .setExpiration(now.plusMinutes(60).toDate())
            .setAudience(projectId);

    if (algorithm.equals("RS256")) {
      PrivateKey privateKey = loadKeyFile(privateKeyFile, "RSA");
      return jwtBuilder.signWith(SignatureAlgorithm.RS256, privateKey).compact();
    } else if (algorithm.equals("ES256")) {
      PrivateKey privateKey = loadKeyFile(privateKeyFile, "EC");
      return jwtBuilder.signWith(SignatureAlgorithm.ES256, privateKey).compact();
    } else {
      throw new IllegalArgumentException(
          "Invalid algorithm " + algorithm + ". Should be one of 'RS256' or 'ES256'.");
    }
  }

  private MqttClient client;
  private String deviceId;
  private String topic;
  private Random rand;
  private String sz = "20";
  private String lat;
  private String lng;

  /** Class for simulator. */
  public Simulator(int id, MqttOptions options) {
    rand = new Random();
    lat = options.lat + String.format("%04d", rand.nextInt(10000));
    lng = options.lng + String.format("%04d", rand.nextInt(10000));
    deviceId = options.deviceId + Integer.toString(id);
    String mqttServerAddress =
        String.format("ssl://%s:%s", options.mqttBridgeHostname, options.mqttBridgePort);
    String mqttClientId =
        String.format(
            "projects/%s/locations/%s/registries/%s/devices/%s",
            options.projectId, options.cloudRegion, options.registryId, deviceId);
    MqttConnectOptions connectOptions = new MqttConnectOptions();
    connectOptions.setMqttVersion(MqttConnectOptions.MQTT_VERSION_3_1_1);
    connectOptions.setUserName("unused");
    try {
      connectOptions.setPassword(
          createJwt(options.projectId, options.privateKeyFile, options.algorithm).toCharArray());
      client = new MqttClient(mqttServerAddress, mqttClientId, new MemoryPersistence());
      client.setCallback(this);
      client.connect(connectOptions);
      topic = String.format("/devices/%s/events", deviceId);
    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  /** Publish temperature data using default (generate random).*/
  public void publish() throws MqttPersistenceException, MqttException {
    publish(-1);
  }

  /** Publish temperature data.*/
  public void publish(int t) throws MqttPersistenceException, MqttException {
    int temp = t;
    if (t == -1) {
      do {
        temp = rand.nextInt(35);
      } while (temp < 20);
    }
    long dt = System.currentTimeMillis();
    String payload =
        String.format(
            "%s,%s,%s,%s,%s,%s", deviceId, Long.toString(dt), Integer.toString(temp), lat, lng, sz);

    MqttMessage message = new MqttMessage(payload.getBytes());
    message.setQos(1);

    client.publish(topic, message);
  }

  public void disconnect() throws MqttException {
    client.disconnect();
  }

  public void connectionLost(Throwable arg0) {}

  public void deliveryComplete(IMqttDeliveryToken arg0) {}

  public void messageArrived(String arg0, MqttMessage arg1) throws Exception {}

  /** Main entry point to application.*/
  public static void main(String[] args) throws Exception {
    MqttOptions options = MqttOptions.fromFlags(args);
    if (options == null) {
      System.exit(1);
    }

    Random rand = new Random();
    Simulator[] sims = new Simulator[NUM_DEVICES];
    for (int i = 0; i < NUM_DEVICES; i++) {
      sims[i] = new Simulator(i + 1, options);
    }

    for (int i = 1; i <= options.numMessages; ++i) {
      // Choose a device randomly to publish a message.
      int id = rand.nextInt(NUM_DEVICES);
      sims[id].publish();
      Thread.sleep(200);
    }

    for (int i = 0; i < NUM_DEVICES; i++) {
      sims[i].disconnect();
    }
    System.out.println("Finished loop successfully. Goodbye!");
  }
}
