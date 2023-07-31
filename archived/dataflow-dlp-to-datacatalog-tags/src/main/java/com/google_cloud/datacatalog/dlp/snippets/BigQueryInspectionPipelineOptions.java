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

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.Validation;
import org.apache.beam.sdk.options.ValueProvider;

/**
 * The {@link BigQueryInspectionPipelineOptions} interface provides the custom execution options
 * passed by the executor at the command-line.
 */
public interface BigQueryInspectionPipelineOptions extends DataflowPipelineOptions {
  @Description("BigQuery Table that will be used for inspection")
  @Validation.Required
  ValueProvider<String> getBigQueryTable();

  void setBigQueryTable(ValueProvider<String> value);

  @Description("DLP Run name to track executions")
  @Validation.Required
  ValueProvider<String> getDlpRunName();

  void setDlpRunName(ValueProvider<String> value);

  @Description("Project id to be used for DLP Inspection")
  @Validation.Required
  ValueProvider<String> getDlpProjectId();

  void setDlpProjectId(ValueProvider<String> value);

  @Description(
      "DLP Inspect Template to be used for API request "
          + "(e.g.projects/{project_id}/inspectTemplates/{inspectTemplateId}")
  @Validation.Required
  ValueProvider<String> getInspectTemplateName();

  void setInspectTemplateName(ValueProvider<String> value);

  @Description("Data Catalog Tag Template suffix, used on the Template creation ")
  @Default.String("")
  ValueProvider<String> getTagTemplateSuffix();

  void setTagTemplateSuffix(ValueProvider<String> value);
}
