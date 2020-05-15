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
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.OptionGroup;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

public class ParseArgs {

  private boolean error;
  private String[] args;
  private CommandLine cmd;
  private String minThreshold;
  private String projectId;
  private String dbName;
  private String tableName;
  private String dbType;
  private String limitMax;
  private String inspectTemplate;
  private String threadPoolSize;

  public ParseArgs(String... args) {
    this.args = args;
  }

  boolean error() {
    return error;
  }

  public CommandLine getCmd() {
    return cmd;
  }

  public String getMinThreshold() {
    return minThreshold;
  }

  public String getProjectId() {
    return projectId;
  }

  public String getDbName() {
    return dbName;
  }

  public String getTableName() {
    return tableName;
  }

  public String getDbType() {
    return dbType;
  }

  public String getLimitMax() {
    return limitMax;
  }

  public String getInspectTemplate() {
    return inspectTemplate;
  }

  public String getThreadPoolSize() {
    return threadPoolSize;
  }

  public ParseArgs invoke() {
    OptionGroup optionsGroup = new OptionGroup();
    optionsGroup.setRequired(true);
    Option dbTypeOption = new Option("dbType", "dbType", true, "Database Type");
    optionsGroup.addOption(dbTypeOption);

    Options commandLineOptions = new Options();
    commandLineOptions.addOptionGroup(optionsGroup);

    Option minLikelihoodOption =
        Option.builder("minLikelihood").hasArg(true).required(false).build();

    commandLineOptions.addOption(minLikelihoodOption);

    Option dbNameOption = Option.builder("dbName").hasArg(true).required(false).build();
    commandLineOptions.addOption(dbNameOption);

    Option tableNameOption = Option.builder("tableName").hasArg(true).required(false).build();
    commandLineOptions.addOption(tableNameOption);

    Option limitMaxOption = Option.builder("limitMax").hasArg(true).required(false).build();
    commandLineOptions.addOption(limitMaxOption);

    Option inspectTemplateOption =
        Option.builder("inspectTemplate").hasArg(true).required(false).build();
    commandLineOptions.addOption(inspectTemplateOption);

    Option threadPoolSizeOption =
        Option.builder("threadPoolSize").hasArg(true).required(false).build();
    commandLineOptions.addOption(threadPoolSizeOption);

    Option projectIdOption = Option.builder("projectId").hasArg(true).required(false).build();
    commandLineOptions.addOption(projectIdOption);

    Option minThresholdOption = Option.builder("minThreshold").hasArg(true).required(false).build();
    commandLineOptions.addOption(minThresholdOption);

    CommandLineParser parser = new DefaultParser();
    HelpFormatter formatter = new HelpFormatter();

    try {
      cmd = parser.parse(commandLineOptions, args);
    } catch (ParseException e) {
      System.out.println(e.getMessage());
      formatter.printHelp(DlpDataCatalogTagsTutorial.class.getName(), commandLineOptions);
      System.exit(1);
      error = true;
      return this;
    }

    minThreshold = cmd.getOptionValue(minThresholdOption.getOpt(), "10");

    projectId = cmd
        .getOptionValue(projectIdOption.getOpt(), ServiceOptions.getDefaultProjectId());

    dbName = cmd.getOptionValue(dbNameOption.getOpt());
    tableName = cmd.getOptionValue(tableNameOption.getOpt());
    dbType = cmd.getOptionValue(dbTypeOption.getOpt());
    limitMax = cmd.getOptionValue(limitMaxOption.getOpt());
    inspectTemplate = cmd.getOptionValue(inspectTemplateOption.getOpt());
    threadPoolSize = cmd.getOptionValue(threadPoolSizeOption.getOpt());
    error = false;
    return this;
  }
}
