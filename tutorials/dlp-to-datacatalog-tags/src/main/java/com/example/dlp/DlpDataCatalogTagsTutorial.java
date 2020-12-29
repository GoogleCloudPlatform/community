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

package com.example.dlp;

// [START dlp_datacatalog_tags]

import com.google.api.client.googleapis.batch.BatchRequest;
import com.google.api.services.datacatalog.v1beta1.DataCatalog;
import com.google.api.services.datacatalog.v1beta1.model.GoogleCloudDatacatalogV1beta1Tag;
import com.google.api.services.datacatalog.v1beta1.model.GoogleCloudDatacatalogV1beta1TagField;
import com.google.cloud.ServiceOptions;
import com.google.cloud.datacatalog.v1beta1.CreateTagTemplateRequest;
import com.google.cloud.datacatalog.v1beta1.DataCatalogClient;
import com.google.cloud.datacatalog.v1beta1.FieldType;
import com.google.cloud.datacatalog.v1beta1.FieldType.PrimitiveType;
import com.google.cloud.datacatalog.v1beta1.LocationName;
import com.google.cloud.datacatalog.v1beta1.LookupEntryRequest;
import com.google.cloud.datacatalog.v1beta1.Tag;
import com.google.cloud.datacatalog.v1beta1.TagTemplate;
import com.google.cloud.datacatalog.v1beta1.TagTemplateField;
import com.google.cloud.dlp.v2.DlpServiceClient;
import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import com.google.privacy.dlp.v2.ContentItem;
import com.google.privacy.dlp.v2.FieldId;
import com.google.privacy.dlp.v2.Finding;
import com.google.privacy.dlp.v2.InspectContentRequest;
import com.google.privacy.dlp.v2.InspectContentResponse;
import com.google.privacy.dlp.v2.InspectResult;
import com.google.privacy.dlp.v2.Table;
import com.google.privacy.dlp.v2.Value;
import com.google.type.Date;
import com.simba.googlebigquery.jdbc42.DataSource;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.Predicate;
import java.util.stream.Collectors;
import org.apache.commons.lang3.StringUtils;

public class DlpDataCatalogTagsTutorial {

  private static boolean VERBOSE_OUTPUT = false; // toggle for more detailed output
  private static int MAX_REQUEST_BYTES = 480000; // max request size in bytes
  private static int MAX_REQUEST_CELLS = 50000; // max cell count per request

  private static Cache<String, Object> dataCatalogLocalCache =
      CacheBuilder.newBuilder().maximumSize(1000).expireAfterAccess(600, TimeUnit.SECONDS).build();

  private static DataCatalogClient dataCatalogClient;
  private static DlpServiceClient dlpServiceClient;
  private static DataCatalog dataCatalogBatchClient;

