/**
Copyright 2018 Ian Maddox

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

'use strict';
/* Required libraries and supporting vars */
process.env.NODE_CONFIG_DIR = process.env.NODE_CONFIG_DIR || __dirname + '/config/';
const config = require('config');
const {google} = require('googleapis');
const {Storage} = require('@google-cloud/storage');
const validator = require('validator');
const authServices = [];

/* Project variables */
// See config/default.json for more information
var PROJECT_ID = config.get("general.project_id");
const AUTH_BUCKET = config.get("auth.test_bucket");
const DEBUG_LOGGING = config.get("logging.debug");
const TEST_PERMISSIONS = config.get("auth.test_permissions");

/**
 * Authenticate against the GCS API. If we already have clients  instantiated for
 * the given auth_token, return them instead of creating new ones.
 *
 * @param {string} authToken - The OAuth2.0 authentication token given to the CF
 * @return Array [ds:{Datastore}, kms:{KMS}] - A cached or newly created DS and KMS object pair
 */
async function authenticateAndBuildServices(authToken) {
  try {

    if(!authToken || !validator.isAscii(authToken)) {
      debug('Invalid token provided to' + __filename);
      return false;
    }

    debug(`authServices with token '${authToken}'`);
    if(authServices[authToken] !== undefined) {
      debug("Using cached auth objects");
      return authServices[authToken];
    }
    debug("Generating new auth object(s)");
    const oauth2client = new google.auth.OAuth2();
    const tokenInfo = await oauth2client.getTokenInfo(authToken);

    debug("token info:");
    debug(tokenInfo);
    let now = Date.now();
    debug('exp:', tokenInfo.expiry_date, 'now:', Date.now(), 'remainder:', (tokenInfo.expiry_date - Date.now()));
    if(!tokenInfo.expiry_date || tokenInfo.expiry_date < now) {
      throw new Error('Token did not validate: ' + authToken);
    }

    // Create a cache of auth objects per token.
    // This array contains a collection of service objects authenticated by the given
    // token. By default, only GCS is used, but two more example blocks authenticating
    // against Datastore and KMS are commented out below. This method can be used
    // to create auth objects for any number of services that the account behind the
    // token is authorized to access.

    authServices[authToken] = {};

    // Authentication against GCS
    oauth2client.setCredentials({token:authToken, res: null});
    let dsOptions = {
      access_token: oauth2client,
      projectId: PROJECT_ID
    };
    authServices[authToken].gcs = new Storage(dsOptions);

    let testfail = false;
    let results = await authServices[authToken].gcs.bucket(AUTH_BUCKET).iam.testPermissions(TEST_PERMISSIONS);
    TEST_PERMISSIONS.forEach((perm) => {
      if(results[0][perm] !== true) {
        debug(`Permission ${perm} is not set`);
        testfail = true;
      }
    });
    if(testfail === true) {
      debug("Authentication failure");
      return false;
    }

    debug("GCS auth success");

    // Authenticate against other services or perform other post-auth actions here
    return authServices[authToken];
  }
  catch(err) {
    debug("GCS auth failure: " + err.message);
    return false;
  };

  // // Example authentication against Datastore
  // oauth2client.setCredentials({token:authToken, res: null});
  // let dsOptions = {
  //   access_token: oauth2client,
  //   projectId: PROJECT_ID
  // };
  // authServices[authToken].ds = Datastore(dsOptions);

  // // Example authentication against KMS
  // oauth2client.setCredentials({access_token:authToken, res: null});
  // let kmsOptions = {
  //   auth: oauth2client,
  //   version: 'v1'
  // };
  // authServices[authToken].kms = google.cloudkms(kmsOptions);
}


/**
 * Helpful debug function that checks for the var DEBUG_LOGGING == true before writing to console.log()
 */
function debug(...args) {
  if(DEBUG_LOGGING) console.log(...args);
}

exports.authenticateAndBuildServices = authenticateAndBuildServices;
