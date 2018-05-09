'use strict';

const appendQuery = require('append-query');
const crypto = require('crypto');
const Datastore = require('@google-cloud/datastore');
const fernet = require('fernet');
const fs = require('fs');
const jwt = require('jsonwebtoken');
const path = require('path');
const pug = require('pug');

const ISSUER = 'sample-issuer';
const JWT_LIFE_SPAN = 1800 * 1000;
const CODE_LIFE_SPAN = 600 * 1000;
/*
 * Linux and macOS users: prepare a base64-encoded 256-bit random seq. with
 *
 * dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64
 *
 * Python package, cryptography, also provides methods to generate keys.
 *
 * See https://cryptography.io/en/latest/fernet/ for more information.
 *
 */
const SECRET = new fernet.Secret(
  'YHD1m3rq3K-x6RxT1MtuGzvyLz4EWIJAEkRtBRycDHA=');

const datastore = Datastore();
const fernetToken = new fernet.Token({
  secret: SECRET
});

let privateKey;
fs.readFile('private.pem', 'utf8', function (error, data) {
  if (error) {
    console.log(`An error has occurred when reading the key file: ${error}`);
  } else {
    privateKey = data;
  }
});

function handleACPKCEAuthRequest (req, res) {
  if (req.query.client_id === undefined ||
      req.query.redirect_url === undefined ||
      req.query.code_challenge === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('acpkce-enabled', '=', true);

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client/redirect URL.'));
      }
    })
    .then(() => {
      const html = pug.renderFile(path.join(__dirname, 'auth.pug'), {
        response_type: 'code',
        client_id: req.query.client_id,
        redirect_url: req.query.redirect_url,
        code_challenge: req.query.code_challenge
      });
      res.status(200).send(html);
    })
    .catch(error => {
      if (error.message === 'Invalid client/redirect URL.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': error.message
        }));
      } else {
        throw error;
      }
    });
}

function handleACAuthRequest (req, res) {
  if (req.query.client_id === undefined ||
      req.query.redirect_url === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('ac-enabled', '=', true);

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client/redirect URL.'));
      }
    })
    .then(() => {
      const html = pug.renderFile(path.join(__dirname, 'auth.pug'), {
        response_type: 'code',
        client_id: req.query.client_id,
        redirect_url: req.query.redirect_url,
        code_challenge: req.query.code_challenge
      });
      res.status(200).send(html);
    })
    .catch(error => {
      if (error.message === 'Invalid client/redirect URL.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': error.message
        }));
      } else {
        throw error;
      }
    });
}

function handleImplicitAuthRequest (req, res) {
  if (req.query.client_id === undefined ||
      req.query.redirect_url === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('implicit-enabled', '=', true);

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client/redirect URL.'));
      }
    })
    .then(() => {
      const html = pug.renderFile(path.join(__dirname, 'auth.pug'), {
        response_type: 'code',
        client_id: req.query.client_id,
        redirect_url: req.query.redirect_url,
        code_challenge: req.query.code_challenge
      });
      res.status(200).send(html);
    })
    .catch(error => {
      if (error.message === 'Invalid client/redirect URL.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': error.message
        }));
      } else {
        throw error;
      }
    });
}

exports.auth = (req, res) => {
  console.log(req.query);
  switch (req.query.response_type) {
    case ('code'):
      if (req.query.code_challenge && req.query.code_challenge_method) {
        handleACPKCEAuthRequest(req, res);
      } else if (!req.query.code_challenge &&
                 !req.query.code_challenge_method) {
        handleACAuthRequest(req, res);
      } else {
        res.status(400).send(JSON.stringify({
          'error': 'invalid_request',
          'error_description': 'Required parameters are missing in the request.'
        }));
      }
      break;

    case ('token'):
      handleImplicitAuthRequest(req, res);
      break;

    default:
      res.status(400).send(JSON.stringify({
        'error': 'invalid_request',
        'error_description': 'Grant type is invalid or missing.'
      }));
      break;
  }
};

function handleACPKCESigninRequest (req, res) {
  if (req.body.username === undefined ||
      req.body.password === undefined ||
      req.body.client_id === undefined ||
      req.body.redirect_url === undefined ||
      req.body.code_challenge === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password);

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('acpkce-enabled', '=', true);

  datastore
    .runQuery(userQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid user credentials.'));
      }
    })
    .then(() => {
      return datastore.runQuery(clientQuery);
    })
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client and/or redirect URL.'));
      }
    })
    .then(() => {
      const authorizationCode = fernetToken
        .encode(JSON.stringify({
          'client_id': req.body.client_id,
          'redirect_url': req.body.redirect_url
        }))
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');

      const exp = Date.now() + CODE_LIFE_SPAN;

      const codeKey = datastore.key(['authorization_code', authorizationCode]);
      const data = {
        'client_id': req.body.client_id,
        'redirect_url': req.body.redirect_url,
        'exp': exp,
        'code_challenge': req.body.code_challenge
      };

      return Promise.all([
        datastore.upsert({ key: codeKey, data: data }),
        Promise.resolve(authorizationCode)
      ]);
    })
    .then(results => {
      res.redirect(appendQuery(req.body.redirect_url, {
        authorization_code: results[1]
      }));
    });
}

