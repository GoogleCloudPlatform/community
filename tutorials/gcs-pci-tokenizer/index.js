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
const crypto = require('crypto');
const Datastore = require('@google-cloud/datastore');
const authServices = [];

/* Project variables */
// See config/default.json for more information
var projectId = config.get("general.project_id");
const DEBUG_LOGGING = config.get("logging.debug");
const VERSION_LOGGING = config.get("logging.version");
const keyRingLocation = config.get("kms.key_ring_location");
const keyRingId = config.get("kms.key_ring_id");
const cryptoKeyId = config.get("kms.crypto_key_id");
const dsNamespace = config.get("datastore.namespace");
const kind = config.get("datastore.kind");

/* Helpful init stuff */
const appVersion = require('fs').statSync(__filename).mtimeMs + " env:" + process.env.NODE_ENV;
// This log line is helpful to keep track of which version of the CF is running.
// The timestamp of index.js is logged at initial script launch as well as each
// individual execution of tokenize() and detokenize()
logVersion(`CF LAUNCHED v.${appVersion}`);


/**
 * Accepts the following params as an HTTP POST:
 *  auth_token - OAuth 2.0 authentication token
 *  project_id - The project ID associated with the auth_token
 *  cc         - 14-16 digit credit card number
 *  mm         - 2 digit month
 *  yyyy       - 4 digit year
 *  user_id     - arbitrary user ID string (optional)
 *
 * Returns an alphanumeric string which can be used as a PCI DSS compliant token
 * in-place of a credit card number in out-of-scope data storage environments.
 *
 * @param {object} req - CF request object
 * @param {object} res - CF response object
 */
exports.tokenize = async (req, res) => {
  logVersion(`tokenizing with CF v.${appVersion}`);
  // The value contains a JSON document representing the entity we want to save
  var cc = req.body.cc;
  var mm = req.body.mm;
  var yyyy = req.body.yyyy;
  var userid = req.body.user_id;
  var authToken = req.body.auth_token;
  var projectId = req.body.project_id || projectId || process.env.GCP_PROJECT;

  if(!authToken) {
    return res.status(401).send("An OAuth acess token must be provided in the param 'auth_token'");
  }

  if (!cc || cc.length < 14 || cc.length > 16) {
    return res.status(500).send('Invalid input for CC');
  }

  if(!mm || mm < 0 || mm > 12) {
    return res.status(500).send('Invalid input for mm');
  }

  if(!yyyy || yyyy < 2010 || yyyy > 3000) {
    return res.status(500).send('Invalid input for yyyy');
  }
  try {
    var auths = await authenticateAndBuildServices(authToken);
    var datastore = auths.ds;
    var cloudkms = auths.kms;

    const request = {
      name: `projects/${projectId}/locations/${keyRingLocation}/keyRings/${keyRingId}/cryptoKeys/${cryptoKeyId}`,
      resource: {
        plaintext: cc.toString('base64')
      }
    };

    // Encrypts the file using the specified crypto key
    cloudkms.projects.locations.keyRings.cryptoKeys.encrypt(request, (err, response) => {
      if (err) {
        console.log(err);
        res.status(401).send(err.message);
        return;
      }

      const buf = new Buffer.from(response.data.ciphertext);
      var cipher = buf.toString();
      // Create the CC token by hashing the encrypted CC along with some other seed data
      var authToken = crypto.createHash('sha256').update(userid + "::" + yyyy + "::" + mm + "::" + cipher).digest("hex");
      const entity = {
        key: {kind: kind, namespace: dsNamespace},
        data: {
          userid: userid,
          token: authToken,
          mm: mm,
          yyyy: yyyy,
          cipher: cipher
        }
      };

      datastore.save(entity)
        .then(() => {
          res.status(200).send(authToken);
          return true;
        })
        .catch((err) => {
          console.error(err);
          res.status(500).send(`Error saving to Datastore: ${err.message}`);
          return false;
        });
    });
  }
  catch(err) {
    res.status(500).send(`Error during tokenization: ${err.message}. Check for invalid auth_token`);
    return false;
  }
}


