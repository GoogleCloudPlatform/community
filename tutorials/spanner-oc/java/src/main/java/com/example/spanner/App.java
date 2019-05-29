/**
 * Copyright 2019 Google Inc. All Rights Reserved.
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.example.spanner;

import com.google.api.gax.longrunning.OperationFuture;
import com.google.cloud.ServiceOptions;
import com.google.cloud.spanner.Database;
import com.google.cloud.spanner.DatabaseAdminClient;
import com.google.cloud.spanner.DatabaseClient;
import com.google.cloud.spanner.DatabaseId;
import com.google.cloud.spanner.Key;
import com.google.cloud.spanner.Mutation;
import com.google.cloud.spanner.Spanner;
import com.google.cloud.spanner.SpannerException;
import com.google.cloud.spanner.SpannerExceptionFactory;
import com.google.cloud.spanner.SpannerOptions;
import com.google.spanner.admin.database.v1.CreateDatabaseMetadata;
import io.opencensus.common.Scope;
import io.opencensus.contrib.grpc.metrics.RpcViews;
import io.opencensus.exporter.stats.stackdriver.StackdriverStatsExporter;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceConfiguration;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceExporter;
import io.opencensus.trace.Tracing;
import io.opencensus.trace.config.TraceConfig;
import io.opencensus.trace.samplers.Samplers;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutionException;

/**
 * This sample demonstrates how to enable opencensus tracing and stats in cloud spanner client.
 */
public class App {

  // [START configChanges]
  private static final String PROJECT_ID = ServiceOptions.getDefaultProjectId();
  private static final String INSTANCE_ID = System.getenv( "INSTANCE_ID");
  private static final String DATABASE_ID = System.getenv( "DATABASE_ID");
  // [END configChanges]

  // [START config_oc_stackdriver_export]
  private static void configureOpenCensusExporters() throws IOException {
    TraceConfig traceConfig = Tracing.getTraceConfig();

    // Sampler is set to Samplers.alwaysSample() for demonstration. In production
    // or in high QPS environment please use default sampler.
    traceConfig.updateActiveTraceParams(
      traceConfig.getActiveTraceParams().toBuilder().setSampler(Samplers.alwaysSample()).build());

    // Create the Stackdriver trace exporter
    StackdriverTraceExporter.createAndRegister(
      StackdriverTraceConfiguration.builder()
        .setProjectId(PROJECT_ID)
        .build());

    // Create the Stackdriver monitoring exporter
    StackdriverStatsExporter.createAndRegister();

    // [END config_oc_stackdriver_export]

    // -------------------------------------------------------------------------------------------
    // Register all the gRPC views
    // OC will automatically go and instrument gRPC. It's going to capture app level metrics
    // like latency, req/res bytes, count of req/res messages, started rpc etc.
    // -------------------------------------------------------------------------------------------
    RpcViews.registerAllGrpcViews();
  }

  /**
   * Connects to Cloud Spanner, runs some basic operations.
   */
  private static void doSpannerOperations() {
    // Instantiate the client.
    SpannerOptions options = SpannerOptions.getDefaultInstance();
    Spanner spanner = options.getService();

    try {
      DatabaseId db = DatabaseId.of(
        options.getProjectId(), INSTANCE_ID, DATABASE_ID);
      // And then create the Spanner database client.
      DatabaseClient dbClient = spanner.getDatabaseClient(db);
      DatabaseAdminClient dbAdminClient = spanner.getDatabaseAdminClient();

      createDatabase(dbAdminClient, db);

      try (Scope ss = Tracing.getTracer().spanBuilder("create-players").startScopedSpan()) {
        // Warm up the spanner client session. In normal usage
        // you'd have hit this point after the first operation.
        dbClient.singleUse().readRow("Players", Key.of("foo@gmail.com"),
          Collections.singletonList("email"));

        // [START spanner_insert_data]
        for (int i = 0; i < 3; i++) {
          String up = i + "-" + (System.currentTimeMillis() / 1000) + ".";
          List<Mutation> mutations = Arrays.asList(
            playerMutation("Poke", "Mon", up + "poke.mon@example.org",
              "f1578551-eb4b-4ecd-aee2-9f97c37e164e"),
            playerMutation("Go", "Census", up + "go.census@census.io",
              "540868a2-a1d8-456b-a995-b324e4e7957a"),
            playerMutation("Quick", "Sort", up + "q.sort@gmail.com",
              "2b7e0098-a5cc-4f32-aabd-b978fc6b9710")
          );

          // write to Spanner
          dbClient.write(mutations);
        }
        // [END spanner_insert_data]
      }
    } catch (Exception e) {
      System.out.print("Exception while adding player: " + e);
    } finally {
      // Closes the client which will free up the resources used
      spanner.close();
    }
  }

  // [START spanner_create_database]
  private static void createDatabase(DatabaseAdminClient dbAdminClient, DatabaseId id) {
    OperationFuture<Database, CreateDatabaseMetadata> op =
      dbAdminClient.createDatabase(
        id.getInstanceId().getInstance(),
        id.getDatabase(),
        Collections.singletonList(
          "CREATE TABLE Players (\n"
            + "  first_name STRING(1024),\n"
            + "  last_name  STRING(1024),\n"
            + "  email   STRING(1024),\n"
            + "  uuid STRING(1024)\n"
            + ") PRIMARY KEY (email)"));
    try {
      // Initiate the request which returns an OperationFuture.
      Database db = op.get();
      System.out.println("Created database [" + db.getId() + "]");
    } catch (ExecutionException e) {
      // If the operation failed during execution, expose the cause.
      throw (SpannerException) e.getCause();
    } catch (InterruptedException e) {
      // Throw when a thread is waiting, sleeping, or otherwise occupied,
      // and the thread is interrupted, either before or during the activity.
      throw SpannerExceptionFactory.propagateInterrupt(e);
    }
  }
  // [END spanner_create_database]

  // [START spanner_insert_data]
  private static Mutation playerMutation(String firstName, String lastName, String email,
    String uuid) {
    return Mutation.newInsertBuilder("Players")
      .set("first_name")
      .to(firstName)
      .set("last_name")
      .to(lastName)
      .set("uuid")
      .to(uuid)
      .set("email")
      .to(email)
      .build();
  }
  // [END spanner_insert_data]

  private static void sleep(int ms) {
    try {
      Thread.sleep(ms);
    } catch (Exception ignored) { }
  }

  public static void main(String ...args) throws Exception {
    configureOpenCensusExporters();
    doSpannerOperations();

    // IMPORTANT: do NOT exit right away. Wait for a duration longer than reporting
    // duration (5s) to ensure spans are exported. Spans are exported every 5 seconds.
    sleep(5100);
  }
}
