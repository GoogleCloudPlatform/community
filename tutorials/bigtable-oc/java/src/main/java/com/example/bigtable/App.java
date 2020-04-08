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
import com.google.cloud.ServiceOptions;

import io.opencensus.common.Scope;
import io.opencensus.contrib.grpc.metrics.RpcViews;
import io.opencensus.exporter.stats.stackdriver.StackdriverStatsExporter;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceConfiguration;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceExporter;

import io.opencensus.stats.Aggregation;
import io.opencensus.stats.Aggregation.Distribution;
import io.opencensus.stats.BucketBoundaries;
import io.opencensus.stats.Measure.MeasureLong;
import io.opencensus.stats.Measure.MeasureDouble;
import io.opencensus.stats.Stats;
import io.opencensus.stats.StatsRecorder;
import io.opencensus.tags.TagKey;
import io.opencensus.stats.View;
import io.opencensus.stats.View.Name;
import io.opencensus.stats.ViewManager;

import io.opencensus.tags.TagKey;

import io.opencensus.trace.Span;
import io.opencensus.trace.Sampler;
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

import java.io.PrintWriter;
import java.io.StringWriter;

import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;

import org.apache.log4j.Level;
import org.apache.log4j.Logger;

public class App {
    private static final Logger logger = Logger.getLogger(App.class);

    // [START configChanges]
    private static final String PROJECT_ID = ServiceOptions.getDefaultProjectId();
    private static final String INSTANCE_ID = System.getenv( "INSTANCE_ID");
    // [END configChanges]
    // Refer to table metadata names by byte array in the HBase API
    private static final byte[] TABLE_NAME = Bytes.toBytes("Hello-Bigtable");
    private static final byte[] COLUMN_FAMILY_NAME = Bytes.toBytes("cf1");
    private static final byte[] COLUMN_NAME = Bytes.toBytes("greeting");


    // The read latency in milliseconds
    private static final MeasureDouble M_READ_LATENCY_MS = MeasureDouble.create("btapp/read_latency", "The latency in milliseconds for read", "ms");

    // [START config_oc_write_latency_measure]
    // The write latency in milliseconds
    private static final MeasureDouble M_WRITE_LATENCY_MS = MeasureDouble.create("btapp/write_latency", "The latency in milliseconds for write", "ms");
    // [END config_oc_write_latency_measure]

    // Counts the number of transactions
    private static final MeasureLong M_TRANSACTION_SETS = MeasureLong.create("btapp/transaction_set_count", "The count of transactions", "1");

    // Define the tags for potential grouping
    private static final TagKey KEY_LATENCY = TagKey.create("latency");
    private static final TagKey KEY_TRANSACTIONS = TagKey.create("transactions");

    private static final StatsRecorder STATS_RECORDER = Stats.getStatsRecorder();

    private static final Tracer tracer = Tracing.getTracer();

    // Write some friendly greetings to Cloud Bigtable
    private static final String[] GREETINGS =
      { "Hello World!", "Hello Cloud Bigtable!", "Hello HBase!" };


    private static void registerMetricViews() {
        // [START config_oc_latency_distribution] 
        Aggregation latencyDistribution = Distribution.create(BucketBoundaries.create(
                Arrays.asList(
                    0.0, 5.0, 10.0, 25.0, 100.0, 200.0, 400.0, 800.0, 10000.0)));
        // [END config_oc_latency_distribution] 

        // Define the count aggregation
        Aggregation countAggregation = Aggregation.Count.create();


        View[] views = new View[]{
            View.create(Name.create("btappmetrics/read_latency"),
                        "The distribution of the read latencies",
                        M_READ_LATENCY_MS,
                        latencyDistribution,
                        Collections.singletonList(KEY_LATENCY)),

            // [START config_oc_write_latency_view]
            View.create(Name.create("btappmetrics/write_latency"),
                        "The distribution of the write latencies",
                        M_WRITE_LATENCY_MS,
                        latencyDistribution,
                        Collections.singletonList(KEY_LATENCY)),
            // [END config_oc_write_latency_view]

            View.create(Name.create("btappmetrics/transaction_set_count"),
                        "The number of transaction sets performed",
                        M_TRANSACTION_SETS,
                        countAggregation, 
                        Collections.singletonList(KEY_TRANSACTIONS))
	};

	// Ensure that they are registered so
        // that measurements won't be dropped.
        ViewManager manager = Stats.getViewManager();
        for (View view : views)
            manager.registerView(view);
    }


