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

import com.google.cloud.datacatalog.v1beta1.CreateTagTemplateRequest;
import com.google.cloud.datacatalog.v1beta1.DataCatalogClient;
import com.google.cloud.datacatalog.v1beta1.FieldType;
import com.google.cloud.datacatalog.v1beta1.LocationName;
import com.google.cloud.datacatalog.v1beta1.Tag;
import com.google.cloud.datacatalog.v1beta1.TagTemplate;
import com.google.cloud.datacatalog.v1beta1.TagTemplateField;
import com.google.cloud.datacatalog.v1beta1.TagTemplateName;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;
import java.util.stream.Collectors;
import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.transforms.DoFn;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link DataCatalogInitTemplatesDoFn} class creates the Data Catalog Templates used by the
 * Data Catalog Tags by calling DC api.
 */
public class DataCatalogInitTemplatesDoFn extends DoFn<List<String>, List<String>> {
  private static final Logger LOG = LoggerFactory.getLogger(DataCatalogInitTemplatesDoFn.class);

  private static final String LOCATION = "us-central1";
  private ValueProvider<String> dcProjectId;
  private DataCatalogClient dataCatalogClient;
  private ValueProvider<String> tagTemplateSuffix;
  private ValueProvider<String> bigQueryTable;
  private ValueProvider<String> dataCatalogEntryName;
  private String entryName;

  public DataCatalogInitTemplatesDoFn(
      ValueProvider<String> dcProjectId,
      ValueProvider<String> tagTemplateSuffix,
      ValueProvider<String> bigQueryTable,
      ValueProvider<String> dataCatalogEntryName) {
    this.dcProjectId = dcProjectId;
    this.dataCatalogClient = null;
    this.entryName = null;
    this.tagTemplateSuffix = tagTemplateSuffix;
    this.bigQueryTable = bigQueryTable;
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
      LOG.error("Failed to create Data Catalog Service Client", e);
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

    List<String> infoTypes = c.element();
    LOG.debug("{} - infoTypes: {}", LoggingPrefix.get(this.getClass().getSimpleName()), infoTypes);

    try {
      TagTemplateField infoTypeField =
          TagTemplateField.newBuilder()
              .setDisplayName("DLP info type")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.STRING).build())
              .build();

