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

import com.google.cloud.datacatalog.v1beta1.DataCatalogClient;
import com.google.cloud.datacatalog.v1beta1.Entry;
import com.google.cloud.datacatalog.v1beta1.LookupEntryRequest;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EntryNameInitializer {

  private static final Logger LOG = LoggerFactory.getLogger(EntryNameInitializer.class);

  public static String lookupEntryName(String fullTableName, DataCatalogClient dataCatalogClient) {
    // Format example: project:dataset.table
    String entryName = null;

    Pattern pattern = Pattern.compile("(.*):(.*)\\.(.*)");
    Matcher matcher = pattern.matcher(fullTableName);
    if (matcher.matches()) {
      String project = matcher.group(1);
      String dataset = matcher.group(2);
      String table = matcher.group(3);

      String linkedResource =
          String.format(
              "//bigquery.googleapis.com/projects/%s/datasets/%s/tables/%s",
              project, dataset, table);

      LOG.debug(
          "{} - linkedResource: {}", LoggingPrefix.get("EntryNameInitializer"), linkedResource);

      LookupEntryRequest lookupEntryRequest =
          LookupEntryRequest.newBuilder().setLinkedResource(linkedResource).build();
      Entry tableEntry = dataCatalogClient.lookupEntry(lookupEntryRequest);
      entryName = tableEntry.getName();

      LOG.debug("{} - entryName: {}", LoggingPrefix.get("EntryNameInitializer"), entryName);
    }

    if (entryName == null) {
      throw new RuntimeException("Unable to setup Entry Name");
    }
    return entryName;
  }
}