    /**
     * Connects to Cloud Bigtable, runs some basic operations and prints the results.
     */
    private static void doBigTableOperations(String projectId, String instanceId, int demoRowCount) {

        long startRead;
        long endRead;
        long startWrite;
        long endWrite;

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

            logger.info("Create table " + descriptor.getNameAsString());
            admin.createTable(descriptor);
            // [END creating_a_table]

            // [START writing_rows]
            // Retrieve the table we just created so we can do some reads and writes
            Table table = connection.getTable(TableName.valueOf(TABLE_NAME));

            for (int i = 0; i < demoRowCount; i++) {
            // [START opencensus_scope_main]
                try (Scope ss = tracer.spanBuilder("opencensus.Bigtable.Tutorial").startScopedSpan()) {
    
                    // generate unique UUID
                    UUID uuid = UUID.randomUUID();
                    String randomUUIDString = uuid.toString();
    
                    startWrite = System.currentTimeMillis();
                    // write to Bigtable
                    writeRows(table, randomUUIDString);
                    endWrite = System.currentTimeMillis(); 
    
    
                    startRead = System.currentTimeMillis();
                    // read from Bigtable
                    readRows(table, randomUUIDString);
                    endRead = System.currentTimeMillis(); 
    
            // [END opencensus_scope_main]
            // [START opencensus_metric_record]
                    // record read, write latency metrics and count
                    STATS_RECORDER.newMeasureMap()
                                  .put(M_READ_LATENCY_MS, endRead - startRead)
                                  .put(M_WRITE_LATENCY_MS, endWrite - startWrite)
                                  .put(M_TRANSACTION_SETS, 1)
                                  .record();
            // [END opencensus_metric_record]
    
                }
            }
            // [START deleting_a_table]
            // Clean up by disabling and then deleting the table
            logger.info("Delete the table");
            admin.disableTable(table.getName());
            admin.deleteTable(table.getName());
            // [END deleting_a_table]

        } catch (IOException e) {
            logger.error("Exception while running HelloWorld: " + e.getMessage());
            StringWriter stackTraceString = new StringWriter();
            e.printStackTrace(new PrintWriter(stackTraceString));
            logger.error(stackTraceString.toString());
            System.exit(1);
        }
    }

    private static void writeRows(Table table, String uuidPrefix) throws IOException {
        try (Scope ss = tracer.spanBuilder("WriteRows").startScopedSpan()) {
            // Write some rows to the table
            Span span = tracer.getCurrentSpan();
            span.addAnnotation("Writing greetings to the table...");
            logger.debug("Write some greetings to the table");
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
                String rowKey = uuidPrefix + "#greeting" + i;

                // Put a single row into the table. We could also pass a list of Puts to write a batch.
                Put put = new Put(Bytes.toBytes(rowKey));
                put.addColumn(COLUMN_FAMILY_NAME, COLUMN_NAME, Bytes.toBytes(GREETINGS[i]));
                table.put(put);
            }
            // [END writing_rows]
        }
    }

    private static void readRows(Table table, String uuidPrefix) throws IOException {
        try (Scope ss = tracer.spanBuilder("ReadRows").startScopedSpan()) {
            // [START getting_a_row]
            // Get the first greeting by row key
            String rowKey =  uuidPrefix + "#greeting0";
            Result getResult = table.get(new Get(Bytes.toBytes(rowKey)));
            String greeting = Bytes
              .toString(getResult.getValue(COLUMN_FAMILY_NAME, COLUMN_NAME));
            logger.debug("Get a single greeting by row key");
            logger.debug(String.format("\t%s = %s\n", rowKey, greeting));
            // [END getting_a_row]

            // [START scanning_all_rows]
            // Now scan across all rows for UUID prefix. 
            byte[] startRow = (uuidPrefix + "#greeting0").getBytes();
            byte[] stopRow = (uuidPrefix + "#greeting3").getBytes();
            Scan scan = new Scan().withStartRow(startRow).withStopRow(stopRow);

            logger.debug("Scan for all greetings:");
            ResultScanner scanner = table.getScanner(scan);
            for (Result row : scanner) {
                byte[] valueBytes = row.getValue(COLUMN_FAMILY_NAME, COLUMN_NAME);
                logger.debug('\t' + Bytes.toString(valueBytes));
            }
            // [END scanning_all_rows]
        }
    }

    // [START config_oc_stackdriver_export]
    private static void configureOpenCensusExporters(Sampler sampler) throws IOException {
        TraceConfig traceConfig = Tracing.getTraceConfig();

        // For demo purposes, lets always sample.

        traceConfig.updateActiveTraceParams(
          traceConfig.getActiveTraceParams().toBuilder().setSampler(sampler).build());

        // Create the Stackdriver trace exporter
        StackdriverTraceExporter.createAndRegister(
          StackdriverTraceConfiguration.builder()
            .setProjectId(PROJECT_ID)
            .build());

        // [Start Stackdriver Monitoring]
        StackdriverStatsExporter.createAndRegister();

    // [END config_oc_stackdriver_export]

        // -------------------------------------------------------------------------------------------
        // Register all the gRPC views
        // OC will automatically go and instrument gRPC. It's going to capture app level metrics
        // like latency, req/res bytes, count of req/res messages, started rpc etc.
        // -------------------------------------------------------------------------------------------
        RpcViews.registerAllGrpcViews();
    }

    private static void sleep(int ms) {
      try {
        Thread.sleep(ms);
      } catch (Exception e) {
        logger.error("Exception while sleeping " + e.getMessage());
      }
    }

    public static void main(String[] args) throws IOException {
        logger.setLevel((Level) Level.INFO);

        // set up the views to expose the metrics
        registerMetricViews();
	    
        // [START config_oc_trace_sample]
        // sample every 1000 transactions
        configureOpenCensusExporters(Samplers.probabilitySampler(1/1000.0));
        // [END config_oc_trace_sample]
	    
        doBigTableOperations(PROJECT_ID, INSTANCE_ID, 10000);

        // IMPORTANT: do NOT exit right away. Wait for a duration longer than reporting
        // duration (5s) to ensure spans are exported. Spans are exported every 5 seconds.
        sleep(5100);
    }
}
