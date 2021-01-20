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

import static com.google.protobuf.util.Timestamps.fromMillis;
import static java.lang.System.currentTimeMillis;

import com.google.cloud.datacatalog.v1beta1.CreateTagRequest;
import com.google.cloud.datacatalog.v1beta1.DataCatalogClient;
import com.google.cloud.datacatalog.v1beta1.Tag;
import com.google.cloud.datacatalog.v1beta1.TagField;
import com.google.cloud.datacatalog.v1beta1.TagTemplateName;
import com.google.cloud.datacatalog.v1beta1.UpdateTagRequest;
import com.google.privacy.dlp.v2.Likelihood;
import java.io.IOException;
import java.util.Optional;
import java.util.function.Predicate;
import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.values.KV;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link DataCatalogTagIngestionDoFn} class creates the Data Catalog Tags based on the input,
 * containing the merged results of {@link DataCatalogColumnFinding}. Data Catalog Entry need to
 * exist before this pipeline runs.
 */
public class DataCatalogTagIngestionDoFn extends DoFn<KV<String, DataCatalogColumnFinding>, Void> {
  private static final Logger LOG = LoggerFactory.getLogger(DataCatalogTagIngestionDoFn.class);

  private static final String LOCATION = "us-central1";
  private ValueProvider<String> dcProjectId;
  private ValueProvider<String> dlpRunName;
  private ValueProvider<String> tagTemplateSuffix;
  private ValueProvider<String> bigQueryTable;
  private String entryName;
  private ValueProvider<String> dataCatalogEntryName;
  private DataCatalogClient dataCatalogClient;

  public DataCatalogTagIngestionDoFn(
      ValueProvider<String> dcProjectId,
      ValueProvider<String> dlpRunName,
      ValueProvider<String> tagTemplateSuffix,
      ValueProvider<String> bigQueryTable,
      ValueProvider<String> dataCatalogEntryName) {
    this.dcProjectId = dcProjectId;
    this.dlpRunName = dlpRunName;
    this.dataCatalogClient = null;
    this.tagTemplateSuffix = tagTemplateSuffix;
    this.bigQueryTable = bigQueryTable;
    this.entryName = null;
    this.dataCatalogEntryName = dataCatalogEntryName;
  }

  @StartBundle
  public void startBundle() {
    try {
      this.dataCatalogClient = DataCatalogClient.create();
      if (dataCatalogEntryName != null) {
        this.entryName = dataCatalogEntryName.get();
      } else {
        this.entryName =
            EntryNameInitializer.lookupEntryName(this.bigQueryTable.get(), dataCatalogClient);
      }
    } catch (IOException e) {
      LOG.error("Failed to initialize Data Catalog", e);
      throw new RuntimeException(e);
    }
  }

  @FinishBundle
  public void finishBundle() throws Exception {
    if (this.dataCatalogClient != null) {
      this.dataCatalogClient.close();
    }
  }

