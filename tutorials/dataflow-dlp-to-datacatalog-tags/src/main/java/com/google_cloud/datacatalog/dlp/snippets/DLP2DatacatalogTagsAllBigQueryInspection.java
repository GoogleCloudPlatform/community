/*
 * Copyright 2020 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.google_cloud.datacatalog.dlp.snippets;

import com.google.api.gax.paging.Page;
import com.google.cloud.bigquery.BigQuery;
import com.google.cloud.bigquery.BigQueryOptions;
import com.google.cloud.bigquery.Dataset;
import com.google.cloud.bigquery.Table;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Properties;
import java.util.UUID;
import org.apache.beam.runners.dataflow.options.DataflowWorkerLoggingOptions;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.options.ValueProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link DLP2DatacatalogTagsAllBigQueryInspection} is a streaming pipeline that reads BigQuery
 * tables, uses Cloud DLP API to inspect and classify sensitive information (e.g. PII Data like
 * passport or SIN number) and at the end stores tags in Data Catalog to be used for various
 * purposes.
 */
public class DLP2DatacatalogTagsAllBigQueryInspection {
  private static final String PIPELINE_PACKAGE_NAME = "com.google_cloud.datacatalog.dlp.snippets";

  /**
   * Main entry point for executing the pipeline. This will run the pipeline asynchronously. If
   * blocking execution is required, use the {@link
   * DLP2DatacatalogTagsAllBigQueryInspection method to start the
   * pipeline and invoke {@code result.waitUntilFinish()} on the {@link PipelineResult}
   *
   * @param args The command-line arguments to the pipeline.
   */
  public static void main(String[] args) {
    try (InputStream input =
        DLP2DatacatalogTagsAllBigQueryInspection.class
            .getClassLoader()
            .getResourceAsStream("config.properties")) {
      Properties prop = new Properties();

      // load a properties file from class path, inside static method
      prop.load(input);

      PipelineOptionsFactory.register(BigQueryInspectionPipelineOptions.class);

      BigQueryInspectionPipelineOptions options =
          PipelineOptionsFactory.fromArgs(args)
              .withValidation()
              .as(BigQueryInspectionPipelineOptions.class);

      Boolean verboseLogging = getPropertiesBool(prop, "verbose.logging", "false");

      if (verboseLogging) {
        DataflowWorkerLoggingOptions loggingOptions =
            options.as(DataflowWorkerLoggingOptions.class);

        // Overrides logger for package.
        DataflowWorkerLoggingOptions.WorkerLogLevelOverrides workerLogger =
            new DataflowWorkerLoggingOptions.WorkerLogLevelOverrides();

        // Set debug level for the pipeline class
        loggingOptions.setWorkerLogLevelOverrides(
            workerLogger.addOverrideForPackage(
                Package.getPackage(PIPELINE_PACKAGE_NAME),
                DataflowWorkerLoggingOptions.Level.DEBUG));
      }

      UUID uuid = UUID.randomUUID();
      String runID = uuid.toString();

      String bigQueryTablesFromConfig = geBigQueryTablesFromConfig(prop);
      if (bigQueryTablesFromConfig != null) {
        createPipelinesForConfigBQResources(prop, options, runID, bigQueryTablesFromConfig);
      } else {
        createPipelinesforALLBQResources(prop, options, runID);
      }
    } catch (IOException ex) {
      ex.printStackTrace();
    }
  }

  private static void createPipelinesForConfigBQResources(
      Properties prop,
      BigQueryInspectionPipelineOptions options,
      String runID,
      String bigQueryTables) {
    System.out.println("Creating Pipelines for Config BQ Resources");

    Boolean serialExecution = getPropertiesBool(prop, "pipeline.serial.execution", "false");

    String[] bigQueryTablesList = bigQueryTables.split(",");

    List<PipelineResult> pipelineResults = new ArrayList<>();
    for (String bigQueryTable : bigQueryTablesList) {
      options.setJobName(buildJobName(bigQueryTable, runID));

      System.out.println("Pipeline created for table: " + bigQueryTable);

      PipelineResult pipeline =
          DLP2DatacatalogTagsBigQueryPipeline.run(
              options, prop, ValueProvider.StaticValueProvider.of(bigQueryTable));

      pipelineResults.add(pipeline);

      if (serialExecution) {
        System.out.println("Waiting for pipeline to be done: " + bigQueryTable);
        pipeline.waitUntilFinish();
      }
    }

    waitForResults(pipelineResults);
  }

  private static void createPipelinesforALLBQResources(
      Properties prop, BigQueryInspectionPipelineOptions options, String runID) {
    BigQuery bigquery = BigQueryOptions.getDefaultInstance().getService();

    Page<Dataset> datasets =
        bigquery.listDatasets(options.getProject(), BigQuery.DatasetListOption.pageSize(100));

    if (datasets == null) {
      System.out.println("No Datasets found");
      return;
    }

    System.out.println("Creating Pipelines for ALL BQ Resources");

    Boolean serialExecution = getPropertiesBool(prop, "pipeline.serial.execution", "false");

    List<PipelineResult> pipelineResults = new ArrayList<>();
    for (Dataset dataset : datasets.iterateAll()) {
      Page<Table> tables = bigquery.listTables(dataset.getDatasetId());

      for (Table table : tables.iterateAll()) {
        final String jobName = buildJobName(table.getTableId().getTable(), runID);
        options.setJobName(jobName);
        System.out.println("Job Name: " + jobName);
        String tableName =
            String.format(
                "%s:%s.%s",
                table.getTableId().getProject(),
                table.getTableId().getDataset(),
                table.getTableId().getTable());

        System.out.println("Pipeline created for table: " + tableName);

        PipelineResult pipeline =
            DLP2DatacatalogTagsBigQueryPipeline.run(
                options, prop, ValueProvider.StaticValueProvider.of(tableName));

        pipelineResults.add(pipeline);

        if (serialExecution) {
          System.out.println("Waiting for pipeline to be done: " + tableName);
          pipeline.waitUntilFinish();
        }
      }
    }

    waitForResults(pipelineResults);
  }

  private static void waitForResults(List<PipelineResult> pipelineResults) {
    Collections.reverse(pipelineResults);
    for (PipelineResult pipeline : pipelineResults) {
      pipeline.waitUntilFinish();
    }

    System.out.println("Execution done, check results on Data Catalog: "
        + "https://console.cloud.google.com/datacatalog");
  }

  private static String buildJobName(String bigQueryTable, String runID) {
    return "dlp2dc-"
        + bigQueryTable.replace(":", "-").replace(".", "-").replace("_", "-")
        + "-"
        + runID.substring(0, 8);
  }

  private static Boolean getPropertiesBool(Properties prop, String key, String defaultValue) {
    return Boolean.valueOf(prop.getProperty(key, defaultValue));
  }

  private static String geBigQueryTablesFromConfig(Properties prop) {
    return prop.getProperty("bigquery.tables", null);
  }
}