function handleACSigninRequest (req, res) {
  if (req.body.username === undefined ||
      req.body.password === undefined ||
      req.body.client_id === undefined ||
      req.body.redirect_url === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password);

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('ac-enabled', '=', true);

  datastore
    .runQuery(userQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid user credentials.'));
      }
    })
    .then(() => {
      return datastore.runQuery(clientQuery);
    })
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client and/or redirect URL.'));
      }
    })
    .then(() => {
      const authorizationCode = fernetToken
        .encode(JSON.stringify({
          'client_id': req.body.client_id,
          'redirect_url': req.body.redirect_url
        }))
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');

      const exp = Date.now() + CODE_LIFE_SPAN;

      const key = datastore.key(['authorization_code', authorizationCode]);
      const data = {
        'client_id': req.body.client_id,
        'redirect_url': req.body.redirect_url,
        'exp': exp
      };

      return Promise.all([
        datastore.upsert({ key: key, data: data }),
        Promise.resolve(authorizationCode)
      ]);
    })
    .then(results => {
      res.redirect(appendQuery(req.body.redirect_url, {
        authorization_code: results[1]
      }));
    });
}

function handleImplictSigninRequest (req, res) {
  if (req.body.username === undefined ||
      req.body.password === undefined ||
      req.body.client_id === undefined ||
      req.body.redirect_url === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password);

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('implicit-enabled', '=', true);

  datastore
    .runQuery(userQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid user credentials.'));
      }
    })
    .then(() => {
      return datastore.runQuery(clientQuery);
    })
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client and/or redirect URL.'));
      }
    })
    .then(() => {
      const token = jwt.sign({}, privateKey, {
        algorithm: 'RS256',
        expiresIn: JWT_LIFE_SPAN,
        issuer: ISSUER
      });
      res.redirect(appendQuery(req.body.redirect_url, {
        access_token: token,
        token_type: 'JWT',
        expires_in: JWT_LIFE_SPAN
      }));
    });
}

exports.signin = (req, res) => {
  switch (req.body.response_type) {
    case ('code'):
      if (!req.body.code_challenge) {
        handleACSigninRequest(req, res);
      } else {
        handleACPKCESigninRequest(req, res);
      }
      break;

    case ('token'):
      handleImplictSigninRequest(req, res);
      break;

    default:
      res.status(400).send(JSON.stringify({
        'error': 'invalid_request',
        'error_description': 'Grant type is invalid or missing.'
      }));
      break;
  }
};

function handleROPCTokenRequest (req, res) {
  if (req.body.username === undefined ||
      req.body.password === undefined ||
      req.body.client_id === undefined ||
      req.body.client_secret === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('client-secret', '=', req.body.client_secret)
    .filter('ropc-enabled', '=', true);

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password);

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid client credentials.'));
      }
    })
    .then(() => datastore.runQuery(userQuery))
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject(new Error('Invalid user credentials.'));
      }
    })
    .then(() => {
      const token = jwt.sign({}, privateKey, {
        algorithm: 'RS256',
        expiresIn: JWT_LIFE_SPAN,
        issuer: ISSUER
      });
      res.status(200).send(JSON.stringify({
        access_token: token,
        token_type: 'JWT',
        expires_in: JWT_LIFE_SPAN
      }));
    })
    .catch(error => {
      if (error.message === 'Invalid client credentials.' ||
          error.message === 'Invalid user credentials.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': error.message
        }));
      } else {
        throw error;
      }
    });
}

