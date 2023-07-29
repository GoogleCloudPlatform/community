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

import org.apache.beam.sdk.transforms.Combine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link DLPColumnAggregatorFn} class executes combining logic, merging results that share the
 * same processing key. Ouptputs merged {@link DataCatalogColumnFinding}.
 */
public class DLPColumnAggregatorFn
    extends Combine.CombineFn<
        DataCatalogColumnFinding, DataCatalogColumnFinding, DataCatalogColumnFinding> {

  private static final Logger LOG = LoggerFactory.getLogger(DLPColumnAggregatorFn.class);

  @Override
  public DataCatalogColumnFinding createAccumulator() {
    LOG.debug("{} - Create accumulator", LoggingPrefix.get(this.getClass().getSimpleName()));
    return new DataCatalogColumnFinding();
  }

  @Override
  public DataCatalogColumnFinding addInput(
      DataCatalogColumnFinding accumulator, DataCatalogColumnFinding input) {
    LOG.debug("{} - input: {}", LoggingPrefix.get(this.getClass().getSimpleName()), input);
    accumulator.merge(input);
    return accumulator;
  }

  @Override
  public DataCatalogColumnFinding mergeAccumulators(
      Iterable<DataCatalogColumnFinding> accumulators) {
    LOG.debug("{} - Merging accumulators", LoggingPrefix.get(this.getClass().getSimpleName()));
    DataCatalogColumnFinding mergedDataCatalogColumnFinding = new DataCatalogColumnFinding();
    for (DataCatalogColumnFinding accumulator : accumulators) {
      mergedDataCatalogColumnFinding.merge(accumulator);
    }
    return mergedDataCatalogColumnFinding;
  }

  @Override
  public DataCatalogColumnFinding extractOutput(DataCatalogColumnFinding accumulator) {
    LOG.debug("{} - Extract output", LoggingPrefix.get(this.getClass().getSimpleName()));
    return accumulator;
  }
}
