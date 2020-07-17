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
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.OptionGroup;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

public class HybridInspectSql {
  // [START HybridInspectSql]

  public static boolean VERBOSE_OUTPUT = false; // flag that will increase output details
  public static int MAX_REQUEST_BYTES = 480000; // max request size in bytes
  public static int MAX_REQUEST_CELLS = 50000; // max cell count per request

  private static DlpServiceClient dlpServiceClient;

  static {
    try {
      dlpServiceClient = DlpServiceClient.create();
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  // This method uses JDBC to read data from a SQL database, then chunks it and sends it to a Cloud
  // DLP Hybrid Job
  private static void inspectSQLDb(
      String databaseInstanceServer,
      String databaseInstanceDescription,
      String databaseName,
      String tableName,
      String databaseUser,
      String databasePassword,
      String databaseType,
      String sampleRowLimit,
      String hybridJobName,
      int threadPoolSize) {
    // generate a UUID as a tracking number for the scan job. This is sent as a label in the Hybrid
    // Inspect Request and used for tracking.
    String runID = UUID.randomUUID().toString();

    try {
      String dataProjectId = ServiceOptions.getDefaultProjectId();

      Connection conn;
      String url;

      // Based on the SQL database type, construct the JDBC URL.  Note the pom.xml must have a
      // matching driver for these to work.
      if (databaseType.equalsIgnoreCase("postgres")) {
        url = String.format("jdbc:postgresql://%s/%s", databaseInstanceServer, databaseName);
        conn = DriverManager.getConnection(url, databaseUser, databasePassword);
      } else if (databaseType.equalsIgnoreCase("mysql")) {
        url =
            String.format(
                "jdbc:mysql://%s/%s?useSSL=false&allowPublicKeyRetrieval=true",
                databaseInstanceServer, databaseName);
        conn = DriverManager.getConnection(url, databaseUser, databasePassword);
      } else if (databaseType.equalsIgnoreCase(
          "cloudsql")) { // Note, in theory you can just use mysql or postgres to access Cloud SQL.
        url =
            String.format(
                "jdbc:mysql://google/%s?cloudSqlInstance=%s&socketFactory=com.google.cloud.sql.mysql.SocketFactory&useSSL=false",
                databaseName, databaseInstanceServer);
        conn = DriverManager.getConnection(url, databaseUser, databasePassword);
      } else {
        throw new Exception(
            "Must specify valid database type of either 'postgres' or 'mysql' or 'cloudsql'");
      }
      int countTablesScanned = 0;

      try {
        DatabaseMetaData db_md = conn.getMetaData();
        String dbVersion =
            db_md.getDatabaseProductName() + "[" + db_md.getDatabaseProductVersion() + "]";

        // this will list out all tables in the curent schama
        ResultSet ListTables_rs =
            db_md.getTables(conn.getCatalog(), null, "%", new String[]{"TABLE"});

        final ExecutorService executor = Executors.newFixedThreadPool(threadPoolSize);
        final List<Future<?>> futures = new ArrayList<>();
        System.out.println("-----------------------------------------");
        System.out.println(" Start Run ID: " + runID);
        System.out.println("-----------------------------------------");

        // this will iterate through every table
        while (ListTables_rs.next()) {
          String tempTable = "";
          String tempDBName = "";

          tempTable = ListTables_rs.getString(3);
          tempDBName = databaseName;

          final String theDBName = tempDBName;
          final String theTable = tempTable;
          final String url_Inside = url;
          final String dbUsername_Inside = databaseUser;
          final String dbPassword_Inside = databasePassword;

          // Set Hybrid "finding details" that will be sent with this request.
          final HybridFindingDetails hybridFindingDetails =
              HybridFindingDetails.newBuilder()
                  .setContainerDetails(
                      Container.newBuilder()
                          .setFullPath(theDBName + ":" + theTable)
                          .setRootPath(theDBName)
                          .setRelativePath(theTable)
                          .setProjectId(dataProjectId)
                          .setType(databaseType.toUpperCase())
                          .setVersion(dbVersion)
                          .build())
                  .putLabels("instance", databaseInstanceDescription.toLowerCase())
                  .putLabels("run-id", runID)
                  .build();

          if (tableName == null
              || tableName.equalsIgnoreCase("")
              || theTable.equalsIgnoreCase(tableName)) {
            countTablesScanned++;
            // This next entire block runs as a "thread"
            Future<?> future =
                executor.submit(
                    () -> {
                      try {
                        System.out.print(
                            "|"
                                + System.lineSeparator()
                                + "> DLP infoType Profile: ["
                                + theDBName
                                + "]["
                                + theTable
                                + "]");
                        if (VERBOSE_OUTPUT) {
                          System.out.print("..(Reading Data).");
                        } else {
                          System.out.print("..R.");
                        }

                        // Doing a simple select * with a limit with no strict order
                        String sqlQuery = "SELECT * from " + theTable + " limit " + sampleRowLimit;

                        Connection connInside =
                            DriverManager.getConnection(
                                url_Inside, dbUsername_Inside, dbPassword_Inside);

                        Statement stmt = connInside.createStatement();
                        ResultSet rs = stmt.executeQuery(sqlQuery);
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

                        if (VERBOSE_OUTPUT) {
                          System.out.print("..(Inspecting Data).");
                        } else {
                          System.out.print("..I.");
                        }
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
                            inspectRowsWithHybrid(
                                hybridJobName, headers, subRows, hybridFindingDetails);
                            if (VERBOSE_OUTPUT) {
                              System.out.println("|");
                              System.out.println(
                                  "[ Request Size ("
                                      + theDBName
                                      + ":"
                                      + theTable
                                      + "): request#"
                                      + splitTotal
                                      + " | start-row="
                                      + prevSentCount
                                      + " | row-count="
                                      + subRows.size()
                                      + " | cell-count="
                                      + subRows.size() * headers.size()
                                      + "]");
                            } else {
                              if (splitTotal % 2 != 0) {
                                System.out.print("/");
                              } else {
                                System.out.print("\\");
                              }
                            }
                          } catch (Exception eTry) {
                            if (eTry.getMessage().contains("exceeds limit")
                                || eTry.getMessage()
                                .contains("only 50,000 table values are allowed")) {
                              // This message should not happen since we are measuring size before
                              // sending. So if it happens, it is a hard fail as something is wrong.
                              System.out.println("|");
                              System.out.print("*** Fatal Error [START] ***");
                              System.out.print(
                                  ">> DLP request size too big. Split failed ["
                                      + theDBName
                                      + "]["
                                      + theTable
                                      + "]");
                              eTry.printStackTrace();
                              System.out.print("*** Fatal Error [END] ***");
                              throw eTry;
                            } else if (eTry.getMessage().contains("DEADLINE_EXCEEDED")) {
                              // This could happen, but when it does the request should still
                              // finish. So no need to retry or you will get duplicates.
                              // There could be some risk that it fails upstream though?!
                              if (VERBOSE_OUTPUT) {
                                System.out.println("|");
                                System.out.println("[deadline exceed / action: do-nothing]");
                                eTry.printStackTrace();
                              } else {
                                System.out.print(".[DE].");
                              }
                            } else {
                              System.out.println("|");
                              System.out.println(
                                  "*** Unknown Fatal Error when trying to inspect data for ["
                                      + theDBName
                                      + "]["
                                      + theTable
                                      + "] ***");
                              throw eTry;
                            }
                          }
                        }
                        connInside.close();

                      } catch (Exception ec) {
                        ec.printStackTrace();
                      }
                    });
            futures.add(future);
          }
        }
        try {
          for (Future<?> future : futures) {
            try {
              // 5 minute timeout. Again even if this hits, it should still finish since the request
              // has already been sent.
              future.get(300, TimeUnit.SECONDS);
            } catch (InterruptedException | ExecutionException e) {
              System.out.println("Runnabled aborted : " + e.getStackTrace());
            }
          }
          executor.shutdown();

        } catch (Exception e) {
          System.out.println("*** Failure at Futures tracking ***");
          e.printStackTrace();
        } finally {
          // shut down the executor manually
          executor.shutdown();
        }
      } catch (Exception e) {
        System.out.println("|");
        System.out.println("*** Unknown Fatal Error when trying to inspect tables ***");
        e.printStackTrace();
      }
      conn.close();
      System.out.println();
      System.out.println("-----------------------------------------");
      System.out.println(" " + countTablesScanned + " tables scanned");
      System.out.println(" End Run ID: " + runID);
      System.out.println("-----------------------------------------");

    } catch (Exception e) {
      System.out.println("|");
      System.out.println("*** Unknown Fatal Error in HybridInspectSQLDb ***");
      e.printStackTrace();
    }
  }