function verifyAuthorizationCode (authorizationCode, clientId, redirectUrl,
                                  codeVerifier = undefined) {
  const transaction = datastore.transaction();
  const key = datastore.key(['authorization_code', authorizationCode]);

  return transaction
    .run()
    .then(() => transaction.get(key))
    .then(result => {
      const entry = result[0];
      if (entry === undefined) {
        return Promise.reject(new Error('Invalid authorization code.'));
      }

      if (entry.client_id !== clientId) {
        return Promise.reject(new Error('Client ID does not match the record.'));
      }

      if (entry.redirect_url !== redirectUrl) {
        return Promise.reject(new Error('Redirect URL does not match the record.'));
      }

      if (entry.exp <= Date.now()) {
        return Promise.reject(new Error('Authorization code expired.'));
      }

      if (codeVerifier !== undefined &&
          entry.code_challenge !== undefined) {
        let codeVerifierBuffer = Buffer.from(codeVerifier);
        let codeChallenge = crypto
                              .createHash('sha256')
                              .update(codeVerifierBuffer)
                              .digest()
                              .toString('base64')
                              .replace(/\+/g, '-')
                              .replace(/\//g, '_')
                              .replace(/=/g, '');
        if (codeChallenge !== entry.code_challenge) {
          return Promise.reject(new Error('Code verifier does not match code challenge.'));
        }
      } else if (codeVerifier === undefined ||
                 entry.code_challenge === undefined) {
        // Pass
      } else {
        return Promise.reject(
          new Error('Code challenge or code verifier does not exist.'));
      }

      return transaction.delete(key);
    })
    .then(() => transaction.commit())
    .catch(error => {
      transaction.rollback();
      throw error;
    });
}

function handleACTokenRequest (req, res) {
  if (req.body.client_id === undefined ||
      req.body.client_secret === undefined ||
      req.body.authorization_code === undefined ||
      req.body.redirect_url === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  const clientQuery = datastore
      .createQuery('client')
      .filter('client-id', '=', req.body.client_id)
      .filter('client-secret', '=', req.body.client_secret)
      .filter('ac-enabled', '=', true);

  datastore
    .runQuery(clientQuery)
    .then(clientQueryResult => {
      if (clientQueryResult[0].length === 0) {
        return Promise.reject(new Error('Invalid client credentials.'));
      }
    })
    .then(() => {
      return verifyAuthorizationCode(req.body.authorization_code,
        req.body.client_id, req.body.redirect_url);
    })
    .then(() => {
      const token = jwt.sign({}, privateKey, {
        algorithm: 'RS256',
        expiresIn: JWT_LIFE_SPAN,
        issuer: ISSUER
      });
      res.status(200).send(JSON.stringify({
        access_token: token,
        token_type: 'JWT',
        expires_in: JWT_LIFE_SPAN
      }));
    })
    .catch(error => {
      if (error.message === 'Invalid client credentials.' ||
          error.message === 'Invalid authorization code.' ||
          error.message === 'Client ID does not match the record.' ||
          error.message === 'Redirect URL does not match the record.' ||
          error.message === 'Authorization code expired.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': error.message
        }));
      } else {
        throw error;
      }
    });
}

function handleACPKCETokenRequest (req, res) {
  if (req.body.client_id === undefined ||
      req.body.authorization_code === undefined ||
      req.body.redirect_url === undefined ||
      req.body.code_verifier === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }));
  }

  verifyAuthorizationCode(req.body.authorization_code, req.body.client_id,
    req.body.redirect_url, req.body.code_verifier)
    .then(() => {
      const token = jwt.sign({}, privateKey, {
        algorithm: 'RS256',
        expiresIn: JWT_LIFE_SPAN,
        issuer: ISSUER
      });
      res.status(200).send(JSON.stringify({
        access_token: token,
        token_type: 'JWT',
        expires_in: JWT_LIFE_SPAN
      }));
    })
    .catch(error => {
      if (error.message === 'Invalid authorization code.' ||
          error.message === 'Client ID does not match the record.' ||
          error.message === 'Redirect URL does not match the record.' ||
          error.message === 'Authorization code expired.' ||
          error.message === 'Code verifier does not match code challenge.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': error.message
        }));
      } else if (error.msg === 'Code challenge does not exist.') {
        res.status(400).send(JSON.stringify({
          'error': 'invalid_request',
          'error_description': error.message
        }));
      } else {
        throw error;
      }
    });
}

function handleCCTokenRequest (req, res) {
  if (req.body.client_id === undefined ||
      req.body.client_secret === undefined) {
    return res.status(400).send(JSON.stringify({
      error: 'invalid_request',
      error_description: 'Required parameters are missing in the request.'
    }));
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('client-secret', '=', req.body.client_secret)
    .filter('cc-enabled', '=', true);

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return res.status(400).send(JSON.stringify({
          error: 'access_denied',
          error_description: 'Invalid client credentials.'
        }));
      } else {
        const token = jwt.sign({}, privateKey, {
          algorithm: 'RS256',
          expiresIn: JWT_LIFE_SPAN,
          issuer: ISSUER
        });
        res.status(200).send(JSON.stringify({
          access_token: token,
          token_type: 'JWT',
          expires_in: JWT_LIFE_SPAN
        }));
      }
    });
}

exports.token = (req, res) => {
  switch (req.body.grant_type) {
    case 'password':
      handleROPCTokenRequest(req, res);
      break;

    case 'authorization_code':
      if (req.body.client_secret && !req.body.code_verifier) {
        handleACTokenRequest(req, res);
        break;
      }
      if (req.body.code_verifier) {
        handleACPKCETokenRequest(req, res);
        break;
      }
      res.status(400).send(JSON.stringify({
        'error': 'invalid_request',
        'error_description': 'Client secret and code verifier are exclusive' +
                             'to each other.'
      }));
      break;

    case 'client_credentials':
      handleCCTokenRequest(req, res);
      break;

    default:
      res.status(400).send(JSON.stringify({
        'error': 'invalid_request',
        'error_description': 'Grant type is invalid or missing.'
      }));
      break;
  }
};
