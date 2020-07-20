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

// [START HybridInspectSql]

import com.google.cloud.ServiceOptions;
import com.google.cloud.dlp.v2.DlpServiceClient;
import com.google.cloud.secretmanager.v1.AccessSecretVersionRequest;
import com.google.cloud.secretmanager.v1.AccessSecretVersionResponse;
import com.google.cloud.secretmanager.v1.SecretManagerServiceClient;
import com.google.cloud.secretmanager.v1.SecretVersionName;
import com.google.privacy.dlp.v2.Container;
import com.google.privacy.dlp.v2.ContentItem;
import com.google.privacy.dlp.v2.FieldId;
import com.google.privacy.dlp.v2.HybridContentItem;
import com.google.privacy.dlp.v2.HybridFindingDetails;
import com.google.privacy.dlp.v2.HybridInspectDlpJobRequest;
import com.google.privacy.dlp.v2.HybridInspectResponse;
import com.google.privacy.dlp.v2.Table;
import com.google.privacy.dlp.v2.Value;
import com.google.type.Date;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import jdk.internal.joptsimple.internal.Strings;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

public class HybridInspectSql {

  private static final Logger LOG = Logger.getLogger(HybridInspectSql.class.getName());
  private static final Level LOG_LEVEL = Level.WARNING;

  public static final String JDBC_URL_POSTGRESQL = "jdbc:postgresql://%s/%s";
  public static final String JDBC_URL_MYSQL = "jdbc:mysql://%s/%s?useSSL=false&allowPublicKeyRetrieval=true";
  public static final String JDBC_URL_CLOUDSQL = "jdbc:mysql://google/%s?cloudSqlInstance=%s&socketFactory=com.google.cloud.sql.mysql.SocketFactory&useSSL=false";
  private static final int MAX_REQUEST_BYTES = 480000; // max request size in bytes
  private static final int MAX_REQUEST_CELLS = 50000; // max cell count per request

  /**
   * Command line application to inspect data using the Data Loss Prevention Hybrid
   */
  public static void main(String[] args) throws Exception {
    System.out.println("Cloud DLP HybridInspect: SQL via JDBC V0.2");
    LOG.setLevel(LOG_LEVEL);

    Options opts = new Options();
    Option sqlOption = createAndAddOptWithArg(opts, "sql", true);
    Option databaseInstanceServer = createAndAddOptWithArg(opts, "databaseInstanceServer", true);
    Option databaseInstanceServerDisplay = createAndAddOptWithArg(opts,
        "databaseInstanceDescription", true);
    Option databaseName = createAndAddOptWithArg(opts, "databaseName", true);
    Option tableName = createAndAddOptWithArg(opts, "tableName", false);
    Option databaseUser = createAndAddOptWithArg(opts, "databaseUser", true);
    Option secretManagerResourceName = createAndAddOptWithArg(opts, "secretManagerResourceName",
        false);
    Option secretVersion = createAndAddOptWithArg(opts, "secretVersion", false);
    Option sampleRowLimit = createAndAddOptWithArg(opts, "sampleRowLimit", true);
    Option hybridJobName = createAndAddOptWithArg(opts, "hybridJobName", true);
    Option threadPoolSize = createAndAddOptWithArg(opts, "threadPoolSize", false);

    CommandLineParser parser = new DefaultParser();
    HelpFormatter formatter = new HelpFormatter();
    CommandLine cmd;
    try {
      cmd = parser.parse(opts, args);
    } catch (ParseException e) {
      LOG.log(Level.SEVERE, "Error parsing command options", e);
      formatter.printHelp(HybridInspectSql.class.getName(), opts);
      System.exit(1);
      return;
    }

    String databasePassword = null;
    if (cmd.hasOption(secretManagerResourceName.getOpt())) {
      LOG.info(String.format(">> Retrieving password from Secret Manager (%s)",
          cmd.getOptionValue(secretManagerResourceName.getOpt())));
      databasePassword = accessSecretVersion(ServiceOptions.getDefaultProjectId(),
          cmd.getOptionValue(secretManagerResourceName.getOpt()),
          cmd.getOptionValue(secretVersion.getOpt(), "latest"));
    }
    String databaseType = cmd.getOptionValue(sqlOption.getOpt());

    inspectSQLDb(
        cmd.getOptionValue(databaseInstanceServer.getOpt()),
        cmd.getOptionValue(databaseInstanceServerDisplay.getOpt()),
        cmd.getOptionValue(databaseName.getOpt()),
        cmd.getOptionValue(tableName.getOpt()),
        cmd.getOptionValue(databaseUser.getOpt()),
        databasePassword,
        databaseType,
        Integer.parseInt(cmd.getOptionValue(sampleRowLimit.getOpt())),
        cmd.getOptionValue(hybridJobName.getOpt()),
        Integer.parseInt(cmd.getOptionValue(threadPoolSize.getOpt(), "4")));
  }

