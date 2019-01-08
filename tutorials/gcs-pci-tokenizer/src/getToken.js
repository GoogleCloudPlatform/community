/**
 * github ianmaddox/gcs-cf-tokenizer
 * Utility script to generate OAuth 2.0 authentication tokens
 * See ../README.md for license and more info
 *
 * USAGE:
 * This tool is designed to be executed within the the GCS Cloud Shell or a PChell that is configured to use NodeJS
 * terminal that is configured to use NodeJS.
 * 1) To initialize the environment run "npm install"
 * 2) Download your service account credential .json file and assign the pathand filename to the environment variable GOOGLE_APPLICATION_CREDENTIALS
 *    and filename to the environment variable GOOGLE_APPLICATION_CREDENTIALS.
 *    Linux/Mac: "export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'"
 * 3) If not running in Cloud Shell, define the GCP project in the environment variable GOOGLE_CLOUD_PROJECT
 *    variable GOOGLE_CLOUD_PROJECT.
 *    Linux/Mac: "export GOOGLE_CLOUD_PROJECT='YOUR_PROJECT'"
 * 4) Run the script
 *    "node getToken.js"
 *    The auth_token will be printed to stdout
 */
"use strict";
const {google} = require('googleapis');

async function main () {
  // This method looks for the GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS
  // environment variables.
  let authfile = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  if (!require('fs').existsSync(authfile)) {
    console.log(`ERROR: Auth file ${authfile} does not exist! Please set env var $GOOGLE_APPLICATION_CREDENTIALS`);
    return false;
  }

  const auth = await google.auth.getClient({
    // Scopes can be specified either as an array or as a single, space-delimited string.
    scopes: ['https://www.googleapis.com/auth/cloud-platform',
      'https://www.googleapis.com/auth/datastore',
      'https://www.googleapis.com/auth/cloudkms']
  });
  return auth.getAccessToken();
}

module.exports.getAccessToken = main;

(async () => {
  let tokens = await main().catch(console.error);
  // console.log(tokens);
  console.log(tokens.token);
})();
