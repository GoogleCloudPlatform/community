---
title: Using OAuth 2.0 and Google Cloud Functions to access Google services
description: Learn how to use OAuth 2.0 with Google Cloud Functions to access a user's data from Google services.
author: ace-n
tags: Cloud Functions, OAuth, Gmail, G Suite
date_published: 2018-01-05
---

## Background
[OAuth 2.0](https://oauth.net/2) is a community standard that allows users to grant programs access to user data in a secure and reliable manner. In this tutorial, we'll be using a process known as _3-legged OAuth_ (3LO). Instead of storing usernames and passwords, 3LO lets you store _authorization codes_. These can then be securely converted into _authorization tokens_, which can grant access to user data on Google services such as Gmail.

This tutorial assumes you've [set up your environment][docs_setup] for developing on Google Cloud Platform (GCP). Furthermore, this tutorial covers authenticating with Google services outside of Google Cloud Platform. If you'd like to interact with Google Cloud Platform services, [see the documentation][docs_gcp_auth] for more information.

This process involves several steps:
- _Generating an OAuth 2.0 client ID_, which the client can use to authenticate itself with OAuth 2.0 APIs
- _Configuring local files_ with GCP-project-specific information
- _Deployment_ of local files to Cloud Functions

## Configuration
### Generating an OAuth 2.0 client ID
In order for an OAuth 2.0 API to verify our program's identity, we must include an _OAuth 2.0 client ID_ with some of our requests to the API. The following steps show how to enable the Gmail API and download the client ID to your local machine.

1. Enable the Gmail API by [visiting the _Enable an API_ page in the GCP Console][console_gmail] (under **APIs** > **Enable APIs and Services**) and selecting the appropriate GCP Project.
1. Find the [GCP region][docs_regions] you want to deploy your function to. (In general, response time is quickest for the regions closest to you.) For the rest of this tutorial, replace `[YOUR_GCF_REGION]` with your selected region's name (for example, `us-central1`).
1. Generate a new OAuth 2.0 client ID by [visiting the GCP Console credentials page][console_credentials]. Configure the fields as indicated below:
    - Application type: `Web application`
    - Name: an appropriate, memorable name for your client
    - Authorized JavaScript origins: `https://[YOUR_GCF_REGION]-[YOUR_GCP_PROJECT_ID].cloudfunctions.net/oauth2callback`
1. Click _Create_, then close the resulting dialog box and click the **Download** icon next to your newly created client ID. The resulting file is your __Client Secret file__.

### Configuring local files
Now that you've created a _Client Secret file_, you can download the code and configure it to use a particular GCP project and Cloud Functions execution region. The function needs this information when running on Cloud Functions, so these changes must be made prior to deployment.

1. [Clone the repo][github_repo], and `cd` into the `cloud-functions-oauth-gmail` directory.

       git clone https://github.com/GoogleCloudPlatform/community
       cd community/tutorials/cloud-functions-oauth-gmail

1. Rename your __Client Secret file__ to `client_secret.json`, and move it to the directory that your `index.js` file is in.
1. In `index.js`, replace `[YOUR_GCP_PROJECT_ID]` and `[YOUR_GCF_REGION]` with your GCP Project ID and GCF region ID respectively.

## Deployment
Once you've configured your local files appropriately, run the following commands in the same directory as `index.js` to deploy the appropriate Cloud Functions:

    gcloud beta functions deploy oauth2init --trigger-http
    gcloud beta functions deploy oauth2callback --trigger-http
    gcloud beta functions deploy listlabels --trigger-http

Visit `https://[YOUR_GCF_REGION]-[YOUR_GCP_PROJECT_ID].cloudfunctions.net/oauth2init` to see your Cloud Functions in action, or go to [the GCP Console's **Stackdriver** page][console_stackdriver] to see the logs.

## Code overview
The code in this tutorial implements 3LO using Cloud Functions and the Gmail API. Below is a brief synopsis of the key parts of `index.js`.

### Requesting an authorization code
The first step of 3LO is to request an authorization code. The `scopes` field defines what permissions the generated authorization code will grant. For this tutorial, we need read-only access to a user's Gmail account.

```javascript
exports.oauth2init = (req, res) => {
  // Parse session cookie
  // Note: this presumes 'token' is the only value in the cookie
  const cookieStr = (req.headers.cookie || '').split('=')[1];
  const token = cookieStr ? JSON.parse(decodeURIComponent(cookieStr)) : null;

  // If the current OAuth token hasn't expired yet, go to /listlabels
  if (token && token.expiry_date && token.expiry_date >= Date.now() + 60000) {
    return res.redirect('/listlabels');
  }

  // Define OAuth2 scopes
  const scopes = [
    'https://www.googleapis.com/auth/gmail.readonly'
  ];

  // Generate + redirect to OAuth2 consent form URL
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'online',
    scope: scopes
  });
  res.redirect(authUrl);
};
```

### Handling the authorization token
The second step of 3LO is to receive the authorization code (via a _callback URL_) and store it for safekeeping. In this example, we store it in a cookie on the user's machine.

```javascript
exports.oauth2Callback = (req, res) => {
  // Get authorization details from request
  const code = req.query.code;

  return new Promise((resolve, reject) => {
    // OAuth2: Exchange authorization code for access token
    oauth2Client.getToken(code, (err, token) => {
      if (err) {
        return reject(err);
      }
      return resolve(token);
    });
  })
    .then((token) => {
      // Respond with OAuth token stored as a cookie
      res.cookie('token', JSON.stringify(token));
      res.redirect('/listlabels');
    })
    .catch((err) => {
      // Handle error
      console.error(err);
      res.status(500).send('Something went wrong; check the logs.');
    });
};
```

### Interacting with Google services
The final step of 3LO is to interact with the appropriate end-user services. In this example, we'll list the user's Gmail labels.
```javascript
exports.listlabels = (req, res) => {
  // Parse session cookie
  // Note: this presumes 'token' is the only value in the cookie
  const cookieStr = (req.headers.cookie || '').split('=')[1];
  const token = cookieStr ? JSON.parse(decodeURIComponent(cookieStr)) : null;

  // If the stored OAuth 2.0 token has expired, request a new one
  if (!token || !token.expiry_date || token.expiry_date < Date.now() + 60000) {
    return res.redirect('/oauth2init').end();
  }

  // Get Gmail labels
  oauth2Client.credentials = token;
  return new Promise((resolve, reject) => {
    gmail.users.labels.list({ auth: oauth2Client, userId: 'me' }, (err, response) => {
      if (err) {
        return reject(err);
      }
      return resolve(response.labels);
    });
  })
    .then((labels) => {
      // Respond to request
      res.set('Content-Type', 'text/html');
      res.write(`${labels.length} label(s) found:`);
      labels.forEach(label => res.write(`<br>${label.name}`));
      res.status(200).end();
    })
    .catch((err) => {
      // Handle error
      console.error(err);
      res.status(500).send('Something went wrong; check the logs.');
    });
};
```

## Complete code
Below is a copy of `index.js`, which contains all the code used in this tutorial.
```javascript
/**
 * Copyright 2018, Google, Inc.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';

const fs = require('fs');
const google = require('googleapis');
const gmail = google.gmail('v1');

const DebugAgent = require('@google-cloud/debug-agent');
DebugAgent.start();

// Configuration constants
// TODO replace these values with your own
const GCF_REGION = '[YOUR_GCF_REGION]';
const GCLOUD_PROJECT = '[YOUR_GCP_PROJECT_ID]';

// Retrieve OAuth2 config
const clientSecretJson = JSON.parse(fs.readFileSync('./client_secret.json'));
const oauth2Client = new google.auth.OAuth2(
  clientSecretJson.web.client_id,
  clientSecretJson.web.client_secret,
  `https://${GCF_REGION}-${GCLOUD_PROJECT}.cloudfunctions.net/oauth2callback`
);

/**
 * Request an OAuth 2.0 authorization code
 */
exports.oauth2init = (req, res) => {
  // Parse session cookie
  // Note: this presumes 'token' is the only value in the cookie
  const cookieStr = (req.headers.cookie || '').split('=')[1];
  const token = cookieStr ? JSON.parse(decodeURIComponent(cookieStr)) : null;

  // If the current OAuth token hasn't expired yet, go to /listlabels
  if (token && token.expiry_date && token.expiry_date >= Date.now() + 60000) {
    return res.redirect('/listlabels');
  }

  // Define OAuth2 scopes
  const scopes = [
    'https://www.googleapis.com/auth/gmail.readonly'
  ];

  // Generate + redirect to OAuth2 consent form URL
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'online',
    scope: scopes
  });
  res.redirect(authUrl);
};

