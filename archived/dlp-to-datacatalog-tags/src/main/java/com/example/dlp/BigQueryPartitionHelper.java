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

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class BigQueryPartitionHelper {

  private static final String SQL_FIND_PARTITION_COLUMN_TEMPLATE =
          "SELECT\n" +
                  " table_name, column_Name, is_partitioning_column from\n" +
                  " `%s`.INFORMATION_SCHEMA.COLUMNS\n" +
                  "WHERE\n" +
                  " table_name=\"%s\";";

  private static final String SQL_PARTITION_FILTER_TEMPLATE =
          "WHERE DATE(%s) <= CURRENT_DATE()";

  private static final String SQL_END_REGEX_STRING =
          "(limit \\d+)";

  public static final String PARTITION_COLUMN_YES = "YES";

  public static ResultSet queryWithPartition(String databaseName,
                                              String tableName,
                                              String sqlQuery,
                                              Connection connection) throws SQLException {
    Statement stmt = connection.createStatement();
    ResultSet rs = stmt.executeQuery(
            String.format(SQL_FIND_PARTITION_COLUMN_TEMPLATE, databaseName, tableName));

    // Find first partition column
    String partitionColumnName = null;

    while (rs.next()) {
      String columnName = rs.getString(2);
      String isPartitionColumn = rs.getString(3);
      if (PARTITION_COLUMN_YES.equalsIgnoreCase(isPartitionColumn)){
        partitionColumnName = columnName;
        break;
      }
    }

    if (partitionColumnName != null){
      String partitionFilter = String.format(SQL_PARTITION_FILTER_TEMPLATE, partitionColumnName);
      String sqlQueryWithPartitionFilter = sqlQuery.replaceAll(
              SQL_END_REGEX_STRING, partitionFilter + " $1");
      return stmt.executeQuery(sqlQueryWithPartitionFilter);
    }

    return null;
  }
}