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
ClaimsRoutingApp.app = ClaimsRoutingApp.app || {};

ClaimsRoutingApp.app.redirectToSignIn = () => {
  window.location.assign('signin');
};

ClaimsRoutingApp.app.enableSignOut = () => {
  document.getElementById('signout').onclick = (event) => {
    event.preventDefault();
    firebase.auth().signOut();
  };
};

ClaimsRoutingApp.app.isBeta = async (user) => {
  // [START claims_routing_identity_platform_app_static_app_isbeta]
  const idTokenResult = await user.getIdTokenResult();
  return idTokenResult.claims.version === 'beta';
  // [END claims_routing_identity_platform_app_static_app_isbeta]
};

ClaimsRoutingApp.app.showBetaLinkIfBetaUser = async (user) => {
  if (await ClaimsRoutingApp.app.isBeta(user)) {
    const betaElement = document.getElementById('gotobeta');
    if (betaElement) {
      betaElement.classList.remove('hidden');
    }
  }
};

ClaimsRoutingApp.app.showGreeting = (user) => {
  document.getElementById('userEmail').innerText =
      user.displayName ? user.displayName : user.email;
};

ClaimsRoutingApp.app.showPage = () => {
  document.getElementById('container').classList.remove('hidden');
};

window.addEventListener('load', () => {
  firebase.auth().onAuthStateChanged(async (user) => {
    if (!user) {
      return ClaimsRoutingApp.app.redirectToSignIn();
    }
    ClaimsRoutingApp.app.enableSignOut();
    await ClaimsRoutingApp.app.showBetaLinkIfBetaUser(user);
    ClaimsRoutingApp.app.showGreeting(user);
    ClaimsRoutingApp.app.showPage();
  });
});
