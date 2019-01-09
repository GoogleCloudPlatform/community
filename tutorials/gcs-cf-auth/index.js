/**
Copyright 2018 Google

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
const cfAuth = require('./cf_auth.js');
const validator = require('validator');

/* Project variables */
// See config/default.json for more information
const DEBUG_LOGGING = config.get('logging.debug');
const VERSION_LOGGING = config.get('logging.version');

/* Helpful init stuff */
const appVersion = require('fs').statSync(__filename).mtimeMs + ' env:' + process.env.NODE_ENV;
// This log line is helpful to keep track of which version of the CF is running.
// The timestamp of index.js is logged at initial script launch as well as each
// individual execution of tokenize() and detokenize()
logVersion(`CF LAUNCHED v.${appVersion}`);


/**
 * @param {object} req - CF request object
 * @param {object} res - CF response object
 */
/* jshint ignore:start */
exports.example_auth = async (req, res) => {
  logVersion(`CF triggered at v.${appVersion}`);
  var authToken = validator.escape(req.body.auth_token);
  var projectId = req.body.project_id || projectId || process.env.GCP_PROJECT;

  if(!authToken || !validator.isAscii(authToken)) {
    return res.status(401).send('Error: A valid ASCII OAuth acess token must be provided in the param \'auth_token\'');
  }

  try {
    // Perform any pre-auth checks such as input validation here

    debug('Authenticating provided token.');

    var auths = await cfAuth.authenticateAndBuildServices(authToken); // jshint ignore:line
    if(auths === false) {
      return res.status(401).send('[-] Authentication failure');
    }

    // Perform actions with the auth object we just created here

    debug('Auth complete.');
    return res.status(200).send('[+] Authentication success');
  }
  catch(err) {
    return res.status(500).send(`Error: ${err.message}`);
  }
};
/* jshint ignore:end */

/**
 * Helpful debug function that checks for the var DEBUG_LOGGING == true before writing to console.log()
 */
function debug(...args) {
  if(DEBUG_LOGGING) console.log(...args);
}

/**
 * A handy utility function that can write the timestamp of index.js when the CF
 * is first launched and again each time it is executed. This is helpful when trying
 * to link log output of a particular run to the code version that generated it.
 * It can take several seconds for the new CF to start getting traffic even after
 * a new CF deploy is marked OK.
 */
function logVersion(...args) {
  if(VERSION_LOGGING) console.log(...args);
}
