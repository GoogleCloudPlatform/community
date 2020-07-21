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

import './asserts.js';
import * as event from './events.js';
import * as fake from './fakes.js';
import * as DOM from './dom.js';
import fs from 'fs';
import t from 'tap';

const baseURL = 'https://example.com/';

t.beforeEach(async (done, t) => {
  const dom = await DOM.fromFile('./templates/prefs.gohtml', {
    // set window location
    url: `${baseURL}prefs`
  });

  // add `dom` to the test context for use by child tests
  t.context.dom = dom;

  // use fakes for `fetch` and `firebase`
  dom.window.fetch = fake.fetch;
  dom.window.firebase = fake.firebase(t.context);

  // load code under test
  dom.window.eval(await fs.promises.readFile('./static/app.js', 'utf8'));
  dom.window.eval(await fs.promises.readFile('./static/prefs.js', 'utf8'));

  // trigger load event listeners from code under test
  event.dispatch(dom.window.document, 'load', dom.window);

  done();
});

t.test('should link to home page for regular users', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with regular user
  await t.context.onIdTokenChanged(fake.user());

  t.equal(document.getElementById('home').href, baseURL);
  t.end();
});

t.test('should link to beta page for beta users', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with regular user
  await t.context.onIdTokenChanged(fake.user({version: 'beta'}));

  t.equal(document.getElementById('home').href, `${baseURL}beta`);
  t.end();
});

t.test('should update form to reflect user custom claims', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with regular user
  await t.context.onIdTokenChanged(fake.user());

  t.notOk(document.getElementById('version_beta').checked);
  t.end();
});

// [START claims_routing_identity_platform_app_test_prefs_test_observer]
t.test('should update form to reflect beta user custom claims', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with beta user
  await t.context.onIdTokenChanged(fake.user({version: 'beta'}));

  t.ok(document.getElementById('version_beta').checked);
  t.end();
});
// [END claims_routing_identity_platform_app_test_prefs_test_observer]

t.test('should submit preference form and display notice', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with beta user
  await t.context.onIdTokenChanged(fake.user({version: 'beta'}));

  event.dispatch(document, 'click', document.getElementById('updatePrefs'));

  const want = '{"version":"beta"}';
  await t.waitForEqual(
    () => window.fetch.requestBody, want, window.fetch.requestBody);

  await t.waitForNotOk(
    () => document.getElementById('updateNotice').classList.contains('hidden'),
    document.getElementById('updateNotice').classList
  );

  await t.waitForOk(
    () => document.getElementById('updateError').classList.contains('hidden'),
    document.getElementById('updateError').classList
  );
  t.end();
});

t.test('should show error notice on failed form submission', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with invalid user token
  await t.context.onIdTokenChanged(fake.user({token: 'invalid'}));

  event.dispatch(document, 'click', document.getElementById('updatePrefs'));

  await t.waitForOk(
    () => document.getElementById('updateNotice').classList.contains('hidden'),
    document.getElementById('updateNotice').classList
  );

  await t.waitForNotOk(
    () => document.getElementById('updateError').classList.contains('hidden'),
    document.getElementById('updateError').classList
  );
  t.end();
});
