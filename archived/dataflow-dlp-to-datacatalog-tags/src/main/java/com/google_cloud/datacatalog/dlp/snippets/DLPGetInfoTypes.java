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

import com.google.cloud.dlp.v2.DlpServiceClient;
import com.google.privacy.dlp.v2.GetInspectTemplateRequest;
import com.google.privacy.dlp.v2.InfoType;
import com.google.privacy.dlp.v2.InspectTemplate;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.stream.Collectors;
import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.transforms.DoFn;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link DLPGetInfoTypes} class executes get Inspection Template request by calling DLP api.
 * This DoFn ouptputs List<String> of DLP InfoTypes mapped to the Inspection Template.
 */
public class DLPGetInfoTypes extends DoFn<Integer, List<String>> {
  private static final Logger LOG = LoggerFactory.getLogger(DLPGetInfoTypes.class);

  private ValueProvider<String> inspectTemplateName;
  private DlpServiceClient dlpServiceClient;
  private GetInspectTemplateRequest request;

  public DLPGetInfoTypes(ValueProvider<String> inspectTemplateName) {
    this.inspectTemplateName = inspectTemplateName;
    this.dlpServiceClient = null;
  }

  @Setup
  public void setup() {
    this.request =
        GetInspectTemplateRequest.newBuilder().setName(inspectTemplateName.get()).build();
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
  public void processElement(ProcessContext c) {
    LOG.debug("{} start process", LoggingPrefix.get(this.getClass().getSimpleName()));

    try {
      LOG.debug("{} - INIT CALL to DLP", LoggingPrefix.get(this.getClass().getSimpleName()));
      InspectTemplate response = this.dlpServiceClient.getInspectTemplate(request);

      LOG.debug("{} - END CALL to DLP", LoggingPrefix.get(this.getClass().getSimpleName()));

      List<String> infoTypeNames =
          response.getInspectConfig().getInfoTypesList().stream()
              .map(InfoType::getName)
              .collect(Collectors.toList());

      LOG.debug(
          "{} - info types: {}", LoggingPrefix.get(this.getClass().getSimpleName()), infoTypeNames);

      c.output(infoTypeNames);
    } catch (Exception e) {
      LOG.error("Request to DLP failed", e);
      throw e;
    }
  }
}