  static {
    try {
      dataCatalogClient = DataCatalogClient.create();
      dlpServiceClient = DlpServiceClient.create();
      dataCatalogBatchClient = DataCatalogBatchClient.getBatchClient();
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  public static void inspectDatabase() {
    // TODO(developer): Replace these variables before running the sample.
    // leave empty for all databases.
    String dbName = "my-db";
    String dbType = "bigquery";
    // leave empty for all tables.
    String tableName = "my-table";
    Integer limitMax = 100;
    String inspectTemplate = "projects/my-project/inspectTemplates/my-inspect-template";
    Integer threadPoolSize = 5;
    String projectId = "my-project";
    Integer minThreshold = 10;

    inspectDatabase(
        dbName,
        dbType,
        tableName,
        limitMax,
        inspectTemplate,
        threadPoolSize,
        projectId,
        minThreshold);
  }

  // Will scan the Database using JDBC drivers and write column level tags in Data Catalog
  private static void inspectDatabase(
      String dbName,
      String dbType,
      String tableName,
      Integer limitMax,
      String inspectTemplate,
      Integer threadPoolSize,
      String projectId,
      Integer minThreshold) {

    // Whether to use tag templates named by infoType or generic
    boolean useInfoTypeTagTemplates = true;

    // generate a UUID as a tracking number for the scan job
    String runID = UUID.randomUUID().toString();
    try {

      String dataProjectId = ServiceOptions.getDefaultProjectId();

      Connection conn;
      String url;

      // Create data source
      if (dbType.equalsIgnoreCase("bigquery")) {
        url =
            String.format(
                "jdbc:bigquery://https://www.googleapis.com/bigquery/v2:443;OAuthType=3;ProjectId=%s;",
                projectId);
        DataSource ds = new com.simba.googlebigquery.jdbc42.DataSource();
        ds.setURL(url);
        conn = ds.getConnection();
        System.out.println(url);
      } else {
        throw new Exception("Must specify valid database type");
      }
      int countTablesScanned = 0;

      try {
        DatabaseMetaData databaseMetadata = conn.getMetaData();

        final ExecutorService executor =
            Executors.newFixedThreadPool(threadPoolSize); // it's just an arbitrary number
        final List<Future<?>> futures = new ArrayList<>();
        System.out.println("-----------------------------------------");
        System.out.println(" Start Run ID: " + runID);
        System.out.println("-----------------------------------------");

        // ------------------------------------------
        // 1 - Get table names in the current project
        // ------------------------------------------
        ResultSet tablesResultSet =
            databaseMetadata.getTables(conn.getCatalog(), null, "%", new String[]{"TABLE"});

        while (tablesResultSet.next()) {
          final String currentTable = tablesResultSet.getString(3);
          final String currentDatabaseName =
              dbType.equalsIgnoreCase("bigquery") ? tablesResultSet.getString(2) : dbName;

          final String currentUrl = url;

          // This filters out tables that do not meet the command line parameters. Note that
          // BigQuery is special here since it does support running all datasets at once.
          if (dbType.equalsIgnoreCase("bigquery")
              && dbName != null
              && !dbName.equalsIgnoreCase("")
              && !dbName.equalsIgnoreCase(currentDatabaseName)) {
            continue;
          } else if (tableName == null
              || tableName.equalsIgnoreCase("")
              || currentTable.equalsIgnoreCase(tableName)) {

            countTablesScanned++;

            // ------------------------------------------
            // 2 - Main logic to process each table.
            // ------------------------------------------
            // This next entire block runs as a "thread"
            Future<?> future =
                executor.submit(
                    processTable(
                        dbType,
                        limitMax,
                        inspectTemplate,
                        projectId,
                        minThreshold,
                        useInfoTypeTagTemplates,
                        runID,
                        dataProjectId,
                        currentTable,
                        currentDatabaseName,
                        currentUrl));
            futures.add(future);
          }
        }
        for (Future<?> future : futures) {
          try {
            future.get(300, TimeUnit.SECONDS); // do anything you need, e.g. isDone(), ...
          } catch (InterruptedException | ExecutionException e) {
            System.out.println("Runnable aborted took more than 60 seconds: ");
            e.printStackTrace();
          }
        }
        executor.shutdown();
      } catch (Exception e) {
        System.err.println(e.getMessage());
      }
      conn.close();
      System.out.println("");
      System.out.println("-----------------------------------------");
      System.out.println(" " + countTablesScanned + " tables inspected");
      System.out.println(" End Run ID: " + runID);
      System.out.println("-----------------------------------------");

    } catch (Exception e) {
      System.out.println("Error in inspectDatabase: " + e.getMessage());
    } finally {
      dataCatalogClient.close();
      dlpServiceClient.close();
    }
  }

  private static Runnable processTable(
      String dbType,
      Integer limitMax,
      String inspectTemplate,
      String projectId,
      Integer minThreshold,
      boolean useInfoTypeTagTemplates,
      String runID,
      String dataProjectId,
      String currentTable,
      String currentDatabaseName,
      String currentUrl) {
    return () -> {
      if (VERBOSE_OUTPUT) {
        System.out.println(
            ">> Runnable started for: "
                + currentTable
                + " on thread: "
                + Thread.currentThread().getName());
      }

      Connection connInside = null;
      try {
        System.out.print(
            "|"
                + System.lineSeparator()
                + "> DLP infoType Profile: ["
                + currentDatabaseName
                + "]["
                + currentTable
                + "]");

        // Doing a simple selet * with a limit with no strict order.
        // ------------------------------------------
        // 2.1 - Execute query on table.
        // ------------------------------------------
        String sqlQuery = "SELECT * from " + currentTable + " limit " + limitMax;
        // Bigquery is a special on how it handles the "dataset" name
        if (dbType.equalsIgnoreCase("bigquery")) {
          DataSource ds2 = new DataSource();
          ds2.setURL(currentUrl);
          connInside = ds2.getConnection();
          sqlQuery =
              // ADD ` to escape reserved keywords.
              "SELECT * from " + "`" + currentDatabaseName + "`" + "." + "`" + currentTable +
                  "`" + " limit " + limitMax;
        }

        Statement stmt = connInside.createStatement();
        ResultSet rs;
        rs = stmt.executeQuery(sqlQuery);
        ResultSetMetaData rsmd = rs.getMetaData();
        int columnsNumber = rsmd.getColumnCount();
        String headerNames = "";

        for (int i = 1; i <= columnsNumber; i++) {
          if (i > 1) {
            headerNames = headerNames + "," + rsmd.getColumnName(i);
          } else {
            headerNames = rsmd.getColumnName(i);
          }
        }
        List<FieldId> headers =
            Arrays.stream(headerNames.split(","))
                .map(header -> FieldId.newBuilder().setName(header).build())
                .collect(Collectors.toList());

        // ------------------------------------------
        // 2.2 - Convert table into DLP TABLE.
        // ------------------------------------------
        // This next block converts data from ResultSet into CSV then into DLP
        // Table. This could likely be optimized but I did this in order to be
        // flexible and support other types like raw CSV reads.
        List<Table.Row> rows = new ArrayList<>();
        while (rs.next()) {
          String rowS = "";
          for (int i = 1; i <= columnsNumber; i++) {
            String theValue = rs.getString(i);
            if (theValue == null) {
              theValue = "";
            }
            if (i > 1) {
              rowS = rowS + "," + theValue.replace(",", "-");
            } else {
              rowS = theValue.replace(",", "-");
            }
          }
          rows.add(convertCsvRowToTableRow(rowS));
        }

        // Close connection earlier to use resources better.
        connInside.close();

        // This loop will process every row but will attempt to split each request
        // so that it does not go above the DLP max request size and cell count
        if (VERBOSE_OUTPUT) {
          System.out.print("..(Inspecting Data).");
        }

        // ------------------------------------------
        // 2.3 - CALL DLP and get Findings results.
        // ------------------------------------------
        int sentCount = 0;
        int prevSentCount = 0;
        java.util.Hashtable<String, InspectResult> splitMap =
            new java.util.Hashtable<String, InspectResult>();
        int splitTotal = 0;
        while (sentCount < rows.size()) {
          splitTotal++;
          try {
            List<Table.Row> subRows = getMaxRows(rows, sentCount, headers.size());
            prevSentCount = sentCount;
            sentCount = sentCount + subRows.size();
            splitMap.put(
                "result" + sentCount,
                inspectRows(getProjectName(dataProjectId), inspectTemplate, headers, subRows));
            if (VERBOSE_OUTPUT) {
              System.out.println("|");
              System.out.println(
                  "[ Request Size ("
                      + currentDatabaseName
                      + ":"
                      + currentTable
                      + "): request#"
                      + splitTotal
                      + " | start-row="
                      + sentCount
                      + " | row-count="
                      + subRows.size()
                      + " | cell-count="
                      + subRows.size() * headers.size()
                      + "]");
            }
          } catch (Exception err) {
            if (err.getMessage().contains("exceeds limit")
                || err.getMessage().contains("only 50,000 table values are allowed")) {
              // This message should not happen since we are measuring size before
              // sending.  So if it happens, it is a hard fail as something is
              // wrong.
              System.out.println("|");
              System.out.print("*** Fatal Error ***");
              System.out.print(
                  ">> DLP request size too big. Split Failed ["
                      + currentDatabaseName
                      + "]["
                      + currentTable
                      + "]");
              throw err;
            } else if (err.getMessage().contains("DEADLINE_EXCEEDED")) {
              // reset sentCount to prev so will make it retry;
              System.out.print("*** deadline_exceeded / retry ***");
              sentCount = prevSentCount;
              Thread.sleep(5000);
            } else {
              System.out.println("|");
              System.out.println(
                  "*** Unknown Fatal Error when trying to inspect data for ["
                      + currentDatabaseName
                      + "]["
                      + currentTable
                      + "] ***");
              throw err;
            }
          }
        }

        // ---------------------------------------------
        // 2.4 - Create Data Catalog Tags with Findings.
        // ----------------------------------------------
        writeFindingsToDataCatalog(
            projectId,
            runID,
            currentDatabaseName,
            currentTable,
            useInfoTypeTagTemplates,
            minThreshold,
            splitMap);
      } catch (Exception ec) {
        ec.printStackTrace();
      }
      if (VERBOSE_OUTPUT) {
        System.out.println(
            ">> Runnable done for: "
                + currentTable
                + " on thread: "
                + Thread.currentThread().getName());
      }
    };
  }

  // this method returns rows that are under the max bytes and cell count for a DLP request.
  private static List getMaxRows(List rows, int startRow, int headerCount) throws Exception {
    ArrayList<Table.Row> subRows = null;

    // estimate the request size
    int estimatedMaxRowsBytes =
        MAX_REQUEST_BYTES
            / (getBytesFromList(rows) / rows.size()); // average could be off if rows differ a lot
    int estimatedMaxRowsCells =
        MAX_REQUEST_CELLS
            / headerCount; // pretty close to the max since every rows has the same count

    // we want the smallest of the two
    int estimatedMaxRows = estimatedMaxRowsBytes;
    if (estimatedMaxRowsCells < estimatedMaxRowsBytes) {
      estimatedMaxRows = estimatedMaxRowsCells;
    }
    int estimatedEndRows = startRow + estimatedMaxRows;
    if (estimatedEndRows > rows.size()) {
      estimatedEndRows = rows.size();
    }
    subRows = new ArrayList<Table.Row>(rows.subList(startRow, estimatedEndRows));

    // in case something is too bill this will remove one row at a time until it's under the limits.
    while (getBytesFromList(subRows) > MAX_REQUEST_BYTES
        || (subRows.size() * headerCount) > MAX_REQUEST_CELLS) {
      if (subRows.size() > 0) {
        subRows.remove(subRows.size() - 1);
      } else {
        throw new Exception("Single Row greater than max size - not currently supported");
      }
    }
    return subRows;
  }

  // this methods calcualtes the total bytes of a list of rows.
  public static int getBytesFromList(List list) throws IOException {
    java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
    java.io.ObjectOutputStream out = new java.io.ObjectOutputStream(baos);
    out.writeObject(list);
    out.close();
    return baos.toByteArray().length;
  }

  private static String getProjectName(String inS) {
    String pid = "projects/" + inS;
    return pid;
  }

  // Takes rows/header and generates inspection results from DLP content.inspect
  private static InspectResult inspectRows(
      String parentName, String inspectTemplate, List<FieldId> headers, List<Table.Row> rows) {
    // Inspect the table for info types

    Table table = Table.newBuilder().addAllHeaders(headers).addAllRows(rows).build();

    ContentItem tableItem = ContentItem.newBuilder().setTable(table).build();
    InspectContentRequest request =
        InspectContentRequest.newBuilder()
            .setParent(parentName)
            .setInspectTemplateName(inspectTemplate)
            .setItem(tableItem)
            .build();
    try {
      InspectContentResponse response = dlpServiceClient.inspectContent(request);
      return response.getResult();
    } catch (Exception e2) {
      throw e2;
    }
  }

  // Writes column level tags to Data Catalog
  private static void writeFindingsToDataCatalog(
      String projectId,
      String runID,
      String dbName,
      String theTable,
      boolean useInfoTypeTagTemplates,
      int minThreshold,
      java.util.Hashtable<String, InspectResult> splitMap) {
    java.util.Hashtable<String, java.util.Hashtable> columnHash =
        new java.util.Hashtable<>();
    for (InspectResult result : splitMap.values()) {
      if (result != null && result.getFindingsCount() > 0) {
        for (Finding finding : result.getFindingsList()) {
          String column =
              finding
                  .getLocation()
                  .getContentLocations(0)
                  .getRecordLocation()
                  .getFieldId()
                  .getName();
          String infoType = finding.getInfoType().getName();
          java.util.Hashtable<String, Integer> tempCol = columnHash.get(column);
          if (tempCol == null) {
            tempCol = new java.util.Hashtable<String, Integer>();
          }
          Integer tempCount = tempCol.get(infoType);
          if (tempCount == null) {
            tempCount = 0;
          }
          tempCol.put(infoType, tempCount + 1);
          columnHash.put(column, tempCol);
        }
      }
    }

    BatchRequest batchRequest = DataCatalogBatchClient.getBatchRequest();
    for (String columnName : columnHash.keySet()) {
      if (VERBOSE_OUTPUT) {
        System.out.println(">> Column [" + columnName + "] has findings");
      } else {
        System.out.print(".");
      }
      java.util.Hashtable<String, Integer> tempCol = columnHash.get(columnName);

      int returnedThreshold = getTopInfoTypeMin(tempCol);

      if (returnedThreshold >= minThreshold) {
        try {
          String topInfoType = getTopInfoType(tempCol);
          String tagTemplateID = "dlp_tag_template_v2_column";
          String tagTemplateDisplayName = "Cloud DLP Tag V2 Template Column";
          if (useInfoTypeTagTemplates) {
            tagTemplateID = "dlp_" + topInfoType.toLowerCase();
            tagTemplateDisplayName = "Cloud DLP - " + topInfoType + "";
          }

          TagTemplate tagTemplate = null;

          String tagTemplateName =
              String.format("projects/%s/locations/us/tagTemplates/%s", projectId, tagTemplateID);
          // try to load the template
          try {

            Object cachedTagTemplate = dataCatalogLocalCache.getIfPresent(tagTemplateName);

            if (cachedTagTemplate != null) {
              tagTemplate = (TagTemplate) cachedTagTemplate;
              if (VERBOSE_OUTPUT) {
                System.out.println("[CacheHit] - getTagTemplate");
              }
            } else {
              tagTemplate = dataCatalogClient.getTagTemplate(tagTemplateName);
              dataCatalogLocalCache.put(tagTemplateName, tagTemplate);
              if (VERBOSE_OUTPUT) {
                System.out.println("[CacheMiss] - getTagTemplate");
              }
            }
          } catch (Exception e) {
            if (VERBOSE_OUTPUT) {
              System.out.println("Template not found, creating");
            } else {
              System.out.print(".");
            }
          }
          if (tagTemplate == null) {
            // Failed to load so Create the Tag Template.
            TagTemplateField topInfoTypeField =
                TagTemplateField.newBuilder()
                    .setDisplayName("top_info_type")
                    .setType(FieldType.newBuilder().setPrimitiveType(PrimitiveType.STRING).build())
                    .build();

            TagTemplateField infoTypesDetailsField =
                TagTemplateField.newBuilder()
                    .setDisplayName("info_types_detail")
                    .setType(FieldType.newBuilder().setPrimitiveType(PrimitiveType.STRING).build())
                    .build();
            TagTemplateField runIdField =
                TagTemplateField.newBuilder()
                    .setDisplayName("run_id")
                    .setType(FieldType.newBuilder().setPrimitiveType(PrimitiveType.STRING).build())
                    .build();

            TagTemplateField lastUpdatedField =
                TagTemplateField.newBuilder()
                    .setDisplayName("last_updated")
                    .setType(FieldType.newBuilder().setPrimitiveType(PrimitiveType.STRING).build())
                    .build();

            tagTemplate =
                TagTemplate.newBuilder()
                    .setDisplayName(tagTemplateDisplayName)
                    .putFields("top_info_type", topInfoTypeField)
                    .putFields("info_types_detail", infoTypesDetailsField)
                    .putFields("last_updated", lastUpdatedField)
                    .putFields("run_id", runIdField)
                    .build();

            CreateTagTemplateRequest createTagTemplateRequest =
                CreateTagTemplateRequest.newBuilder()
                    .setParent(
                        LocationName.newBuilder()
                            .setProject(projectId)
                            .setLocation("us")
                            .build()
                            .toString())
                    .setTagTemplateId(tagTemplateID)
                    .setTagTemplate(tagTemplate)
                    .build();

            // when running with many threads, it's possible that a new template gets created at the
            // same time. So we want to catch this.
            try {
              tagTemplate = dataCatalogClient.createTagTemplate(createTagTemplateRequest);
              if (VERBOSE_OUTPUT) {
                System.out.println(String.format("Created template: %s", tagTemplate.getName()));
              } else {
                System.out.print("+");
              }
            } catch (Exception e) {
              // this just means template is already there.
              // In the case other thread creates the template, we need to fill the template name
              // used by the Tags.
              if (tagTemplate != null && StringUtils.isBlank(tagTemplate.getName())) {
                tagTemplate = TagTemplate.newBuilder().mergeFrom(tagTemplate).
                    setName(tagTemplateName).build();
              }
            }
          }

          // -------------------------------
          // Lookup Data Catalog's Entry referring to the table.
          // -------------------------------
          String linkedResource =
              String.format(
                  "//bigquery.googleapis.com/projects/%s/datasets/%s/tables/%s",
                  projectId, dbName, theTable);
          LookupEntryRequest lookupEntryRequest =
              LookupEntryRequest.newBuilder().setLinkedResource(linkedResource).build();

          Object cachedEntry = dataCatalogLocalCache.getIfPresent(linkedResource);

          com.google.cloud.datacatalog.v1beta1.Entry tableEntry = null;

          if (cachedEntry != null) {
            tableEntry = (com.google.cloud.datacatalog.v1beta1.Entry) cachedEntry;
            if (VERBOSE_OUTPUT) {
              System.out.println("[CacheHit] - lookupEntry");
            }
          } else {
            tableEntry = dataCatalogClient.lookupEntry(lookupEntryRequest);
            dataCatalogLocalCache.put(linkedResource, tableEntry);
            if (VERBOSE_OUTPUT) {
              System.out.println("[CacheMiss] - lookupEntry");
            }
          }

          // -------------------------------
          // Attach a Tag to the table.
          // -------------------------------
          GoogleCloudDatacatalogV1beta1Tag tag = new GoogleCloudDatacatalogV1beta1Tag();
          tag.setTemplate(tagTemplate.getName());
          Map<String, GoogleCloudDatacatalogV1beta1TagField> fields = new HashMap<>();

          fields.put(
              "top_info_type",
              new GoogleCloudDatacatalogV1beta1TagField().setStringValue(topInfoType));
          fields.put(
              "info_types_detail",
              new GoogleCloudDatacatalogV1beta1TagField()
                  .setStringValue(getInfoTypeDetail(tempCol)));
          fields.put(
              "last_updated",
              new GoogleCloudDatacatalogV1beta1TagField()
                  .setStringValue(new java.util.Date().toString()));
          fields.put("run_id", new GoogleCloudDatacatalogV1beta1TagField().setStringValue(runID));

          tag.setFields(fields);
          tag.setColumn(columnName);

          // if create tag fails this likely means it already exists
          // Note currently API requires iterating through tags to find the right one
          String entryName = tableEntry.getName();
          DataCatalogClient.ListTagsPagedResponse listTags = null;

          Object cachedListTags = dataCatalogLocalCache.getIfPresent(entryName);

          if (cachedListTags != null) {
            listTags = (DataCatalogClient.ListTagsPagedResponse) cachedListTags;
            if (VERBOSE_OUTPUT) {
              System.out.println("[CacheHit] - listTags");
            }
          } else {
            listTags = dataCatalogClient.listTags(entryName);
            dataCatalogLocalCache.put(entryName, listTags);
            if (VERBOSE_OUTPUT) {
              System.out.println("[CacheMiss] - listTags");
            }
          }

          Optional<Tag> existentTag = Optional.empty();

          for (DataCatalogClient.ListTagsPage pagedResponse : listTags.iteratePages()) {
            Predicate<Tag> tagEqualsPredicate =
                currentTag -> currentTag.getTemplate().equalsIgnoreCase(tag.getTemplate());

            Predicate<Tag> columnEqualsPredicate =
                currentTag -> currentTag.getColumn().equalsIgnoreCase(tag.getColumn());

            existentTag =
                pagedResponse.getResponse().getTagsList().stream()
                    .parallel()
                    .filter(tagEqualsPredicate.and(columnEqualsPredicate))
                    .findAny();

            if (existentTag.isPresent()) {
              break;
            }
          }

          // -------------------------------------------
          // Create Batch request for Patch/Create Tag.
          // -------------------------------------------
          if (existentTag.isPresent()) {
            if (VERBOSE_OUTPUT) {
              System.out.print("Found existing tag template in this column...[Updating]...");
            } else {
              System.out.print(".");
            }
            dataCatalogBatchClient
                .projects()
                .locations()
                .entryGroups()
                .entries()
                .tags()
                .patch(existentTag.get().getName(), tag)
                .queue(batchRequest, DataCatalogBatchClient.updatedTagCallback);
          } else {
            dataCatalogBatchClient
                .projects()
                .locations()
                .entryGroups()
                .entries()
                .tags()
                .create(entryName, tag)
                .queue(batchRequest, DataCatalogBatchClient.createdTagCallback);
          }

        } catch (Exception err) {
          System.out.println("Error writing findings to DC ");
          err.printStackTrace();
        }
      } else {
        if (VERBOSE_OUTPUT) {
          System.out.println(">> Findings for ["
              + columnName + "] has threshold " + returnedThreshold
              + " when minimum threshold is " + minThreshold
          );
        }
      }
    }
    try {
      if (batchRequest.size() > 0) {
        batchRequest.execute();
      } else {
        if (VERBOSE_OUTPUT) {
          System.out.println(">> Not creating Data Catalog Tags for "
              + "[" + dbName + "]" + "[" + theTable + "]"
          );
        }
      }
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  private static String getTopInfoType(java.util.Hashtable<String, Integer> tempCol) {
    String maxInfoTypeName = null;
    int maxInt = 0;
    for (String infoTypeName : tempCol.keySet()) {
      if (maxInfoTypeName == null || tempCol.get(infoTypeName) > maxInt) {
        maxInfoTypeName = infoTypeName;
        maxInt = tempCol.get(infoTypeName);
      }
    }
    return maxInfoTypeName;
  }

  private static int getTopInfoTypeMin(java.util.Hashtable<String, Integer> tempCol) {
    String maxInfoTypeName = null;
    int maxInt = 0;
    for (String infoTypeName : tempCol.keySet()) {
      if (maxInfoTypeName == null || tempCol.get(infoTypeName) > maxInt) {
        maxInfoTypeName = infoTypeName;
        maxInt = tempCol.get(infoTypeName);
      }
    }
    return maxInt;
  }

  private static String getInfoTypeDetail(java.util.Hashtable<String, Integer> tempCol) {
    String infoTypeDetails = null;
    for (String infoTypeName : tempCol.keySet()) {
      if (infoTypeDetails == null) {
        infoTypeDetails = infoTypeName + "[" + tempCol.get(infoTypeName) + "]";
      } else {
        infoTypeDetails =
            infoTypeDetails + ", " + infoTypeName + "[" + tempCol.get(infoTypeName) + "]";
      }
    }
    return infoTypeDetails;
  }

  // Parse string to valid date, return null when invalid
  private static LocalDate getValidDate(String dateString) {
    try {
      return LocalDate.parse(dateString);
    } catch (DateTimeParseException e) {
      return null;
    }
  }

  private static Table.Row convertCsvRowToTableRow(String row) {
    // Complex split that allows quoted commas
    String[] values = row.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", -1);
    Table.Row.Builder tableRowBuilder = Table.Row.newBuilder();
    int i = 0;
    for (String value : values) {
      i++;
      LocalDate date = getValidDate(value);
      if (date != null) {
        // convert to com.google.type.Date
        Date dateValue =
            Date.newBuilder()
                .setYear(date.getYear())
                .setMonth(date.getMonthValue())
                .setDay(date.getDayOfMonth())
                .build();
        Value tableValue = Value.newBuilder().setDateValue(dateValue).build();
        tableRowBuilder.addValues(tableValue);
      } else {
        tableRowBuilder.addValues(Value.newBuilder().setStringValue(value).build());
      }
    }
    return tableRowBuilder.build();
  }

  public static void main(String[] args) throws Exception {

    java.util.Date startDate = new java.util.Date();
    System.out.println("[Start: " + startDate.toString() + "]");

    ParseArgs parseArgs = new ParseArgs(args).invoke();
    if (parseArgs.error()) {
      return;
    }

    String minThreshold = parseArgs.getMinThreshold();
    String projectId = parseArgs.getProjectId();
    String dbName = parseArgs.getDbName();
    String tableName = parseArgs.getTableName();
    String dbType = parseArgs.getDbType();
    String limitMax = parseArgs.getLimitMax();
    String inspectTemplate = parseArgs.getInspectTemplate();
    String threadPoolSize = parseArgs.getThreadPoolSize();

    System.out.println("Inspect SQL via JDBC V0.1");

    inspectDatabase(
        dbName,
        dbType,
        tableName,
        new Integer(limitMax),
        inspectTemplate,
        new Integer(threadPoolSize),
        projectId,
        new Integer(minThreshold));

    java.util.Date endDate = new java.util.Date();
    System.out.println("[End: " + endDate.toString() + "]");

    long diff = endDate.getTime() - startDate.getTime();

    long diffSeconds = diff / 1000 % 60;
    long diffMinutes = diff / (60 * 1000) % 60;
    long diffHours = diff / (60 * 60 * 1000) % 24;
    long diffDays = diff / (24 * 60 * 60 * 1000);

    System.out.print("[Duration: ");
    System.out.print("  " + diffDays + " days, ");
    System.out.print("  " + diffHours + " hours, ");
    System.out.print("  " + diffMinutes + " minutes, ");
    System.out.print("  " + diffSeconds + " seconds.");
    System.out.println("]");
  }
}

// [end dlp_datacatalog_tags]
