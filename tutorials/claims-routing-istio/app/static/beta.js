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

/* globals ClaimsRoutingApp, firebase */

window.ClaimsRoutingApp = window.ClaimsRoutingApp || {};
ClaimsRoutingApp.beta = ClaimsRoutingApp.beta || {};

ClaimsRoutingApp.beta.deepThought = async (user) => {
  try {
    const token = await user.getIdToken();
    const resp = await window.fetch('api/beta', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    if (!resp.ok) {
      throw Error(resp.statusText);
    }
    const answer = await resp.text();
    document.getElementById('answer').textContent = answer;
  } catch (e) {
    console.error(e);
    document.getElementById('answer').textContent = e;
  }
};

window.addEventListener('load', () => {
  firebase.auth().onAuthStateChanged(async (user) => {
    if (!user) {
      return;
    }
    document.getElementById('getanswer').onclick = async (event) => {
      event.preventDefault();
      await ClaimsRoutingApp.beta.deepThought(user);
    };
  });
});
