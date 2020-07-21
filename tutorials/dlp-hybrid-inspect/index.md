# Cloud Data Loss Prevention (DLP) Hybrid Inspect Sample for SQL Databases using JDBC

## Configuration and Build
Depend in on the database you are conecting to, you may need to update the ```pom.xml``` file to include the proper JDBC client.

__Compile everything__
```
mvn clean package -DskipTests
```

## Command line parameters

| parameter                   | desc                                                                                                                                                                                                                  | 
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| sql                         | database type "mysql" "postgres" "cloudsql" (there must be a JDBC driver for these configured in ```your pom.xml```)                                                                                                  |
| threadPoolSize              | number of worker threads. _Note: This code uses 1 thread per table regardless of this setting. If you are scanning multiple tables, increasing this number means more than one table can be processed in parallel.    |
| sampleRowLimit              | max number of rows to scan per table                                                                                                                                                                                  |
| hybridJobName               | Cloud DLP Hybrid job resource ID/name                                                                                                                                                                                 |
| databaseInstanceDescription | Give this run an instance name for tracking - this gets written to Hybrid and must follow label contraints.                                                                                                           |
| databaseInstanceServer      | The hostname where your database is running (e.g. localhsot or 127.0.0.1 for local).                                                                                                                                  |
| databaseName                | The name of the database or dataset name that you want to scan.                                                                                                                                                       |
| tableName                   | (Optional) The name of the table you want to scan. If blank, then all tables will be scanned.                                                                                                                         |
| databaseUser                | The username for your database instance.                                                                                                                                                                              |
| secretManagerResourceName   | The Secret Manager resrouce ID/name that has your database password. Currently this is just the _name_ and the secret must be in the same project.                                                                    |

## Example command lines

### MySQL

```
java -cp target/dlp-hybrid-inspect-sql-0.5-jar-with-dependencies.jar com.example.dlp.HybridInspectSql \
-sql "mysql" \
-threadPoolSize 1 \
-sampleRowLimit 1000 \
-hybridJobName "projects/[PROJECT-ID]/dlpJobs/[HYBRID-JOB-NAME]" \
-databaseInstanceDescription "Hybrid Inspect Test" \
-databaseInstanceServer "127.0.0.1" \
-databaseName "[DATABSE-NAME]" \
-databaseUser "[DATABASE-USER]" \
-secretManagerResourceName "[SECRET-MANAGER]"
```
