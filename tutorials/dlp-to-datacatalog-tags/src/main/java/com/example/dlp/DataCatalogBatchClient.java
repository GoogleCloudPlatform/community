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

import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.batch.BatchRequest;
import com.google.api.client.googleapis.batch.json.JsonBatchCallback;
import com.google.api.client.googleapis.json.GoogleJsonError;
import com.google.api.client.http.HttpHeaders;
import com.google.api.client.http.HttpRequestInitializer;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.datacatalog.v1beta1.DataCatalog;
import com.google.api.services.datacatalog.v1beta1.model.GoogleCloudDatacatalogV1beta1Tag;
import java.util.Collections;

public class DataCatalogBatchClient {

  private static boolean VERBOSE_OUTPUT = false; // toggle for more detailed output
  private static final JsonFactory JSON_FACTORY = new JacksonFactory();
  private static final NetHttpTransport NET_HTTP_TRANSPORT = new NetHttpTransport();
  private static final String SCOPES = "https://www.googleapis.com/auth/cloud-platform";
  private static final String DEFAULT_PROJECT_ID =
      "projects/" + System.getenv("GOOGLE_CLOUD_PROJECT");

  private static DataCatalog dataCatalogClient = createDataCatalogClient(generateCredential());

  private static DataCatalog createDataCatalogClient(GoogleCredential credential) {
    String url = "https://us-datacatalog.googleapis.com";

    return new DataCatalog.Builder(NET_HTTP_TRANSPORT, JSON_FACTORY, setHttpTimeout(credential))
        .setApplicationName("DataCatalogBatchClient")
        .setRootUrl(url)
        .build();
  }

  private static GoogleCredential generateCredential() {
    try {
      // Credentials could be downloaded after creating service account
      // set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable, for example:
      // export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json
      return GoogleCredential.getApplicationDefault(NET_HTTP_TRANSPORT, JSON_FACTORY)
          .createScoped(Collections.singleton(SCOPES));
    } catch (Exception e) {
      System.out.print("Error in generating credential");
      throw new RuntimeException(e);
    }
  }

  private static HttpRequestInitializer setHttpTimeout(
      final HttpRequestInitializer requestInitializer) {
    return request -> {
      requestInitializer.initialize(request);
      request.setConnectTimeout(1 * 60000); // 1 minute connect timeout
      request.setReadTimeout(1 * 60000); // 1 minute read timeout
    };
  }

  public static JsonBatchCallback<GoogleCloudDatacatalogV1beta1Tag> createdTagCallback =
      new JsonBatchCallback<GoogleCloudDatacatalogV1beta1Tag>() {
        @Override
        public void onFailure(GoogleJsonError e, HttpHeaders responseHeaders) {
          System.out.println("Create Tag Error Message: " + e.getMessage());
        }

        @Override
        public void onSuccess(GoogleCloudDatacatalogV1beta1Tag tag, HttpHeaders responseHeaders) {
          if (VERBOSE_OUTPUT) {
            System.out.println("[Created]");
          } else {
            System.out.print(".");
          }
        }
      };

  public static JsonBatchCallback<GoogleCloudDatacatalogV1beta1Tag> updatedTagCallback =
      new JsonBatchCallback<GoogleCloudDatacatalogV1beta1Tag>() {
        @Override
        public void onFailure(GoogleJsonError e, HttpHeaders responseHeaders) {
          System.out.println("Update Tag Error Message: " + e.getMessage());
        }

        @Override
        public void onSuccess(GoogleCloudDatacatalogV1beta1Tag tag, HttpHeaders responseHeaders) {
          if (VERBOSE_OUTPUT) {
            System.out.println("[Updated]");
          } else {
            System.out.print(".");
          }
        }
      };

  public static DataCatalog getBatchClient() {
    return dataCatalogClient;
  }

  public static BatchRequest getBatchRequest() {
    return dataCatalogClient.batch();
  }
}
