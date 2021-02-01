/*
 * Copyright 2021 Google Inc.
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
import com.google.privacy.dlp.v2.HybridInspectJobTriggerRequest;
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
import java.time.Instant;
import java.time.Duration;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.io.Reader;
import java.nio.file.Paths;
import java.nio.file.Files;

public class HybridInspectSql {

  private static final Logger LOG = Logger.getLogger(HybridInspectSql.class.getName());
  private static final Level LOG_LEVEL = Level.WARNING;
  private static final String DISPLAY_VERSION = "0.2";

  // Below are standard JDBC URLs for a select set of data sources. To add more sources, you will need to add the URLs here and update
  // code methods below to use these. 
  public static final String JDBC_URL_POSTGRESQL = "jdbc:postgresql://%s/%s";
  public static final String JDBC_URL_MYSQL = "jdbc:mysql://%s/%s?useSSL=false&allowPublicKeyRetrieval=true";
  public static final String JDBC_URL_SQLSERVER = "jdbc:sqlserver://%s;database=%s;integratedSecurity=false;";

  // The values below can be configured to shrink the size of an individual request. Please consider usage limits and quota when adjusting these
  // https://cloud.google.com/dlp/limits
  private static final int MAX_REQUEST_BYTES = 480000; // max request size in bytes
  private static final int MAX_REQUEST_CELLS = 50000; // max cell count per request

  /**
   * Class object for a Database instance
   */
  public static class Database {

    private int threadPoolSize = 1;
    private int sampleRowLimit = 1000;
    private String databaseType;
    private String databaseInstanceDescription;
    private String databaseInstanceServer;
    private String databaseName;
    private String tableName;
    private String databaseUser;
    private String secretManagerResourceName;

    public int getThreadPoolSize() { return threadPoolSize; }
    public int getSampleRowLimit() { return sampleRowLimit; }
    public String getDatabaseType() { return databaseType; }
    public String getDatabaseInstanceDescription() { return databaseInstanceDescription; }
    public String getDatabaseInstanceServer() { return databaseInstanceServer; }
    public String getDatabaseName() { return databaseName; }
    public String getTableName() { return tableName; }
    public String getDatabaseUser() { return databaseUser; }
    public String getSecretManagerResourceName() { return secretManagerResourceName; }

    public Database(int threadPoolSizeIn,
                    int sampleRowLimitIn,
                    String databaseTypeIn,
                    String databaseInstanceDescriptionIn,
                    String databaseInstanceServerIn,
                    String databaseNameIn,
                    String tableNameIn,
                    String databaseUserIn,
                    String secretManagerResourceNameIn) {

      threadPoolSize = threadPoolSizeIn;
      sampleRowLimit = sampleRowLimitIn;
      databaseType = databaseTypeIn;
      databaseInstanceDescription = databaseInstanceDescriptionIn;
      databaseInstanceServer = databaseInstanceServerIn;
      databaseName = databaseNameIn;
      tableName = tableNameIn;
      databaseUser = databaseUserIn;
      secretManagerResourceName = secretManagerResourceNameIn;
   }

    public String toString(){
          return databaseInstanceDescription + " [" + databaseType + "] Host:" + databaseInstanceServer;
    }

    public Database() {
    }

  }


  /**
   * Command line application to inspect data using the Data Loss Prevention Hybrid
   */
  public static void main(String[] args) throws Exception {
    System.out.println("Cloud DLP HybridInspect: SQL via JDBC Script Version " + DISPLAY_VERSION);
    // generate a UUID as a tracking number for the scan job. This is sent as a label in the Hybrid
    // Inspect Request and used for tracking.
    String runId = UUID.randomUUID().toString();

    Instant startTime = Instant.now();

    System.out.println("-----------------------------------------------------------------");
    System.out.println(" Start Run ID: " + runId);
    System.out.println(" Start Time: " + startTime.toString());
    System.out.println("-----------------------------------------------------------------");

    LOG.setLevel(LOG_LEVEL);

    Options opts = new Options();

    // General options
    Option hybridJobNameOption = createAndAddOptWithArg(opts, "hybridJobName", true);
    Option threadPoolSizeOption = createAndAddOptWithArg(opts, "threadPoolSize", true);

    // Options for sending in a JSON list of databases
    Option databasesOption = createAndAddOptWithArg(opts, "databases", false);

    // Options for sending a single database in via command line
    Option sqlOption = createAndAddOptWithArg(opts, "sql", false);
    Option databaseInstanceServerOption = createAndAddOptWithArg(opts, "databaseInstanceServer", false);
    Option databaseInstanceServerDisplayOption = createAndAddOptWithArg(opts,
        "databaseInstanceDescription", false);
    Option databaseNameOption = createAndAddOptWithArg(opts, "databaseName", false);
    Option tableNameOption = createAndAddOptWithArg(opts, "tableName", false);
    Option databaseUserOption = createAndAddOptWithArg(opts, "databaseUser", false);
    Option secretManagerResourceNameOption = createAndAddOptWithArg(opts, "secretManagerResourceName",
        false);
    Option secretVersionOption = createAndAddOptWithArg(opts, "secretVersion", false);
    Option sampleRowLimitOption = createAndAddOptWithArg(opts, "sampleRowLimit", false);

    CommandLineParser parser = new DefaultParser();
    HelpFormatter formatter = new HelpFormatter();
    CommandLine cmd;
    try {
      cmd = parser.parse(opts, args);
    } catch (ParseException e) {
      LOG.log(Level.SEVERE, "Error parsing command options", e);
      formatter.printHelp(HybridInspectSql.class.getName(), opts);
      System.out.println("You must pass either parameters for a data source to scan or an " +
                         "input file to a JSON list of data sources to scan. Please see" +
                         " the readme for more details");
      System.exit(1);
      return;
    }

    int totalDatabaseCount = 0;
    int totalTableCount = 0;

    if (cmd.hasOption(sqlOption.getOpt())) {
      //Read information from command line parameters to scan a single source
      Database tempDB = new HybridInspectSql.Database(Integer.parseInt(cmd.getOptionValue(threadPoolSizeOption.getOpt(), "1")),
                                                      Integer.parseInt(cmd.getOptionValue(sampleRowLimitOption.getOpt())),
                                                      cmd.getOptionValue(sqlOption.getOpt()),
                                                      cmd.getOptionValue(databaseInstanceServerDisplayOption.getOpt()),
                                                      cmd.getOptionValue(databaseInstanceServerOption.getOpt()),
                                                      cmd.getOptionValue(databaseNameOption.getOpt()),
                                                      cmd.getOptionValue(tableNameOption.getOpt()),
                                                      cmd.getOptionValue(databaseUserOption.getOpt()),
                                                      cmd.getOptionValue(secretManagerResourceNameOption.getOpt()) );
      totalTableCount = inspectSQLDb(tempDB, cmd.getOptionValue(hybridJobNameOption.getOpt(),null), runId);
      totalDatabaseCount++;
    }
    else if (cmd.hasOption(databasesOption.getOpt())) {
      //Read a list of data sources from JSON input
      LOG.info(String.format("> Retrieving list from (%s)",
          cmd.getOptionValue(databasesOption.getOpt())));
      List<Database> databases = loadDatabaseListFromJSON(cmd.getOptionValue(databasesOption.getOpt()));

      // set up threading for the first level of threads (e.g. how many data sources do we scan in parallel)
      final ExecutorService executorDB = Executors.newFixedThreadPool(new Integer(cmd.getOptionValue(threadPoolSizeOption.getOpt())).intValue());
      final Map<String, Future<Integer>> futuresDB = new HashMap<>();

      //Loop through all databases and inspect
      for (Database tempDB : databases) {
        LOG.info(String.format("Scanning data sources: ",tempDB.toString()));
        Future<Integer> futureDB =
            executorDB.submit(
                () -> inspectSQLDb(tempDB, cmd.getOptionValue(hybridJobNameOption.getOpt(),null), runId));
        futuresDB.put(tempDB.databaseName, futureDB);
      }
      executorDB.shutdown();

      for (String databaseName : futuresDB.keySet()) {
        try {
          // 10 minute timeout. Note that this a timeout on creating & sending the hybrid request(s),
          // not waiting for it to finish.  Larger data sources may need more time.
          totalTableCount += futuresDB.get(databaseName).get(10, TimeUnit.MINUTES).intValue();
          totalDatabaseCount++;
        } catch (TimeoutException e) {
          LOG.log(Level.WARNING, String.format("Timed out creating a scan for table %s", databaseName), e);
        } catch (Exception e) {
          LOG.log(Level.WARNING, String.format("Exception creating a scan for table %s", databaseName), e);
        }
      }

    }

    Instant endTime = Instant.now();
    Duration elapsed = Duration.between(startTime, endTime);
    long diffSeconds = elapsed.getSeconds() % 60;
    long diffMinutes = elapsed.getSeconds() / 60 % 60;
    long diffHours = elapsed.getSeconds() / (60 * 60 ) % 24;
    long diffDays = elapsed.getSeconds() / (24 * 60 * 60 );

    System.out.println();
    System.out.println("-----------------------------------------------------------------");
    System.out.println(" End Run ID: " + runId);
    System.out.println(" Total Databases scanned: " + totalDatabaseCount);
    System.out.println(" Total Tables scanned: " + totalTableCount);
    System.out.println(" End Time: " + endTime.toString());
    System.out.print  (" Duration: ");
    System.out.print  ("  " + diffDays + " days, ");
    System.out.print  ("  " + diffHours + " hours, ");
    System.out.print  ("  " + diffMinutes + " minutes, ");
    System.out.println("  " + diffSeconds + " seconds.");
    System.out.println("-----------------------------------------------------------------");

  }


  /**
   * This method will load a list of Database objects from an external JSON file
   */
  private static List<Database> loadDatabaseListFromJSON(String fileName) throws java.io.IOException {
    // create Gson instance
    Gson gson = new Gson();
    // create a reader
    Reader reader = Files.newBufferedReader(Paths.get(fileName));
    // convert JSON file to map
    List <Database> databases = new Gson().fromJson(reader, new TypeToken<List<Database>>() {}.getType());
    // close reader
    reader.close();

    return databases;
  }


  /**
   * This method uses JDBC to read data from a SQL database, then chunks it and sends it to a Cloud
   * DLP Hybrid Job
   */
  private static Integer inspectSQLDb(
      Database database,
      String hybridJobName,
      String runId) throws Exception {

    System.out.println();
    System.out.print(String.format(">> [%s,%s:%s]: Starting Inspection", database.databaseInstanceDescription, database.databaseInstanceServer, database.databaseName));

    //retreive the password from Secret Manager
    final String databasePassword = accessSecretVersion(ServiceOptions.getDefaultProjectId(),
          database.getSecretManagerResourceName(),"latest");

    String dataProjectId = ServiceOptions.getDefaultProjectId();
    String url = getJdbcUrl(database.getDatabaseType(),
                            database.getDatabaseInstanceServer(),
                            database.getDatabaseName(),
                            database.getDatabaseUser(),
                            databasePassword);
    int countTablesScanned = 0;

    try  {
      DriverManager.registerDriver(getJdbcDriver(database.getDatabaseType()));
      Connection conn = DriverManager.getConnection(url, database.getDatabaseUser(), databasePassword);
      DatabaseMetaData dbMetadata = conn.getMetaData();
      String dbVersion = String.format("%s[%s]", dbMetadata.getDatabaseProductName(),
          dbMetadata.getDatabaseProductVersion());

      // this will list out all tables in the curent schama
      ResultSet ListTablesResults = dbMetadata
          .getTables(conn.getCatalog(), null, "%", new String[]{"TABLE"});

      // this will iterate through every table, and initiate a hybrid inspect scan for it on a new thread
      final ExecutorService executor = Executors.newFixedThreadPool(database.getThreadPoolSize());
      final Map<String, Future<?>> futures = new HashMap<>();
      while (ListTablesResults.next()) {
        // If we are filtering on table name, skip tables that don't match the filter

        // pull the table name
        String tempTable = ListTablesResults.getString(3);

        //for some databases you need the full schema + table name
        if (database.databaseType.equalsIgnoreCase("sqlserver")){
          tempTable = String.format("%s.%s",ListTablesResults.getString(2),ListTablesResults.getString(3));
        }

        final String table = tempTable;;
        if (database.getTableName() != null && !database.getTableName().equalsIgnoreCase(table)) {
          continue;
        }

        // Set Hybrid "finding details" that will be sent with this request.
        final HybridFindingDetails hybridFindingDetails =
            HybridFindingDetails.newBuilder()
                .setContainerDetails(
                    Container.newBuilder()
                        .setFullPath(String.format("%s:%s:%s", database.getDatabaseInstanceServer(), database.getDatabaseName(), table))
                        .setRootPath(String.format("%s:%s",database.getDatabaseInstanceServer(),database.getDatabaseName()))
                        .setRelativePath(table)
                        .setProjectId(database.getDatabaseInstanceServer())
                        .setType(database.getDatabaseType().toUpperCase())
                        .setVersion(dbVersion)
                        .build())
                .putLabels("instance", database.getDatabaseInstanceDescription().toLowerCase())
                .putLabels("run-id", runId)
                .build();

        Future<?> future =
            executor.submit(
                () -> scanTable(database.getSampleRowLimit(), hybridJobName, table, url, database.getDatabaseUser(),
                    databasePassword, hybridFindingDetails, database.getDatabaseType(), database.getDatabaseName()));
        futures.put(table, future);
      }
      executor.shutdown();

      for (String table : futures.keySet()) {
        try {
          // 5 minute timeout. Note that this a timeout on creating & sending the job request,
          // not waiting for it to finish.
          futures.get(table).get(5, TimeUnit.MINUTES);
          countTablesScanned++;
          System.out.println();
          System.out.print(String.format(">>>> Scanned table %s", table));
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
    System.out.print(String.format(">> [%s,%s:%s]: %s tables scanned successfully", database.databaseInstanceDescription, database.databaseInstanceServer, database.databaseName, countTablesScanned));
    return new Integer(countTablesScanned);

  }


  /**
   * Scans a specific db table and creates a hybrid inspect job for it
   */
  private static void scanTable(int sampleRowLimit, String hybridJobName, String table, String url,
      String databaseUser, String databasePassword, HybridFindingDetails hybridFindingDetails, String databaseType, String databaseName) {

    try (Connection conn = DriverManager.getConnection(url, databaseUser, databasePassword);
        DlpServiceClient dlpClient = DlpServiceClient.create()) {
      LOG.log(Level.INFO, String.format(">>>>>> Table %s: reading data", table));

      // Doing a simple select * with a limit with no strict order

      String sqlQuery = getSqlQuery(databaseType, databaseName, table, sampleRowLimit);

      ResultSet rs = conn.createStatement().executeQuery(sqlQuery);
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

      LOG.log(Level.INFO, String.format(">>>>>> Table %s: inspecting data", table));

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
              .format(">>>>>> Table %s: inspecting row: batch=%d,startRow=%d,rowCount=%d,cellCount=%d",
                  table, splitTotal, prevSentCount, subRows.size(),
                  subRows.size() * headers.size()));
        } catch (Exception e) {
          if (e.getMessage().contains("DEADLINE_EXCEEDED")) {
            // This could happen, but when it does the request should still
            // finish. So no need to retry or you will get duplicates.
            // There could be some risk that it fails upstream though?!
            LOG.log(Level.WARNING,
                String.format(">>>> Table %s: deadline exceeded, doing nothing", table));
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
   * Takes rows/header and a findings details object and generates a DLP Hybrid Request
   */
  private static HybridInspectResponse inspectRowsWithHybrid(DlpServiceClient dlpClient,
      String hybridJobName, List<FieldId> headers, List<Table.Row> rows,
      HybridFindingDetails hybridFindingDetails) {
    Table table = Table.newBuilder().addAllHeaders(headers).addAllRows(rows).build();
    ContentItem tableItem = ContentItem.newBuilder().setTable(table).build();

    System.out.print(".");

    HybridContentItem hybridContentItem =
        HybridContentItem.newBuilder()
            .setItem(tableItem)
            .setFindingDetails(hybridFindingDetails)
            .build();
    //Use either HybridDlpJob or HybridJobTrigger depending on the command line parameter
    if (hybridJobName.contains("/dlpJobs/i-")) {
      HybridInspectDlpJobRequest request =
      HybridInspectDlpJobRequest.newBuilder()
        .setName(hybridJobName)
        .setHybridItem(hybridContentItem)
        .build();
      return dlpClient.hybridInspectDlpJob(request);
    } else {
      HybridInspectJobTriggerRequest request =
         HybridInspectJobTriggerRequest.newBuilder()
             .setName(hybridJobName)
             .setHybridItem(hybridContentItem)
             .build();
      return dlpClient.hybridInspectJobTrigger(request);
    }
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
  * Because this script may be connecting to mulitple JDBC drivers in the same run, this method helps ensure that the drivers are registered
  */
  private static java.sql.Driver getJdbcDriver (String databaseType){
    // Based on the SQL database type, reguster the driver. Note the pom.xml must have a
    // matching driver for these to work. This addresses driver not found issues when
    // trying to scan more than one JDBC type.
    try {
        switch (databaseType.toLowerCase()) {
          case "postgres":
            return new org.postgresql.Driver();
          case "mysql":
            return new com.mysql.cj.jdbc.Driver();
          case "sqlserver":
            return new com.microsoft.sqlserver.jdbc.SQLServerDriver();
          default:
            throw new IllegalArgumentException(
                "Must specify valid databaseType of either 'postgres' or 'mysql' or 'sqlserver'");
        }
    } catch (java.sql.SQLException je){
        LOG.log(Level.WARNING, "failed to load SQL Driver",je);
        return null;
    }
  }


  /**
  * Get the SQL query string for the specified database type
  */
  private static String getSqlQuery (String databaseType, String databaseName, String tableName, int sampleRowLimit){
  // Based on the SQL database type, the SQL query used to select data may differ, This method allows for that per JDBC source type
     switch (databaseType.toLowerCase()) {
        case "sqlserver":
          return String.format("SELECT TOP %d * FROM %s", sampleRowLimit, tableName);
        default:
          return String.format("SELECT * FROM %s LIMIT %d", tableName, sampleRowLimit);
     }
  }

  /**
   * Get the JDBC url for the specified database type
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
      case "sqlserver":
        return String.format(JDBC_URL_SQLSERVER,databaseInstanceServer, databaseName);
      default:
        throw new IllegalArgumentException(
            "Must specify valid databaseType of either 'postgres' or 'mysql' or 'sqlserver'");
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
   * Helper to create an Option and add it to the specified Options object
   */
  private static Option createAndAddOptWithArg(Options options, String name, boolean required) {
    Option opt = Option.builder(name).required(required).hasArg(true).build();
    options.addOption(opt);
    return opt;
  }
}
// [END HybridInspectSql]