  @ProcessElement
  public void processElement(ProcessContext c) {

    String key = c.element().getKey();
    DataCatalogColumnFinding dcColumnFinding = c.element().getValue();
    LOG.debug(
        "{} - columnKey: {} columnFindings: {}",
        LoggingPrefix.get(this.getClass().getSimpleName()),
        key,
        dcColumnFinding);

    try {
      String[] keySplit = key.split("@");
      String columnName = keySplit[0];
      String infoType = keySplit[1];

      TagField infoTypeValue = TagField.newBuilder().setStringValue(infoType).build();

      TagField jobName =
          TagField.newBuilder().setStringValue(c.getPipelineOptions().getJobName()).build();

      TagField dlpRunName = TagField.newBuilder().setStringValue(this.dlpRunName.get()).build();

      TagField highestLikelihoodValue =
          TagField.newBuilder()
              .setStringValue(dcColumnFinding.getHighestLikelihoodFound().name())
              .build();
      com.google.protobuf.Timestamp timestamp = fromMillis(currentTimeMillis());

      TagField syncExecutionValue = TagField.newBuilder().setTimestampValue(timestamp).build();

      TagField veryUnlikelyFindingValue =
          TagField.newBuilder().setDoubleValue(dcColumnFinding.getCountVeryUnlikely()).build();

      TagField unlikelyFinding =
          TagField.newBuilder().setDoubleValue(dcColumnFinding.getCountUnlikely()).build();

      TagField possibleFinding =
          TagField.newBuilder().setDoubleValue(dcColumnFinding.getCountPossible()).build();

      TagField likelyFinding =
          TagField.newBuilder().setDoubleValue(dcColumnFinding.getCountLikely()).build();

      TagField veryLikelyFinding =
          TagField.newBuilder().setDoubleValue(dcColumnFinding.getCountVeryLikely()).build();

      TagField undefinedFinding =
          TagField.newBuilder().setDoubleValue(dcColumnFinding.getCountUndefined()).build();

      Tag tag =
          Tag.newBuilder()
              .setTemplate(
                  TagTemplateName.of(
                          this.dcProjectId.get(),
                          LOCATION,
                          String.format(
                              "dlp_%s_info_type%s", infoType, this.tagTemplateSuffix.get()))
                      .toString())
              .putFields("info_type", infoTypeValue)
              .putFields("sync_job_name", jobName)
              .putFields("dlp_run_name", dlpRunName)
              .putFields("highest_likelihood_found", highestLikelihoodValue)
              .putFields("sync_execution_time", syncExecutionValue)
              .putFields("count_very_unlikely_finding", veryUnlikelyFindingValue)
              .putFields("count_unlikely_finding", unlikelyFinding)
              .putFields("count_possible_finding", possibleFinding)
              .putFields("count_likely_finding", likelyFinding)
              .putFields("count_very_likely_finding", veryLikelyFinding)
              .putFields("count_undefined_finding", undefinedFinding)
              .setColumn(columnName)
              .build();

      DataCatalogClient.ListTagsPagedResponse listTagsResponse =
          dataCatalogClient.listTags(this.entryName);

      Optional<Tag> existentTag = Optional.empty();

      for (DataCatalogClient.ListTagsPage pagedResponse : listTagsResponse.iteratePages()) {
        Predicate<Tag> tagEqualsPredicate =
            currentTag -> currentTag.getTemplate().equals(tag.getTemplate());

        Predicate<Tag> columnEqualsPredicate =
            currentTag -> currentTag.getColumn().equals(tag.getColumn());

        existentTag =
            pagedResponse.getResponse().getTagsList().stream()
                .parallel()
                .filter(tagEqualsPredicate.and(columnEqualsPredicate))
                .findAny();
      }

      LOG.debug("{} - INIT CALL to DC {}", LoggingPrefix.get(this.getClass().getSimpleName()), key);

      if (existentTag.isPresent()) {
        UpdateTagRequest updateTagRequest =
            UpdateTagRequest.newBuilder()
                .setTag(
                    Tag.newBuilder()
                        .mergeFrom(tag)
                        .putFields(
                            "highest_likelihood_found",
                            mergeHighestLikelihoodFound(existentTag.get(), tag))
                        .putFields(
                            "count_very_unlikely_finding",
                            mergeTagField("count_very_unlikely_finding", existentTag.get(), tag))
                        .putFields(
                            "count_unlikely_finding",
                            mergeTagField("count_unlikely_finding", existentTag.get(), tag))
                        .putFields(
                            "count_possible_finding",
                            mergeTagField("count_possible_finding", existentTag.get(), tag))
                        .putFields(
                            "count_likely_finding",
                            mergeTagField("count_likely_finding", existentTag.get(), tag))
                        .putFields(
                            "count_very_likely_finding",
                            mergeTagField("count_very_likely_finding", existentTag.get(), tag))
                        .putFields(
                            "count_undefined_finding",
                            mergeTagField("count_undefined_finding", existentTag.get(), tag))
                        .setName(existentTag.get().getName())
                        .build())
                .build();

        dataCatalogClient.updateTag(updateTagRequest);
      } else {
        CreateTagRequest createTagRequest =
            CreateTagRequest.newBuilder().setParent(this.entryName).setTag(tag).build();
        dataCatalogClient.createTag(createTagRequest);
      }

      LOG.debug("{} - END CALL to DC {}", LoggingPrefix.get(this.getClass().getSimpleName()), key);

    }
    catch (com.google.api.gax.rpc.AlreadyExistsException e) {
      // This shouldn't happen since tags are clean up
      // so we just ignore the error, in case there are
      // parallel executions.
      LOG.warn("Tag already exists, error: {}", e.getMessage());
    }
    catch (Exception e) {
      LOG.error("Request to Data Catalog failed", e);
      throw e;
    }
  }

  private TagField mergeHighestLikelihoodFound(Tag oldTag, Tag newTag) {
    String fieldName = "highest_likelihood_found";

    TagField oldTagField = oldTag.getFieldsMap().get(fieldName);
    TagField newTagField = newTag.getFieldsMap().get(fieldName);

    String oldLikelihood = oldTagField.getStringValue();
    String newLikelihood = newTagField.getStringValue();

    if (Likelihood.valueOf(oldLikelihood).getNumber()
        < Likelihood.valueOf(newLikelihood).getNumber()) {
      return newTagField;
    }

    return oldTagField;
  }

  private TagField mergeTagField(String fieldName, Tag oldTag, Tag newTag) {
    TagField oldTagField = oldTag.getFieldsMap().get(fieldName);
    TagField newTagField = newTag.getFieldsMap().get(fieldName);

    TagField mergedTagField =
        TagField.newBuilder()
            .setDoubleValue(oldTagField.getDoubleValue() + newTagField.getDoubleValue())
            .build();
    return mergedTagField;
  }
}
