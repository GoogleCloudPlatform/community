/*
# Copyright Google Inc. 2018
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
*/

package com.example.memorystore;

import com.google.cloud.storage.Blob;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;
import io.opencensus.common.Scope;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceConfiguration;
import io.opencensus.exporter.trace.stackdriver.StackdriverTraceExporter;
import io.opencensus.trace.Tracer;
import io.opencensus.trace.Tracing;
import io.opencensus.trace.config.TraceConfig;
import io.opencensus.trace.samplers.Samplers;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;

import java.io.IOException;

public class App {

    private static final String PROJECT_ID = "[YOUR PROJECT ID]";
    private static final String GCS_BUCKET_NAME = "[YOUR BUCKET NAME]";
    private static final String GCS_OBJECT_NAME = "person.json";
    private static final String REDIS_HOST = "[YOUR REDIS HOST]";

    private static final String CACHE_KEY = "REDIS_CACHE_KEY";

    private static final Tracer tracer = Tracing.getTracer();

    private static JedisPool jedisPool;

    public static void main(String[] args) throws IOException, InterruptedException {
        configureOpenCensusExporters();

        // initialize jedis pool
        jedisPool = new JedisPool(REDIS_HOST);

        try (Scope ss = tracer.spanBuilder("In main").startScopedSpan()) {

            // do initial read from GCS
            String jsonPayloadFromGCS = readFromGCS();

            // now write to Redis
            writeToCache(jsonPayloadFromGCS);

            // read from Redis
            String jsonPayloadFromCache = readFromCache();

            if (jsonPayloadFromCache.equals(jsonPayloadFromGCS)) {
                System.out.println("SUCCESS: Value from cache = value from GCS");
            } else {
                System.out.println("ERROR: Value from cache != value from GCS");
            }
        }

        // IMPORTANT: do NOT exit right away. OpenCensus needs time to
        // send traces to backend (Stackdriver in this case)
        int secondsToWait = 15;
        System.out.println("Exiting in " + String.valueOf(secondsToWait) + "s...");
        for(int i = secondsToWait-1; i >= 0; i--) {
            Thread.sleep(1000);
            System.out.println(String.valueOf(i) + "s...");
        }

        System.exit(0);
    }

    private static String readFromGCS() {
        try (Scope ss = tracer.spanBuilder("In readFromGCS").startScopedSpan()) {
            Storage storage = StorageOptions.getDefaultInstance().getService();

            Blob blob = storage.get(GCS_BUCKET_NAME, GCS_OBJECT_NAME);

            String content = new String(blob.getContent());

            return content;
        }
    }

    private static void writeToCache(String payload) {
        try (Scope ss = tracer.spanBuilder("In writeToCache").startScopedSpan()) {

            Jedis jedis = null;

            try {
                jedis = jedisPool.getResource();
                jedis.set(CACHE_KEY, payload);
            } finally {
                if (jedis != null) {
                    jedis.close();
                }
            }
        }
    }

    private static String readFromCache() {
        try (Scope ss = tracer.spanBuilder("In readFromCache").startScopedSpan()) {

            Jedis jedis = null;

            try {
                jedis = jedisPool.getResource();
                return jedis.get(CACHE_KEY);
            } finally {
                if (jedis != null) {
                    jedis.close();
                }
            }
        }
    }

    private static void configureOpenCensusExporters() throws IOException {
        TraceConfig traceConfig = Tracing.getTraceConfig();

        // For demo purposes, lets always sample.
        traceConfig.updateActiveTraceParams(
            traceConfig.getActiveTraceParams().toBuilder().setSampler(Samplers.alwaysSample()).build());

        // Create the Stackdriver trace exporter
        StackdriverTraceExporter.createAndRegister(
            StackdriverTraceConfiguration.builder()
                .setProjectId(PROJECT_ID)
                .build());
    }
}