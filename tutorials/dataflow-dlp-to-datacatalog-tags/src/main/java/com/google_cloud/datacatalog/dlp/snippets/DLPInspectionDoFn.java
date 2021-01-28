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

import com.google.api.client.util.ExponentialBackOff;
import com.google.api.gax.rpc.ResourceExhaustedException;
import com.google.cloud.dlp.v2.DlpServiceClient;
import com.google.privacy.dlp.v2.ContentItem;
import com.google.privacy.dlp.v2.Finding;
import com.google.privacy.dlp.v2.InfoType;
import com.google.privacy.dlp.v2.InspectContentRequest;
import com.google.privacy.dlp.v2.InspectContentResponse;
import com.google.privacy.dlp.v2.ProjectName;
import com.google.privacy.dlp.v2.RecordLocation;
import com.google.privacy.dlp.v2.Table;
import java.io.IOException;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.beam.sdk.metrics.Distribution;
import org.apache.beam.sdk.metrics.Metrics;
import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.values.KV;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link DLPInspectionDoFn} class executes Inspection request by calling DLP api. It uses DLP
 * table as a content item as CSV file contains fully structured data. DLP templates need to exist
 * before this pipeline runs. As response from the API is received, this DoFn ouptputs KV of
 * composed key columnName@findingType with findings list as value.
 */
public class DLPInspectionDoFn extends DoFn<KV<String, Table>, KV<String, List<Finding>>> {
  private static final String COMPOSE_KEY_SEPARATOR = "@";

  private static final Logger LOG = LoggerFactory.getLogger(DLPInspectionDoFn.class);

  private ValueProvider<String> dlpProjectId;
  private ValueProvider<String> inspectTemplateName;
  private DlpServiceClient dlpServiceClient;
  private InspectContentRequest.Builder requestBuilder;
  private final Distribution numberOfRowsInspected =
      Metrics.distribution(DLPInspectionDoFn.class, "numberOfRowsInspectedDistro");
  private final Distribution numberOfBytesInspected =
      Metrics.distribution(DLPInspectionDoFn.class, "numberOfBytesInspectedDistro");

  public DLPInspectionDoFn(
      ValueProvider<String> dlpProjectId, ValueProvider<String> inspectTemplateName) {
    this.dlpProjectId = dlpProjectId;
    this.inspectTemplateName = inspectTemplateName;
    this.dlpServiceClient = null;
  }

  @Setup
  public void setup() {
    this.requestBuilder =
        InspectContentRequest.newBuilder()
            .setParent(ProjectName.of(this.dlpProjectId.get()).toString())
            .setInspectTemplateName(this.inspectTemplateName.get().toString());
  }

  @StartBundle
  public void startBundle() throws SQLException {

    try {
      this.dlpServiceClient = DlpServiceClient.create();

    } catch (IOException e) {
      LOG.error("Failed to create DLP Service Client", e);
      throw new RuntimeException(e);
    }
  }

  @FinishBundle
  public void finishBundle() throws Exception {
    if (this.dlpServiceClient != null) {
      this.dlpServiceClient.close();
    }
  }

  @ProcessElement
  public void processElement(ProcessContext c) throws IOException, InterruptedException {
    String key = c.element().getKey();
    Table nonEncryptedData = c.element().getValue();
    LOG.debug(
        "{} - Shard {} rows: {}",
        LoggingPrefix.get(this.getClass().getSimpleName()),
        key,
        nonEncryptedData.getRowsCount());
    ContentItem tableItem = ContentItem.newBuilder().setTable(nonEncryptedData).build();
    this.requestBuilder.setItem(tableItem);

    try {
      LOG.debug(
          "{} - INIT CALL to DLP {}", LoggingPrefix.get(this.getClass().getSimpleName()), key);
      InspectContentResponse response = callDLPInspectionWithBackoff();
      LOG.debug("{} - END CALL to DLP {}", LoggingPrefix.get(this.getClass().getSimpleName()), key);
      List<Finding> findingsList = response.getResult().getFindingsList();
      numberOfRowsInspected.update(nonEncryptedData.getRowsCount());
      numberOfBytesInspected.update(nonEncryptedData.toByteArray().length);

      Map<String, List<Finding>> dataCatalogColumnFindingsMap =
          groupFindingsByColumn(key, findingsList);

      for (Map.Entry<String, List<Finding>> entry : dataCatalogColumnFindingsMap.entrySet()) {
        LOG.debug(
            "{} - key {}, findings: {}",
            LoggingPrefix.get(this.getClass().getSimpleName()),
            entry.getKey(),
            entry.getValue().size());
        c.output(KV.of(entry.getKey(), entry.getValue()));
      }
    } catch (Exception e) {
      LOG.error("Request to DLP failed");
      e.printStackTrace();
      throw e;
    }
  }

  // DLP Content API has a 500req/min quota, so we do exponential backoff here.
  private InspectContentResponse callDLPInspectionWithBackoff()
      throws IOException, InterruptedException {
    ExponentialBackOff backoff =
        new ExponentialBackOff.Builder()
            .setInitialIntervalMillis(60000)
            .setMaxElapsedTimeMillis(900000)
            .setMaxIntervalMillis(600000)
            .setMultiplier(1.5)
            .setRandomizationFactor(0.5)
            .build();

    long currentBackoff = 0;
    int attemptNumber = 0;

    while (currentBackoff != -1) {
      try {
        return dlpServiceClient.inspectContent(this.requestBuilder.build());
      } catch (ResourceExhaustedException e) {
        LOG.warn("Request to DLP failed DEADLINE_EXCEEDED");
        currentBackoff = backoff.nextBackOffMillis();
        LOG.warn(
            "{} - Backoff: {}, Attempt: {}",
            LoggingPrefix.get(this.getClass().getSimpleName()),
            currentBackoff,
            ++attemptNumber);
        Thread.sleep(currentBackoff);
      }
    }

    throw new RuntimeException(
        String.format(
            "Waited: %sms giving up on this request", backoff.getCurrentIntervalMillis()));
  }

  private Map<String, List<Finding>> groupFindingsByColumn(String key, List<Finding> findingsList) {
    Map<String, List<Finding>> dataCatalogColumnFindingsMap = new HashMap<>();

    for (Finding f : findingsList) {
      RecordLocation recordLocation =
          f.getLocation().getContentLocationsList().get(0).getRecordLocation();
      String columnName = recordLocation.getFieldId().getName();

      InfoType infoType = f.getInfoType();

      String infoTypeName = infoType.getName().toLowerCase();

      // Create a composed key to parallelize processing.
      String composedKey =
          key + COMPOSE_KEY_SEPARATOR + columnName + COMPOSE_KEY_SEPARATOR + infoTypeName;

      List<Finding> findingsByColumnList =
          dataCatalogColumnFindingsMap.getOrDefault(composedKey, new ArrayList<>());

      findingsByColumnList.add(f);

      dataCatalogColumnFindingsMap.put(composedKey, findingsByColumnList);
    }
    return dataCatalogColumnFindingsMap;
  }
}
