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
  const dom = await DOM.fromFile('./templates/signin.gohtml');

  // add `dom` to the test context for use by child tests
  t.context.dom = dom;

  // load code under test
  dom.window.eval(await fs.promises.readFile('./static/signin.js', 'utf8'));

  // trigger load event listeners from code under test
  event.dispatch(dom.window.document, 'load', dom.window);

  done();
});

t.test('redirect to signInSuccessUrl for regular users', async (t) => {
  // get handy `window` reference
  const window = t.context.dom.window;

  // directly invoke signInSuccessHandler with regular user
  t.ok(await window.ClaimsRoutingApp.signin.handleSignInSuccess({
    user: fake.user()
  }));
  t.end();
});

t.test('navigate to beta page for beta users on sign in success', async (t) => {
  // get handy `window` reference
  const window = t.context.dom.window;

  // directly invoke signInSuccessHandler with beta user
  t.notOk(await window.ClaimsRoutingApp.signin.handleSignInSuccess({
    user: fake.user({version: 'beta'})
  }));
  t.end();
});