  /**
   * This method uses JDBC to read data from a SQL database, then chunks it and sends it to a Cloud
   * DLP Hybrid Job
   */
  private static void inspectSQLDb(
      String databaseInstanceServer,
      String databaseInstanceDescription,
      String databaseName,
      String tableName,
      String databaseUser,
      String databasePassword,
      String databaseType,
      int sampleRowLimit,
      String hybridJobName,
      int threadPoolSize) {
    // generate a UUID as a tracking number for the scan job. This is sent as a label in the Hybrid
    // Inspect Request and used for tracking.
    String runId = UUID.randomUUID().toString();

    System.out.println("-----------------------------------------");
    System.out.println(" Start Run ID: " + runId);
    System.out.println("-----------------------------------------");

    String dataProjectId = ServiceOptions.getDefaultProjectId();
    String url = getJdbcUrl(databaseType, databaseInstanceServer, databaseName, databaseUser,
        databasePassword);
    int countTablesScanned = 0;

    try (Connection conn = DriverManager.getConnection(url, databaseUser, databasePassword)) {
      DatabaseMetaData dbMetadata = conn.getMetaData();
      String dbVersion = String.format("%s[%s]", dbMetadata.getDatabaseProductName(),
          dbMetadata.getDatabaseProductVersion());

      // this will list out all tables in the curent schama
      ResultSet ListTablesResults = dbMetadata
          .getTables(conn.getCatalog(), null, "%", new String[]{"TABLE"});

      // this will iterate through every table, and initiate a hybrid inspect scan for it on a new thread
      final ExecutorService executor = Executors.newFixedThreadPool(threadPoolSize);
      final Map<String, Future<?>> futures = new HashMap<>();
      while (ListTablesResults.next()) {
        // If we are filtering on table name, skip tables that don't match the filter
        final String table = ListTablesResults.getString(3);
        ;
        if (!Strings.isNullOrEmpty(tableName) && !tableName.equalsIgnoreCase(table)) {
          continue;
        }

        // Set Hybrid "finding details" that will be sent with this request.
        final HybridFindingDetails hybridFindingDetails =
            HybridFindingDetails.newBuilder()
                .setContainerDetails(
                    Container.newBuilder()
                        .setFullPath(String.format("%s:%s", databaseName, table))
                        .setRootPath(databaseName)
                        .setRelativePath(table)
                        .setProjectId(dataProjectId)
                        .setType(databaseType.toUpperCase())
                        .setVersion(dbVersion)
                        .build())
                .putLabels("instance", databaseInstanceDescription.toLowerCase())
                .putLabels("run-id", runId)
                .build();

        Future<?> future =
            executor.submit(
                () -> scanTable(sampleRowLimit, hybridJobName, databaseName, table, url,
                    databaseUser, databasePassword, hybridFindingDetails));
        futures.put(table, future);
      }

      for (String table : futures.keySet()) {
        try {
          // 5 minute timeout. Note that this a timeout on creating & sending the job request,
          // not waiting for it to finish.
          futures.get(table).get(5, TimeUnit.MINUTES);
          countTablesScanned++;
          System.out.println(String.format(" Scanned table %s", table));
        } catch (TimeoutException e) {
          LOG.log(Level.WARNING, String.format("Timed out scanning table %s", table), e);
        } catch (Exception e) {
          LOG.log(Level.WARNING, String.format("Exception scanning table %s", table), e);
        }
      }
    } catch (Exception e) {
      LOG.log(Level.SEVERE, "Fatal error trying to inspect tables", e);
    }
    System.out.println();
    System.out.println("-----------------------------------------");
    System.out.println(" " + countTablesScanned + " tables scanned successfully");
    System.out.println(" End Run ID: " + runId);
    System.out.println("-----------------------------------------");
  }