      TagTemplateField jobName =
          TagTemplateField.newBuilder()
              .setDisplayName("Sync Job Name")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.STRING).build())
              .build();

      TagTemplateField dlpRunName =
          TagTemplateField.newBuilder()
              .setDisplayName("DLP Run Name")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.STRING).build())
              .build();

      TagTemplateField highestLikelihoodFoundField =
          TagTemplateField.newBuilder()
              .setDisplayName("Highest level of likelihood found on the column")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.STRING).build())
              .build();

      TagTemplateField findingsField =
          TagTemplateField.newBuilder()
              .setDisplayName("List of findings")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.STRING).build())
              .build();

      TagTemplateField veryUnlikelyFinding =
          TagTemplateField.newBuilder()
              .setDisplayName("Count Very Unlikely Finding")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.DOUBLE).build())
              .build();

      TagTemplateField unlikelyFinding =
          TagTemplateField.newBuilder()
              .setDisplayName("Count Unlikely Finding")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.DOUBLE).build())
              .build();

      TagTemplateField possibleFinding =
          TagTemplateField.newBuilder()
              .setDisplayName("Count Possible Finding")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.DOUBLE).build())
              .build();

      TagTemplateField likelyFinding =
          TagTemplateField.newBuilder()
              .setDisplayName("Count Likely Finding")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.DOUBLE).build())
              .build();

      TagTemplateField veryLikelyFinding =
          TagTemplateField.newBuilder()
              .setDisplayName("Count Very Likely Finding")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.DOUBLE).build())
              .build();

      TagTemplateField undefinedFinding =
          TagTemplateField.newBuilder()
              .setDisplayName("Count Undefined Finding")
              .setType(
                  FieldType.newBuilder().setPrimitiveType(FieldType.PrimitiveType.DOUBLE).build())
              .build();

      TagTemplateField syncExecutionTime =
          TagTemplateField.newBuilder()
              .setDisplayName("Sync Execution time")
              .setType(
                  FieldType.newBuilder()
                      .setPrimitiveType(FieldType.PrimitiveType.TIMESTAMP)
                      .build())
              .build();

      List<String> tagTemplatesNames = new ArrayList<>();

      for (String infoType : infoTypes) {
        TagTemplate tagTemplate =
            TagTemplate.newBuilder()
                .setDisplayName(String.format("%s", infoType.toUpperCase()))
                .putFields("info_type", infoTypeField)
                .putFields("highest_likelihood_found", highestLikelihoodFoundField)
                .putFields("findings", findingsField)
                .putFields("count_very_unlikely_finding", veryUnlikelyFinding)
                .putFields("count_unlikely_finding", unlikelyFinding)
                .putFields("count_possible_finding", possibleFinding)
                .putFields("count_likely_finding", likelyFinding)
                .putFields("count_very_likely_finding", veryLikelyFinding)
                .putFields("count_undefined_finding", undefinedFinding)
                .putFields("sync_execution_time", syncExecutionTime)
                .putFields("sync_job_name", jobName)
                .putFields("dlp_run_name", dlpRunName)
                .build();

        CreateTagTemplateRequest createTagTemplateRequest =
            CreateTagTemplateRequest.newBuilder()
                .setParent(
                    LocationName.newBuilder()
                        .setProject(this.dcProjectId.get())
                        .setLocation(LOCATION)
                        .build()
                        .toString())
                .setTagTemplateId(
                    String.format(
                        "dlp_%s_info_type%s", infoType.toLowerCase(), this.tagTemplateSuffix.get()))
                .setTagTemplate(tagTemplate)
                .build();

        LOG.debug(
            "{} - INIT CALL to DC {}",
            LoggingPrefix.get(this.getClass().getSimpleName()),
            createTagTemplateRequest);

        TagTemplate createdTagTemplate = createTagTemplate(createTagTemplateRequest);
        tagTemplatesNames.add(createdTagTemplate.getName());

        cleanUpTagFromEntry(createdTagTemplate);
      }

      LOG.debug(
          "{} - Templates initialized: {}",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          tagTemplatesNames);

      c.output(tagTemplatesNames);
    } catch (Exception e) {
      LOG.error("Request to Data Catalog failed", e);
      throw e;
    }
  }

  private TagTemplate createTagTemplate(CreateTagTemplateRequest createTagTemplateRequest) {
    try {
      TagTemplate tagTemplate = dataCatalogClient.createTagTemplate(createTagTemplateRequest);

      LOG.debug(
          "{} - END CALL to DC template created: {}",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          tagTemplate.getName());

      return tagTemplate;
    } catch (Exception e) {
      LOG.debug(
          "{} - END CALL to DC template already exists!",
          LoggingPrefix.get(this.getClass().getSimpleName()));

      TagTemplate inputTagTemplate = createTagTemplateRequest.getTagTemplate();

      // Return input tagTemplate if it already exists, and build the template name.
      return TagTemplate.newBuilder()
          .mergeFrom(inputTagTemplate)
          .setName(
              TagTemplateName.of(
                      this.dcProjectId.get(), LOCATION, createTagTemplateRequest.getTagTemplateId())
                  .toString())
          .build();
    }
  }

  private void cleanUpTagFromEntry(TagTemplate currentTagTemplate) {
    DataCatalogClient.ListTagsPagedResponse listTagsResponse =
        dataCatalogClient.listTags(this.entryName);

    List<Tag> existentTags = new ArrayList<>();

    LOG.debug(
        "{} - Will clean up tags from template name {}",
        LoggingPrefix.get(this.getClass().getSimpleName()),
        currentTagTemplate.getName());

    for (DataCatalogClient.ListTagsPage pagedResponse : listTagsResponse.iteratePages()) {
      Predicate<Tag> tagEqualsPredicate =
          currentTag -> currentTag.getTemplate().equals(currentTagTemplate.getName());

      final List<Tag> tagsList = pagedResponse.getResponse().getTagsList();

      LOG.debug(
          "{} - Existent tags parent templates: {}",
          LoggingPrefix.get(this.getClass().getSimpleName()),
          tagsList.stream().map(Tag::getTemplate).collect(Collectors.toList()));

      existentTags.addAll(tagsList.stream()
              .parallel()
              .filter(tagEqualsPredicate)
              .collect(Collectors.toList()));
    }

    try {
      for (Tag tag : existentTags) {
        dataCatalogClient.deleteTag(tag.getName());
        LOG.debug(
            "{} - tag deleted: {}",
            LoggingPrefix.get(this.getClass().getSimpleName()),
            tag.getName());
      }
    } catch (Exception e) {
      LOG.error("Error deleting tag", e);
    }
  }
}
