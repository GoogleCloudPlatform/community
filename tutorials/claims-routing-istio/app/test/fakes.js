/*
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Test double of the `fetch` API.
 * @param {string} resource The URL being fetched
 * @param {object} init Custom settings applied to the request
 * @return {Promise<Response>}
 */
export async function fetch (resource, init = {}) {
  if (!init.method) {
    init.method = 'GET'; // fetch uses HTTP GET by default
  }
  if (init.method.toLowerCase() === 'post' &&
      init.headers['Content-Type'] === 'application/json' &&
      init.headers['Authorization'] === 'Bearer validToken') {
    fetch.requestBody = init.body; // save request body for test assertions
    return {
      ok: true,
      statusText: 'OK',
      text: async () => `${init.body}`
    };
  }
  if (init.method.toLowerCase() === 'get' &&
      init.headers.Authorization === 'Bearer validToken') {
    return {
      ok: true,
      statusText: 'OK',
      text: async () => `${resource} text`
    };
  }
  return {
    ok: false,
    statusText: `failed for ${init.method} on ${resource} with ` +
      `Authorization ${init.headers.Authorization}`,
    text: async () => `${resource} error`
  };
}

/**
 * Creates a test double of the Identity Platform / Firebase Authentication
 * User object.
 * @param {object} params User parameters
 * @return {firebase.User}
 */
export function user (params = {}) {
  return {
    displayName: params.displayName || 'Fake User',
    email: params.email || 'user@example.com',
    getIdToken: async () => params.token || 'validToken',
    getIdTokenResult: async () => ({
      claims: {
        version: params.version || 'stable'
      }
    })
  };
}

// [START claims_routing_identity_platform_app_test_fakes_firebase]
/**
 * Creates a `firebase` test double that saves observer function references to
 * the provided context object (e.g., tap.context), so we can invoke them
 * directly in tests by accessing the same context object.
 * @param {object} context The test context
 * @return {firebase.auth.Auth}
 */
export function firebase (context = {}) {
  const auth = {};
  auth.onAuthStateChanged = (fn) => {
    context.onAuthStateChanged = fn;
  };
  auth.onIdTokenChanged = (fn) => {
    context.onIdTokenChanged = fn;
  };
  auth.signOut = () => {
    auth.signedOut = true;
  };
  return {
    auth: () => auth
  };
}
// [END claims_routing_identity_platform_app_test_fakes_firebase]
