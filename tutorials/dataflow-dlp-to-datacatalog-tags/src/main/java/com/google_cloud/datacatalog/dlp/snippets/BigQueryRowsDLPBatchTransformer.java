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
import com.google.privacy.dlp.v2.FieldId;
import com.google.privacy.dlp.v2.Table;
import com.google.privacy.dlp.v2.Value;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Random;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.GroupIntoBatches;
import org.apache.beam.sdk.transforms.PTransform;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Sample;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Batch clicks into packs of BATCH_SIZE size */
public class BigQueryRowsDLPBatchTransformer
    extends PTransform<PCollection<TableRow>, PCollection<KV<String, Table>>> {
  private static final Logger LOG = LoggerFactory.getLogger(BigQueryRowsDLPBatchTransformer.class);

  // Determine possible parallelism level
  private Integer shardsNumber;
  private Integer batchSize;
  private Integer sampleRows;

  public BigQueryRowsDLPBatchTransformer(
      Integer shardsNumber, Integer batchSize, Integer sampleRows) {
    super();
    this.shardsNumber = shardsNumber;
    this.batchSize = batchSize;
    this.sampleRows = sampleRows;
  }

  public static BigQueryRowsDLPBatchTransformer of(
      Integer shardsNumber, Integer batchSize, Integer sampleRows) {
    return new BigQueryRowsDLPBatchTransformer(shardsNumber, batchSize, sampleRows);
  }

  private static List<Table.Row> convertBQRowsToDLPTableRows(List<TableRow> bqRows) {
    List<Table.Row> rows = new ArrayList<>();
    for (TableRow row : bqRows) {
      Table.Row.Builder tableRowBuilder = Table.Row.newBuilder();

      Collection<Object> rowValues = row.values();

      for (Object rowValue : rowValues) {
        tableRowBuilder.addValues(Value.newBuilder().setStringValue(rowValue.toString()).build());
      }
      rows.add(tableRowBuilder.build());
    }
    return rows;
  }

  @Override
  public PCollection<KV<String, Table>> expand(PCollection<TableRow> input) {
    PCollection<TableRow> bigQueryRows = null;

    if (this.sampleRows > 0) {
      LOG.debug(
          "{} Sampling by {} rows",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          this.sampleRows);
      bigQueryRows = input.apply("Sample Rows", Sample.any(this.sampleRows));
    } else {
      LOG.debug(
          "{} Sampling disabled: {} rows",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          this.sampleRows);
      bigQueryRows = input;
    }

    PCollection<KV<String, Iterable<TableRow>>> batchedRows =
        bigQueryRows
            .apply("Bucket Rows", ParDo.of(new AssignRandomKeys(this.shardsNumber)))
            .apply(GroupIntoBatches.ofSize(this.batchSize));
    return batchedRows.apply(ParDo.of(new ConvertAndShardDLPTables()));
  }

  /** Assigns random integer between zero and shardsNumber */
  private static class AssignRandomKeys extends DoFn<TableRow, KV<String, TableRow>> {
    private Integer shardsNumber;
    private Random random;

    AssignRandomKeys(Integer shardsNumber) {
      super();
      this.shardsNumber = shardsNumber;
      LOG.debug(
          "{} Sharding value: {}",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          this.shardsNumber);
    }

    @Setup
    public void setup() {
      random = new Random();
    }

    @ProcessElement
    public void processElement(ProcessContext c) {
      TableRow row = c.element();
      KV kv = KV.of(String.valueOf(random.nextInt(this.shardsNumber)), row);
      c.output(kv);
    }
  }

  private static class ConvertAndShardDLPTables
      extends DoFn<KV<String, Iterable<TableRow>>, KV<String, Table>> {

    @ProcessElement
    public void processElement(ProcessContext c) {
      KV<String, Iterable<TableRow>> element = c.element();

      List<TableRow> bqRows =
          StreamSupport.stream(element.getValue().spliterator(), false)
              .collect(Collectors.toList());

      // Sample first result
      TableRow tableRow = bqRows.get(0);

      List<String> headers = new ArrayList<>(tableRow.keySet());

      String shard = element.getKey();
      LOG.debug(
          "{} shard: {}, row size: {}",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          shard,
          bqRows.size());

      List<FieldId> dlpTableHeaders =
          headers.stream()
              .map(headerName -> FieldId.newBuilder().setName(headerName).build())
              .collect(Collectors.toList());

      List<Table.Row> rows = convertBQRowsToDLPTableRows(bqRows);

      Table dlpTable = Table.newBuilder().addAllHeaders(dlpTableHeaders).addAllRows(rows).build();

      c.output(KV.of(shard, dlpTable));
    }
  }
}
