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

import com.google.privacy.dlp.v2.Finding;
import java.util.List;
import org.apache.beam.sdk.transforms.Combine;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.PTransform;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataCatalogFindingsCombiner
    extends PTransform<
        PCollection<KV<String, List<Finding>>>, PCollection<KV<String, DataCatalogColumnFinding>>> {

  private static final String COMPOSE_KEY_SEPARATOR = "@";
  private static final Logger LOG = LoggerFactory.getLogger(DataCatalogFindingsCombiner.class);

  // Determine possible parallelism level
  private Integer shardsNumber;

  public DataCatalogFindingsCombiner(Integer shardsNumber) {
    super();
    this.shardsNumber = shardsNumber;
  }

  public static DataCatalogFindingsCombiner of(Integer shardsNumber) {
    return new DataCatalogFindingsCombiner(shardsNumber);
  }

  @Override
  public PCollection<KV<String, DataCatalogColumnFinding>> expand(
      PCollection<KV<String, List<Finding>>> dlpDCColumnFindings) {
    PCollection<KV<String, DataCatalogColumnFinding>> combinedResults =
        dlpDCColumnFindings.apply(
            "Combine Sharded Findings Results",
            Combine.<String, List<Finding>, DataCatalogColumnFinding>perKey(
                    new DLPInspectionAggregatorFn())
                .withHotKeyFanout(this.shardsNumber));

    PCollection<KV<String, DataCatalogColumnFinding>> combinedResultsByColumn =
        combinedResults
            .apply("Transform Columns key", ParDo.of(new TransformColumnKeys()))
            .apply(
                "Combine Column Results",
                Combine.<String, DataCatalogColumnFinding, DataCatalogColumnFinding>perKey(
                    new DLPColumnAggregatorFn()));

    return combinedResultsByColumn;
  }

  private static class TransformColumnKeys
      extends DoFn<KV<String, DataCatalogColumnFinding>, KV<String, DataCatalogColumnFinding>> {

    @ProcessElement
    public void processElement(ProcessContext c) {
      KV<String, DataCatalogColumnFinding> element = c.element();

      String key = element.getKey();

      String[] keySplit = key.split(COMPOSE_KEY_SEPARATOR);
      String columnName = keySplit[1];
      String infoType = keySplit[2];

      String newKey = columnName + COMPOSE_KEY_SEPARATOR + infoType;

      c.output(KV.of(newKey, element.getValue()));
    }
  }
}
