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

t.beforeEach(async (done, t) => {
  const dom = await DOM.fromFile('./templates/beta.gohtml');

  // add `dom` to the test context for use by child tests
  t.context.dom = dom;

  // use fakes for `fetch` and `firebase`
  dom.window.fetch = fake.fetch;
  dom.window.firebase = fake.firebase(t.context);

  // load code under test
  dom.window.eval(await fs.promises.readFile('./static/beta.js', 'utf8'));

  // trigger load event listeners from code under test
  event.dispatch(dom.window.document, 'load', dom.window);

  done();
});

t.test('should display answer for authenticated user', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler
  await t.context.onAuthStateChanged(fake.user());

  // trigger click event
  event.dispatch(document, 'click', document.getElementById('getanswer'));

  const want = 'api/beta text';
  await t.waitForEqual(
    () => document.getElementById('answer').textContent, want);
  t.end();
});

t.test('should display error for invalid token', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler, providing user with invalid token
  await t.context.onAuthStateChanged(fake.user({token: 'invalid'}));

  // trigger click event
  event.dispatch(document, 'click', document.getElementById('getanswer'));

  await t.waitForOk(() => {
    return document.getElementById('answer').textContent.startsWith('Error');
  });
  t.end();
});
