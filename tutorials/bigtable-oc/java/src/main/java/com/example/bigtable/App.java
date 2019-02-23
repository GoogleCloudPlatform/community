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
package com.example.bigtable;

import com.google.cloud.bigtable.hbase.BigtableConfiguration;

import io.opencensus.common.Scope;
import io.opencensus.contrib.grpc.metrics.RpcViews;
import io.opencensus.exporter.stats.stackdriver.StackdriverStatsExporter;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceConfiguration;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceExporter;
import io.opencensus.trace.Span;
import io.opencensus.trace.Tracer;
import io.opencensus.trace.Tracing;
import io.opencensus.trace.config.TraceConfig;
import io.opencensus.trace.samplers.Samplers;
import org.apache.hadoop.hbase.HColumnDescriptor;
import org.apache.hadoop.hbase.HTableDescriptor;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.Admin;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.Get;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.ResultScanner;
import org.apache.hadoop.hbase.client.Scan;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;

import java.io.IOException;

public class App {
    private static final String PROJECT_ID = System.getProperty("PROJECT_ID", "my-project-id");
    private static final String INSTANCE_ID = System.getProperty( "INSTANCE_ID", "my-bigtable-instance-id");
    // Refer to table metadata names by byte array in the HBase API
    private static final byte[] TABLE_NAME = Bytes.toBytes("Hello-Bigtable");
    private static final byte[] COLUMN_FAMILY_NAME = Bytes.toBytes("cf1");
    private static final byte[] COLUMN_NAME = Bytes.toBytes("greeting");

    private static final Tracer tracer = Tracing.getTracer();

    // Write some friendly greetings to Cloud Bigtable
    private static final String[] GREETINGS =
      { "Hello World!", "Hello Cloud Bigtable!", "Hello HBase!" };

    /**
     * Connects to Cloud Bigtable, runs some basic operations and prints the results.
     */
    private static void doHelloWorld(String projectId, String instanceId)
      throws InterruptedException {

        // [START connecting_to_bigtable]
        // Create the Bigtable connection, use try-with-resources to make sure it gets closed
        try (Connection connection = BigtableConfiguration.connect(projectId, instanceId)) {

            // The admin API lets us create, manage and delete tables
            Admin admin = connection.getAdmin();
            // [END connecting_to_bigtable]

            // [START creating_a_table]
            // Create a table with a single column family
            HTableDescriptor descriptor = new HTableDescriptor(TableName.valueOf(TABLE_NAME));
            descriptor.addFamily(new HColumnDescriptor(COLUMN_FAMILY_NAME));

            System.out.println("Create table " + descriptor.getNameAsString());
            admin.createTable(descriptor);
            // [END creating_a_table]

            // [START writing_rows]
            // Retrieve the table we just created so we can do some reads and writes
            Table table = connection.getTable(TableName.valueOf(TABLE_NAME));

            try (Scope ss = tracer.spanBuilder("opencensus.Bigtable.Tutorial").startScopedSpan()) {

                // now write to Bigtable
                writeRows(table);

                // read from Bigtable
                readRows(table);

            }
            // [START deleting_a_table]
            // Clean up by disabling and then deleting the table
            System.out.println("Delete the table");
            admin.disableTable(table.getName());
            admin.deleteTable(table.getName());
            // [END deleting_a_table]

        } catch (IOException e) {
            System.err.println("Exception while running HelloWorld: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }

        // IMPORTANT: do NOT exit right away. OpenCensus needs time to
        // send traces to backend (Stackdriver in this case)
        int secondsToWait = 15;
        System.out.println("Exiting in " + String.valueOf(secondsToWait) + "s...");
        for(int i = secondsToWait-1; i >= 0; i--) {
            Thread.sleep(1000);
            System.out.println(String.valueOf(i) + "s...");
        }

        System.exit(0);
    }

    private static void writeRows(Table table) throws IOException {
        try (Scope ss = tracer.spanBuilder("WriteRows").startScopedSpan()) {
            // Write some rows to the table
            Span span = tracer.getCurrentSpan();
            span.addAnnotation("Writing greetings to the table...");
            System.out.println("Write some greetings to the table");
            for (int i = 0; i < GREETINGS.length; i++) {
                // Each row has a unique row key.
                //
                // Note: This example uses sequential numeric IDs for simplicity, but
                // this can result in poor performance in a production application.
                // Since rows are stored in sorted order by key, sequential keys can
                // result in poor distribution of operations across nodes.
                //
                // For more information about how to design a Bigtable schema for the
                // best performance, see the documentation:
                //
                //     https://cloud.google.com/bigtable/docs/schema-design
                String rowKey = "greeting" + i;

                // Put a single row into the table. We could also pass a list of Puts to write a batch.
                Put put = new Put(Bytes.toBytes(rowKey));
                put.addColumn(COLUMN_FAMILY_NAME, COLUMN_NAME, Bytes.toBytes(GREETINGS[i]));
                table.put(put);
            }
            // [END writing_rows]
        }
    }

    private static void readRows(Table table) throws IOException {
        try (Scope ss = tracer.spanBuilder("ReadRows").startScopedSpan()) {
            // [START getting_a_row]
            // Get the first greeting by row key
            String rowKey = "greeting0";
            Result getResult = table.get(new Get(Bytes.toBytes(rowKey)));
            String greeting = Bytes
              .toString(getResult.getValue(COLUMN_FAMILY_NAME, COLUMN_NAME));
            System.out.println("Get a single greeting by row key");
            System.out.printf("\t%s = %s\n", rowKey, greeting);
            // [END getting_a_row]

            // [START scanning_all_rows]
            // Now scan across all rows.
            Scan scan = new Scan();

            System.out.println("Scan for all greetings:");
            ResultScanner scanner = table.getScanner(scan);
            for (Result row : scanner) {
                byte[] valueBytes = row.getValue(COLUMN_FAMILY_NAME, COLUMN_NAME);
                System.out.println('\t' + Bytes.toString(valueBytes));
            }
            // [END scanning_all_rows]
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        configureOpenCensusExporters();

        doHelloWorld(PROJECT_ID, INSTANCE_ID);
    }

    private static String requiredProperty(String prop) {
        String value = System.getProperty(prop);
        if (value == null) {
            throw new IllegalArgumentException("Missing required system property: " + prop);
        }
        return value;
    }

    private static void configureOpenCensusExporters() throws IOException {
        TraceConfig traceConfig = Tracing.getTraceConfig();

        // For demo purposes, lets always sample.
        traceConfig.updateActiveTraceParams(
          traceConfig.getActiveTraceParams().toBuilder().setSampler(Samplers.alwaysSample()).build());

        // Create the Stackdriver trace exporter
        StackdriverTraceExporter.createAndRegister(
          StackdriverTraceConfiguration.builder()
            .setProjectId(PROJECT_ID)
            .build());

        // [Start Stackdriver Monitoring]
        StackdriverStatsExporter.createAndRegister();

        // -------------------------------------------------------------------------------------------
        // Register all the gRPC views
        // OC will automatically go and instrument gRPC. It's going to capture app level metrics
        // like latency, req/res bytes, count of req/res messages, started rpc etc.
        // -------------------------------------------------------------------------------------------
        RpcViews.registerAllGrpcViews();
    }
}

