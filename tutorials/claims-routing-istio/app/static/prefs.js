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

/* globals ClaimsRoutingApp, FormData, fetch, firebase */

window.ClaimsRoutingApp = window.ClaimsRoutingApp || {};
if (!ClaimsRoutingApp.app) {
  throw new Error('Must load app.js first');
}
ClaimsRoutingApp.prefs = ClaimsRoutingApp.prefs || {};

ClaimsRoutingApp.prefs.updateHomePageLink = async (user) => {
  if ((await ClaimsRoutingApp.app.isBeta(user))) {
    document.getElementById('home').href = 'beta';
  } else {
    document.getElementById('home').href = '.';
  }
};

ClaimsRoutingApp.prefs.getPrefs = async (user) => {
  const idTokenResult = await user.getIdTokenResult();
  if (!Object.keys(idTokenResult.claims).length) {
    return;
  }
  for (const [pref, val] of Object.entries(idTokenResult.claims)) {
    const el = document.querySelector(`input[name='${pref}'][value='${val}']`);
    if (el) {
      el.checked = true;
    }
  }
  document.getElementById('prefsForm').classList.remove('hidden');
};

ClaimsRoutingApp.prefs.enablePrefsForm = (user) => {
  document.getElementById('updatePrefs').onclick = async (event) => {
    event.preventDefault();
    try {
      // [START claims_routing_identity_platform_app_static_prefs_updateprefs]
      const prefsForm = document.getElementById('prefsForm');
      const prefsFormData = new FormData(prefsForm);
      const requestBody = JSON.stringify(Object.fromEntries(prefsFormData));
      const token = await user.getIdToken();
      const resp = await fetch('api/user', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: requestBody
      });
      // [END claims_routing_identity_platform_app_static_prefs_updateprefs]
      if (!resp.ok) {
        throw Error(resp.statusText);
      }
      await user.getIdToken(true); // force ID token refresh
      document.getElementById('updateError').classList.add('hidden');
      document.getElementById('updateNotice').classList.remove('hidden');
    } catch (e) {
      console.error(e);
      document.getElementById('updateError').classList.remove('hidden');
      document.getElementById('updateNotice').classList.add('hidden');
    }
  };
};

// [START claims_routing_identity_platform_app_test_prefs_observer]
window.addEventListener('load', () => {
  firebase.auth().onIdTokenChanged(async (user) => {
    if (!user) {
      return;
    }
    await ClaimsRoutingApp.prefs.updateHomePageLink(user);
    await ClaimsRoutingApp.prefs.getPrefs(user);
    ClaimsRoutingApp.prefs.enablePrefsForm(user);
  });
});
// [END claims_routing_identity_platform_app_test_prefs_observer]
