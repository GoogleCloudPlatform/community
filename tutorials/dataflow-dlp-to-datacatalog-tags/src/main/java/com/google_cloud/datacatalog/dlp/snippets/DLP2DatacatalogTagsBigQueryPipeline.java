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

import com.google.api.services.bigquery.model.TableRow;
import com.google.privacy.dlp.v2.Finding;
import com.google.privacy.dlp.v2.Table;
import java.util.Collections;
import java.util.List;
import java.util.Properties;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Wait;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;

public class DLP2DatacatalogTagsBigQueryPipeline {

  /**
   * Runs the pipeline with the supplied options.
   *
   * @param options The execution parameters to the pipeline.
   * @return The result of the pipeline execution.
   */
  public static PipelineResult run(
      BigQueryInspectionPipelineOptions options,
      Properties prop,
      ValueProvider<String> bigQueryTableProvider) {

    // Create the main pipeline
    Pipeline mainPipeline = Pipeline.create(options);

    PCollection<List<String>> setupFlow =
        mainPipeline
            .apply("Setup Flow", Create.of(Collections.singletonList(1)))
            .apply(
                "Get Info Types", ParDo.of(new DLPGetInfoTypes(options.getInspectTemplateName())))
            .apply(
                "Init Tag Templates",
                // Create Data Catalog Tag Templates used by Tags.
                ParDo.of(
                    new DataCatalogInitTemplatesDoFn(
                        options.getDlpProjectId(),
                        options.getTagTemplateSuffix(),
                        bigQueryTableProvider,
                        null)));

    PCollection<TableRow> rowsFromBigQuery =
        mainPipeline.apply(
            "Read from BQ Storage API",
            BigQueryIO.readTableRowsWithSchema()
                .withTemplateCompatibility() // fixes BigQueryStorageSourceBase.split error
                .from(bigQueryTableProvider)
                .withoutValidation()
                .withMethod(BigQueryIO.TypedRead.Method.DIRECT_READ));

    Integer shardSize = geShardSize(prop, "rows.shard.size");

    PCollection<KV<String, Table>> shardedDLPTables =
        rowsFromBigQuery.apply(
            "Shard BigQuery Rows",
            BigQueryRowsDLPBatchTransformer.of(
                shardSize,
                getBatchSize(prop, "rows.batch.size"),
                getSampleSize(prop, "rows.sample.size")));

    PCollection<KV<String, List<Finding>>> dlpDCColumnFindings =
        shardedDLPTables.apply(
            "DLP Inspection",
            ParDo.of(
                new DLPInspectionDoFn(
                    options.getDlpProjectId(), options.getInspectTemplateName())));

    PCollection<KV<String, DataCatalogColumnFinding>> combinedResults =
        dlpDCColumnFindings.apply("Combine Results", DataCatalogFindingsCombiner.of(shardSize));

    combinedResults
        .apply("Wait Setup Flow", Wait.on(setupFlow))
        .apply(
            "Data Catalog Tag Ingestion",
            // Create Data Catalog Tags based on findings.
            ParDo.of(
                new DataCatalogTagIngestionDoFn(
                    options.getDlpProjectId(),
                    options.getDlpRunName(),
                    options.getTagTemplateSuffix(),
                    bigQueryTableProvider,
                    null)));

    return mainPipeline.run();
  }

  private static Integer geShardSize(Properties prop, String key) {
    return getPropertiesInt(prop, key, "10");
  }

  private static Integer getBatchSize(Properties prop, String key) {
    return getPropertiesInt(prop, key, "1000");
  }

  private static Integer getSampleSize(Properties prop, String key) {
    return getPropertiesInt(prop, key, "0");
  }

  private static Integer getPropertiesInt(Properties prop, String key, String defaultValue) {
    return Integer.valueOf(prop.getProperty(key, defaultValue));
  }
}