/**
 * Get an access token from the authorization code and store token in a cookie
 */
exports.oauth2callback = (req, res) => {
  // Get authorization code from request
  const code = req.query.code;

  return new Promise((resolve, reject) => {
    // OAuth2: Exchange authorization code for access token
    oauth2Client.getToken(code, (err, token) => {
      if (err) {
        return reject(err);
      }
      return resolve(token);
    });
  })
    .then((token) => {
      // Respond with OAuth token stored as a cookie
      res.cookie('token', JSON.stringify(token));
      res.redirect('/listlabels');
    })
    .catch((err) => {
      // Handle error
      console.error(err);
      res.status(500).send('Something went wrong; check the logs.');
    });
};

/**
 * List the current user's Gmail labels
 */
exports.listlabels = (req, res) => {
  // Parse session cookie
  // Note: this presumes 'token' is the only value in the cookie
  const cookieStr = (req.headers.cookie || '').split('=')[1];
  const token = cookieStr ? JSON.parse(decodeURIComponent(cookieStr)) : null;

  // If the stored OAuth 2.0 access token has expired, request a new one
  if (!token || !token.expiry_date || token.expiry_date < Date.now() + 60000) {
    return res.redirect('/oauth2init').end();
  }

  // Get Gmail labels
  oauth2Client.credentials = token;
  return new Promise((resolve, reject) => {
    gmail.users.labels.list({ auth: oauth2Client, userId: 'me' }, (err, response) => {
      if (err) {
        return reject(err);
      }
      return resolve(response.labels);
    });
  })
    .then((labels) => {
      // Respond to request
      res.set('Content-Type', 'text/html');
      res.write(`${labels.length} label(s) found:`);
      labels.forEach(label => res.write(`<br>${label.name}`));
      res.status(200).end();
    })
    .catch((err) => {
      // Handle error
      console.error(err);
      res.status(500).send('Something went wrong; check the logs.');
    });
};
```

[github_repo]: https://github.com/GoogleCloudPlatform/community
[docs_setup]: https://cloud.google.com/nodejs/docs/setup
[docs_regions]: https://cloud.google.com/compute/docs/regions-zones/#available
[docs_gcp_auth]: https://cloud.google.com/docs/authentication/
[console_gmail]: https://console.cloud.google.com/start/api?id=gmail
[console_credentials]: https://console.cloud.google.com/apis/credentials/oauthclient
[console_stackdriver]: https://console.cloud.google.com/logs/viewer