/**
 * Accepts the following params as an HTTP POST:
 *  auth_token - OAuth 2.0 authentication token
 *  project_id - The project ID associated with the auth_token
 *  cc_token   - The tokenized CC number
 *
 * If the auth_token was valid, this returns a JSON object containing the
 * sensitive payment card data that was stored under the given token.
 *
 * @param {object} req - CF request object
 * @param {object} res - CF response object
 */
exports.detokenize = async (req, res) => {
  logVersion(`detokenizing ver ${appVersion}`);
  var ccToken = req.body.cc_token;
  var authToken = req.body.auth_token;
  var projectId = req.body.project_id || projectId || process.env.GCP_PROJECT;

  if(!authToken) {
    res.status(401).send("An OAuth acess token must be provided in the param 'auth_token'");
    return false;
  }

  if (!ccToken || ccToken.length < 16) {
    throw new Error('Invalid input for token: ' + ccToken);
  }

  try {
    var auths = await authenticateAndBuildServices(authToken);
    var datastore = auths.ds;
    var cloudkms = auths.kms;

    const query = datastore
      .createQuery(dsNamespace, kind)
      .filter('token', '=', ccToken);

      datastore.runQuery(query)
      .then((rs) => {
        var row = rs[0][0];

        if(!row || row === undefined) {
          res.status(404).send("Record not found");
          return false;
        }
        var cipher = row.cipher;
        var buff = new Buffer.from(cipher);
        let cipherB64 = buff.toString('base64');
        var payload = {
          cc: '',
          mm: row.mm,
          yyyy: row.yyyy,
          userid: row.userid
        };

      const request = {
        name: `projects/${projectId}/locations/${keyRingLocation}/keyRings/${keyRingId}/cryptoKeys/${cryptoKeyId}`,
        resource: {
          ciphertext: cipher
        }
      };
      cloudkms.projects.locations.keyRings.cryptoKeys.decrypt(request, (err, response) => {
        if (err) {
          console.log(err);
          res.status(401).send(err.message);
        }

        payload.cc = response.data.plaintext;
        res.status(200).send(payload);
        return true;
      });
    })
    .catch((err) => {
      console.log(err);
      res.status(500).send(`Datastore query error: ${err.message}`);
      return false;
    })
  }
  catch(e) {
    res.status(500).send(`Detokenization error: ${err.message}`);
    return false;
  }
};


/**
 * Authenticate against the Datastore and KMS APIs. If we already have clients
 * instantiated for the given auth_token, return them instead of creating new ones.
 *
 * @param {string} authToken - The OAuth2.0 authentication token given to the CF
 * @return Array [ds:{Datastore}, kms:{KMS}] - A cached or newly created DS and KMS object pair
 */
async function authenticateAndBuildServices(authToken) {
  debug(`authServices with token '${authToken}'`);
  if(authServices[authToken] !== undefined) {
    debug("Using cached KMS/DS");
    return authServices[authToken];
  }
  debug("Generating new KMS/DS");
  const oauth2client = new google.auth.OAuth2();
  const tokenInfo = await oauth2client.getTokenInfo(authToken);

  debug("token info:");
  debug(tokenInfo);
  let now = Date.now();
  debug('exp:', tokenInfo.expiry_date, 'now:', Date.now(), 'remainder:', (tokenInfo.expiry_date - Date.now()));
  if(!tokenInfo.expiry_date || tokenInfo.expiry_date < now) {
    throw new Error('Token did not validate: ' + authToken);
  }

  authServices[authToken] = {};

  oauth2client.setCredentials({token:authToken, res: null});
  let dsOptions = {
    access_token: oauth2client,
    projectId: projectId
  };
  authServices[authToken].ds = Datastore(dsOptions);

  oauth2client.setCredentials({access_token:authToken, res: null});
  let kmsOptions = {
    auth: oauth2client,
    version: 'v1'
  };
  authServices[authToken].kms = google.cloudkms(kmsOptions);
  return authServices[authToken];
}


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
 * It can take up to 45 seconds for the new CF to start getting traffic even after
 * a new CF deploy is marked OK.
 */
function logVersion(...args) {
  if(VERSION_LOGGING) console.log(...args);
}
