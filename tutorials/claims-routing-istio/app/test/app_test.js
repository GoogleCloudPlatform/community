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
  const dom = await DOM.fromFile('./templates/index.gohtml');

  // add `dom` to the test context for use by child tests
  t.context.dom = dom;

  // use fake for `firebase`
  dom.window.firebase = fake.firebase(t.context);

  // load code under test
  dom.window.eval(await fs.promises.readFile('./static/app.js', 'utf8'));

  // trigger load event listeners from code under test
  event.dispatch(dom.window.document, 'load', dom.window);

  done();
});

t.test('should sign out using sign out button', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler
  await t.context.onAuthStateChanged(fake.user());

  // trigger sign out click event
  event.dispatch(document, 'click', document.getElementById('signout'));

  t.ok(window.firebase.auth().signedOut);
  t.end();
});

t.test('should show user display name if available', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler
  await t.context.onAuthStateChanged(fake.user({displayName: 'foo bar'}));

  t.equal(document.getElementById('userEmail').innerText, 'foo bar');
  t.end();
});

t.test('should show user email if display name is unavailable', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler, with a user object that doesn't
  // have the displayName property
  const email = 'test@example.com';
  const user = fake.user({email: email});
  user.displayName = undefined;
  await t.context.onAuthStateChanged(user);

  t.equal(document.getElementById('userEmail').innerText, email);
  t.end();
});

t.test('should show beta section for beta user', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with a beta user
  await t.context.onAuthStateChanged(fake.user({version: 'beta'}));

  const betaElemClasses = document.getElementById('gotobeta').classList;
  t.notOk(betaElemClasses.contains('hidden'), betaElemClasses);
  t.end();
});

t.test('should not show beta section for regular user', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with a regular user
  await t.context.onAuthStateChanged(fake.user());

  const betaElemClasses = document.getElementById('gotobeta').classList;
  t.ok(betaElemClasses.contains('hidden'), betaElemClasses);
  t.end();
});

t.test('should show page for authenticated user', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with a regular user
  await t.context.onAuthStateChanged(fake.user());

  const containerClasses = document.getElementById('container').classList;
  t.notOk(containerClasses.contains('hidden'), containerClasses);
  t.end();
});

t.test('should not show page for unauthenticated user', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with null user
  await t.context.onAuthStateChanged(null);

  const containerClasses = document.getElementById('container').classList;
  t.ok(containerClasses.contains('hidden'), containerClasses);
  t.end();
});
