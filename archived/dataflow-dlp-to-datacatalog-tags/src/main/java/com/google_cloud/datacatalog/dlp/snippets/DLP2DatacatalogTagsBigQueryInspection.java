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

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import org.apache.beam.runners.dataflow.options.DataflowWorkerLoggingOptions;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.options.PipelineOptionsFactory;

/**
 * The {@link DLP2DatacatalogTagsBigQueryInspection} is a streaming pipeline that reads a BigQuery
 * table, uses Cloud DLP API to inspect and classify sensitive information (e.g. PII Data like
 * passport or SIN number) and at the end stores tags in Data Catalog to be used for various
 * purposes.
 */
public class DLP2DatacatalogTagsBigQueryInspection {

  private static final String PIPELINE_PACKAGE_NAME = "com.google_cloud.datacatalog.dlp.snippets";

  /**
   * Main entry point for executing the pipeline. This will run the pipeline asynchronously. If
   * blocking execution is required, use the {@link DLP2DatacatalogTagsBigQueryInspection} method to
   * start the pipeline and invoke {@code result.waitUntilFinish()} on the {@link PipelineResult}
   *
   * @param args The command-line arguments to the pipeline.
   */
  public static void main(String[] args) {
    try (InputStream input =
        DLP2DatacatalogTagsBigQueryInspection.class
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

      DLP2DatacatalogTagsBigQueryPipeline.run(options, prop, options.getBigQueryTable());
    } catch (IOException ex) {
      ex.printStackTrace();
    }
  }

  private static Boolean getPropertiesBool(Properties prop, String key, String defaultValue) {
    return Boolean.valueOf(prop.getProperty(key, defaultValue));
  }
}
