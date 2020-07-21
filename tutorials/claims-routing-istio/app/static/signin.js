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

/* globals ClaimsRoutingApp, firebase, firebaseui */

window.ClaimsRoutingApp = window.ClaimsRoutingApp || {};
ClaimsRoutingApp.signin = ClaimsRoutingApp.signin || {};

ClaimsRoutingApp.signin.handleSignInSuccess = async (authResult) => {
  const idTokenResult = await authResult.user.getIdTokenResult();
  if (idTokenResult.claims.version === 'beta') {
    window.location.assign('beta');
    return false; // prevent redirect to signInSuccessUrl
  }
  return true; // redirects to signInSuccessUrl
};

window.addEventListener('load', () => {
  firebase.auth().onAuthStateChanged((user) => {
    if (user) {
      // redirect authenticated users to the home page
      return window.location.assign('.');
    }
    const ui = new firebaseui.auth.AuthUI(firebase.auth());
    const uiConfig = {
      callbacks: {
        signInSuccessWithAuthResult: (authResult) => {
          ClaimsRoutingApp.signin.handleSignInSuccess(authResult);
        }
      },
      credentialHelper: firebaseui.auth.CredentialHelper.NONE,
      signInOptions: [
        firebase.auth.EmailAuthProvider.PROVIDER_ID
      ],
      signInSuccessUrl: '.'
    };
    ui.start('#firebaseui-auth-container', uiConfig);
  });
});
