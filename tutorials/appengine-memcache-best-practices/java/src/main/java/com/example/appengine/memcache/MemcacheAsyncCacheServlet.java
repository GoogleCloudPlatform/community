/**
 * Copyright 2016 Google Inc. All Rights Reserved.
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

package com.example.appengine.memcache;

import com.google.appengine.api.memcache.AsyncMemcacheService;
import com.google.appengine.api.memcache.ErrorHandlers;
import com.google.appengine.api.memcache.MemcacheServiceFactory;

import java.io.IOException;
import java.math.BigInteger;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.logging.Level;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@SuppressWarnings("serial")
public class MemcacheAsyncCacheServlet extends HttpServlet {

  @Override
  public void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException,
      ServletException {
    String path = req.getRequestURI();
    if (path.startsWith("/favicon.ico")) {
      return; // ignore the request for favicon.ico
    }

    // [START example]
    AsyncMemcacheService asyncCache = MemcacheServiceFactory.getAsyncMemcacheService();
    asyncCache.setErrorHandler(ErrorHandlers.getConsistentLogAndContinue(Level.INFO));
    String key = "count-async";
    byte[] value;
    long count = 1;
    Future<Object> futureValue = asyncCache.get(key); // Read from cache.
    // ... Do other work in parallel to cache retrieval.
    try {
      value = (byte[]) futureValue.get();
      if (value == null) {
        value = BigInteger.valueOf(count).toByteArray();
        asyncCache.put(key, value);
      } else {
        // Increment value
        count = new BigInteger(value).longValue();
        count++;
        value = BigInteger.valueOf(count).toByteArray();
        // Put back in cache
        asyncCache.put(key, value);
      }
    } catch (InterruptedException | ExecutionException e) {
      throw new ServletException("Error when waiting for future value", e);
    }
    // [END example]

    // Output content
    resp.setContentType("text/plain");
    resp.getWriter().print("Value is " + count + "\n");
  }
}