  /**
   * Scans a specific db table and creates a hybrid inspect job for it
   */
  private static void scanTable(int sampleRowLimit, String hybridJobName, String databaseName,
      String table, String url, String databaseUser, String databasePassword,
      HybridFindingDetails hybridFindingDetails) {
    try (Connection conn = DriverManager.getConnection(url, databaseUser, databasePassword);
        DlpServiceClient dlpClient = DlpServiceClient.create()) {
      LOG.log(Level.INFO, String.format("Table %s: reading data", table));

      // Doing a simple select * with a limit with no strict order
      PreparedStatement sqlQuery = conn.prepareStatement("SELECT * FROM ? LIMIT ?");
      sqlQuery.setString(1, table);
      sqlQuery.setInt(2, sampleRowLimit);

      ResultSet rs = sqlQuery.executeQuery();
      ResultSetMetaData rsmd = rs.getMetaData();
      int columnsNumber = rsmd.getColumnCount();
      String sHeader = "";

      // This next block converts data from ResultSet into CSV then into DLP
      // Table. This could likely be optimized but I did this in order to be
      // flexible and support other types like raw CSV reads.
      for (int i = 1; i <= columnsNumber; i++) {
        if (i > 1) {
          sHeader = sHeader + "," + rsmd.getColumnName(i);
        } else {
          sHeader = rsmd.getColumnName(i);
        }
      }
      List<FieldId> headers = Arrays.stream(sHeader.split(","))
          .map(header -> FieldId.newBuilder().setName(header).build())
          .collect(Collectors.toList());

      // Iterate through all the rows and add them to the csv
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

      LOG.log(Level.INFO, String.format("Table %s: inspecting data", table));

      int sentCount = 0;
      int prevSentCount = 0;
      int splitTotal = 0;

      // This loop will process every row but will attempt to split each request
      // so that it does not go above the DLP max request size and cell count
      while (sentCount < rows.size()) {
        try {
          splitTotal++;
          List<Table.Row> subRows = getMaxRows(rows, sentCount, headers.size());
          prevSentCount = sentCount;
          sentCount = sentCount + subRows.size();
          inspectRowsWithHybrid(dlpClient, hybridJobName, headers, subRows, hybridFindingDetails);
          LOG.log(Level.INFO, String
              .format("Table %s: inspecting row: batch=%d,startRow=%d,rowCount=%d,cellCount=%d",
                  table, splitTotal, prevSentCount, subRows.size(),
                  subRows.size() * headers.size()));
        } catch (Exception e) {
          if (e.getMessage().contains("DEADLINE_EXCEEDED")) {
            // This could happen, but when it does the request should still
            // finish. So no need to retry or you will get duplicates.
            // There could be some risk that it fails upstream though?!
            LOG.log(Level.WARNING,
                String.format("Table %s: deadline exceeded, doing nothing", table));
          } else {
            throw e;
          }
        }
      }
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  /**
   * Get the JDBC uril for the specified database type
   */
  private static String getJdbcUrl(String databaseType, String databaseInstanceServer,
      String databaseName, String databaseUser, String databasePassword) {
    // Based on the SQL database type, construct the JDBC URL. Note the pom.xml must have a
    // matching driver for these to work.
    switch (databaseType.toLowerCase()) {
      case "postgres":
        return String.format(JDBC_URL_POSTGRESQL, databaseInstanceServer, databaseName);
      case "mysql":
        return String.format(JDBC_URL_MYSQL, databaseInstanceServer, databaseName);
      case "cloudsql":
        return String.format(JDBC_URL_CLOUDSQL, databaseName, databaseInstanceServer);
      default:
        throw new IllegalArgumentException(
            "Must specify valid databaseType of either 'postgres' or 'mysql' or 'cloudsql'");
    }
  }

  /**
   * this method returns rows that are under the max bytes and cell count for a DLP request.
   */
  private static List getMaxRows(List rows, int startRow, int headerCount) throws Exception {
    ArrayList<Table.Row> subRows = null;

    // estimate the request size
    int estimatedMaxRows_bytes = MAX_REQUEST_BYTES
        / (getBytesFromList(rows) / rows.size()); // average could be off if rows differ a lot
    int estimatedMaxRows_cells = MAX_REQUEST_CELLS
        / headerCount; // pretty close to the max since every rows has the same count

    // we want the smallest of the two
    int estimatedMaxRows = estimatedMaxRows_bytes;
    if (estimatedMaxRows_cells < estimatedMaxRows_bytes) {
      estimatedMaxRows = estimatedMaxRows_cells;
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

  /**
   * this methods calculates the total bytes of a list of rows.
   */
  public static int getBytesFromList(List list) throws IOException {
    java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
    java.io.ObjectOutputStream out = new java.io.ObjectOutputStream(baos);
    out.writeObject(list);
    out.close();
    return baos.toByteArray().length;
  }

  /**
   * Takes rows/header and a findings details object and generates a DLP Hybrid Request
   */
  private static HybridInspectResponse inspectRowsWithHybrid(DlpServiceClient dlpClient,
      String hybridJobName, List<FieldId> headers, List<Table.Row> rows,
      HybridFindingDetails hybridFindingDetails) {
    Table table = Table.newBuilder().addAllHeaders(headers).addAllRows(rows).build();
    ContentItem tableItem = ContentItem.newBuilder().setTable(table).build();

    HybridContentItem hybridContentItem =
        HybridContentItem.newBuilder()
            .setItem(tableItem)
            .setFindingDetails(hybridFindingDetails)
            .build();

    HybridInspectDlpJobRequest request =
        HybridInspectDlpJobRequest.newBuilder()
            .setName(hybridJobName)
            .setHybridItem(hybridContentItem)
            .build();

    return dlpClient.hybridInspectDlpJob(request);
  }

  /**
   * Parse a date string to valid date, return null when invalid
   */
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

  /**
   * Access the payload for the given secret version if one exists. The version can be a version
   * number as a string (e.g. "5") or an alias (e.g. "latest").
   */
  public static String accessSecretVersion(String projectId, String secretId, String versionId)
      throws IOException {
    // Initialize client that will be used to send requests. This client only needs to be created
    // once, and can be reused for multiple requests. After completing all of your requests, call
    // the "close" method on the client to safely clean up any remaining background resources.
    try (SecretManagerServiceClient client = SecretManagerServiceClient.create()) {
      SecretVersionName name = SecretVersionName.of(projectId, secretId, versionId);

      // Access the secret version.
      AccessSecretVersionRequest request =
          AccessSecretVersionRequest.newBuilder().setName(name.toString()).build();
      AccessSecretVersionResponse response = client.accessSecretVersion(request);

      String payload = response.getPayload().getData().toStringUtf8();
      return payload;
    }
  }

  /**
   * Helper to create an Option and add it to the specified Options object
   */
  private static Option createAndAddOptWithArg(Options options, String name, boolean required) {
    Option opt = Option.builder(name).required(required).hasArg(true).build();
    options.addOption(opt);
    return opt;
  }
}
// [END HybridInspectSql]