  // this method returns rows that are under the max bytes and cell count for a DLP request.
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

  // this methods calculates the total bytes of a list of rows.
  public static int getBytesFromList(List list) throws IOException {
    java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
    java.io.ObjectOutputStream out = new java.io.ObjectOutputStream(baos);
    out.writeObject(list);
    out.close();
    return baos.toByteArray().length;
  }

  // Takes rows/header and a findings details object and generates a DLP Hybrid Request
  private static HybridInspectResponse inspectRowsWithHybrid(
      String hybridJobName,
      List<FieldId> headers,
      List<Table.Row> rows,
      HybridFindingDetails hybridFindingDetails) {
    try {
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

      return dlpServiceClient.hybridInspectDlpJob(request);
    } catch (Exception e) {
      // System.out.println("Error in inspectSQLDb: " + e.getMessage());
      throw e;
    }
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

  // Access the payload for the given secret version if one exists. The version can be a version
  // number as a string (e.g. "5") or an alias (e.g. "latest").
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
   * Command line application to inspect data using the Data Loss Prevention Hybrid
   */
  public static void main(String[] args) throws Exception {
    java.util.Date dStart = new java.util.Date();
    System.out.println("[Start: " + dStart.toString() + "]");

    OptionGroup optionsGroup = new OptionGroup();
    optionsGroup.setRequired(true);

    Option sqlOption = new Option("sql", "sql", true, "inspect sql");
    optionsGroup.addOption(sqlOption);

    Options commandLineOptions = new Options();
    commandLineOptions.addOptionGroup(optionsGroup);

    Option databaseInstanceServerOption = Option.builder("databaseInstanceServer").hasArg(true)
        .required(false).build();
    commandLineOptions.addOption(databaseInstanceServerOption);

    Option databaseInstanceServerDisplayOption =
        Option.builder("databaseInstanceDescription").hasArg(true).required(false).build();
    commandLineOptions.addOption(databaseInstanceServerDisplayOption);

    Option databaseNameOption = Option.builder("databaseName").hasArg(true).required(false).build();
    commandLineOptions.addOption(databaseNameOption);

    Option tableNameOption = Option.builder("tableName").hasArg(true).required(false).build();
    commandLineOptions.addOption(tableNameOption);

    Option databaseUserOption = Option.builder("databaseUser").hasArg(true).required(false).build();
    commandLineOptions.addOption(databaseUserOption);

    Option secretManagerResourceNameOption = Option.builder("secretManagerResourceName")
        .hasArg(true).required(false).build();
    commandLineOptions.addOption(secretManagerResourceNameOption);

    Option sampleRowLimitOption = Option.builder("sampleRowLimit").hasArg(true).required(false)
        .build();
    commandLineOptions.addOption(sampleRowLimitOption);

    Option hybridJobNameOption =
        Option.builder("hybridJobName").hasArg(true).required(false).build();
    commandLineOptions.addOption(hybridJobNameOption);

    Option sThreadPoolSizeOption =
        Option.builder("threadPoolSize").hasArg(true).required(false).build();
    commandLineOptions.addOption(sThreadPoolSizeOption);

    CommandLineParser parser = new DefaultParser();
    HelpFormatter formatter = new HelpFormatter();
    CommandLine cmd;

    try {
      cmd = parser.parse(commandLineOptions, args);
    } catch (ParseException e) {
      System.out.println(e.getMessage());
      formatter.printHelp(HybridInspectSql.class.getName(), commandLineOptions);
      System.exit(1);
      return;
    }

    if (cmd.hasOption("sql")) {
      System.out.println("Cloud DLP HybridInspect: SQL via JDBC V0.2");
      String databaseInstanceServer = cmd.getOptionValue(databaseInstanceServerOption.getOpt());
      String databaseInstanceDescription = cmd
          .getOptionValue(databaseInstanceServerDisplayOption.getOpt());
      String databaseName = cmd.getOptionValue(databaseNameOption.getOpt());
      String tableName = cmd.getOptionValue(tableNameOption.getOpt());
      String databaseUser = cmd.getOptionValue(databaseUserOption.getOpt());
      String secretManagerResourceName = cmd
          .getOptionValue(secretManagerResourceNameOption.getOpt());
      String databasePassword = null;
      if (secretManagerResourceName != null && !secretManagerResourceName.equalsIgnoreCase("")) {
        System.out.println(
            ">> Retrieving password from Secret Manager ("
                + cmd.getOptionValue(secretManagerResourceNameOption.getOpt())
                + ")");
        databasePassword =
            accessSecretVersion(ServiceOptions.getDefaultProjectId(),
                cmd.getOptionValue(secretManagerResourceNameOption.getOpt()), "1");
      }
      String databaseType = cmd.getOptionValue(sqlOption.getOpt());
      String sampleRowLimit = cmd.getOptionValue(sampleRowLimitOption.getOpt());
      String hybridJobName = cmd.getOptionValue(hybridJobNameOption.getOpt());
      int threadPoolSize = new Integer(cmd.getOptionValue(sThreadPoolSizeOption.getOpt()))
          .intValue();
      inspectSQLDb(
          databaseInstanceServer,
          databaseInstanceDescription,
          databaseName,
          tableName,
          databaseUser,
          databasePassword,
          databaseType,
          sampleRowLimit,
          hybridJobName,
          threadPoolSize);
    }

    java.util.Date dEnd = new java.util.Date();
    System.out.println("[End: " + dEnd.toString() + "]");

    long diff = dEnd.getTime() - dStart.getTime();

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
// [END HybridInspectSql]