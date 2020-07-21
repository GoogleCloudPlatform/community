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

import t from 'tap';

// tap.waitForOk is similar to tap.ok, but it waits up to 5 seconds for
// the result of the provided function `fn` to be truthy.
t.Test.prototype.addAssert('waitForOk', 3,
  async (fn, waittimes = 5, waitms = 1000, message, extra) => {
    const result = await waitForOk(fn, waittimes, waitms);
    return t.ok(result, message, extra);
  }
);

const waitForOk = async (fn, waittimes, waitms) => {
  let counter = 0;
  while (!fn()) {
    if (counter++ >= waittimes) {
      return false;
    }
    await wait(waitms);
  }
  return true;
};

// tap.waitForNotOk is similar to tap.notOk, but it waits up to 5 seconds for
// the result of the provided function `fn` to be falsy.
t.Test.prototype.addAssert('waitForNotOk', 3,
  async (fn, waittimes = 5, waitms = 1000, message, extra) => {
    const result = await waitForNotOk(fn, waittimes, waitms);
    return t.notOk(result, message, extra);
  }
);

const waitForNotOk = async (fn, waittimes, waitms) => {
  let counter = 0;
  while (fn()) {
    if (counter++ >= waittimes) {
      return true;
    }
    await wait(waitms);
  }
  return false;
};

// tap.waitForEqual is similar to tap.Equal, but it waits up to 5 seconds for
// the result of the provided function `fn` to be strictly equal to `want`.
t.Test.prototype.addAssert('waitForEqual', 4,
  async (fn, want, waittimes = 5, waitms = 1000, message, extra) => {
    const result = await waitForEqual(fn, want, waittimes, waitms);
    return t.equal(result, want, message, extra);
  }
);

const waitForEqual = async (fn, want, waittimes, waitms) => {
  let counter = 0;
  let result;
  while ((result = fn()) !== want) {
    if (counter++ >= waittimes) {
      return result;
    }
    await wait(waitms);
  }
  return result;
};

const wait = (waitms) => {
  return new Promise((resolve) => {
    setTimeout(resolve, waitms);
  });
};

export {};
