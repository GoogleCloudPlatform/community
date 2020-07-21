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

import jsdom from 'jsdom';

/**
 * Loads a HTML page or fragment by path. Waits for the page to load.
 * @param {string} url The file path of the HTML file
 * @param {object} params jsdom parameters, see
 *   https://github.com/jsdom/jsdom#customizing-jsdom
 * @return {jsdom.JSDOM}
 */
export async function fromFile (url, params = {}) {
  // enable injecting scripts using `window.eval`
  if (!params.runScripts) {
    params.runScripts = 'outside-only';
  }

  // Hide "browser" console output when running tests using the `tap` command.
  // You can run tests directly with node <test> to see console output.
  // Hiding the console output is useful when testing for expected errors.
  if (process.env.TAP) {
    params.virtualConsole = new jsdom.VirtualConsole();
  }

  // load html
  const dom = await jsdom.JSDOM.fromFile(url, params);

  // wait for the page to load
  await new Promise((resolve) => dom.window.addEventListener('load', resolve));

  return dom;
}
