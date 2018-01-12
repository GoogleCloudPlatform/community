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
