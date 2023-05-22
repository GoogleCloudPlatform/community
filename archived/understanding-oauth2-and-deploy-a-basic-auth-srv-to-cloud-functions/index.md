---
title: Understanding OAuth2 and deploying a basic authorization service to Cloud Functions
description: Learn how to deploy a basic OAuth2 authorization service to Cloud Functions.
author: michaelawyu
tags: OAuth 2.0, Node.js, Cloud Functions, Cloud Datastore
date_published: 2018-06-15
---

Chen Yu | | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains the basics of OAuth 2.0 and how to deploy an OAuth2 authorization service in [Node.js](https://nodejs.org/en/) to [Google Cloud Functions](https://cloud.google.com/functions/). For a general overview of OAuth 2.0, see [Understanding OAuth2 and Building a Basic Authorization Server of Your Own: A Beginner’s Guide](https://medium.com/@ratrosy/understanding-oauth2-and-building-a-basic-authorization-server-of-your-own-a-beginners-guide-cf7451a16f66).

Cloud Functions is an event-driven serverless compute platform. It offers one of the simplest ways to run code in the cloud and provides developers with automatic scaling, high availability and fault tolerance. As a part of the computing solutions on Google Cloud, your Cloud Functions can easily integrate with other Google Cloud services.

## Objectives

* Understand the basics of OAuth 2 and the architecture of the project
* Deploy the code to Cloud Functions

## Costs

This tutorial uses billable components of Google Cloud, including

* Cloud Functions
* Datastore

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage. Depending on the actual usage, you might be eligible for [Google Cloud Free Tier](https://cloud.google.com/free/).

## Before you begin

1. Select a project from [Cloud Console](https://console.cloud.google.com/). If you have never used Google Cloud before, sign up or log in with your existing Google account, then follow the on-screen instructions to start using Google Cloud.

1. [Enable billing](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project) for your account.

1. [Enable the Cloud Functions API](https://console.cloud.google.com/flows/enableapi?apiid=cloudfunctions&redirect=https://cloud.google.com/functions/quickstart).

1. [Install the Cloud SDK](https://cloud.google.com/sdk/).

1. Windows Developers Only: Install [cURL](https://curl.haxx.se/download.html).

1. Create the following entities in Datastore:

    a. Go to the [Cloud Datastore Entities Page](https://console.cloud.google.com/datastore) in the Cloud Console.

    b. Click **Create Entity**. Datastore may ask you to pick a location to store your data; select one of the locations and click **Next**.

    c. Type `user` for **Kind**.

    d. Click **Add Property**.

    e. Add a property `username` of the `String` type with the value `sample-user`. Click **Done**.

    f. Add a property `password` of the `String` type with the value `sample-password`. Click **Done**.

    g. Click **Create**.

    h. Repeat the steps above and create **5** `client` kind entities, with the following properties:

    | Property Name      | Property Type | Property Value           |
    |--------------------|---------------|--------------------------|
    | `client-id`        | `String`      | `sample-implicit-client` |
    | `implicit-enabled` | `Boolean`     | `true`                   |
    | `redirect-url`     | `String`      | `https://www.google.com` |

    | Property Name   | Property Type | Property Value         |
    |-----------------|---------------|------------------------|
    | `client-id`     | `String`      | `sample-ropc-client`   |
    | `ropc-enabled`  | `Boolean`     | `true`                 |
    | `client-secret` | `String`      | `sample-client-secret` |

    | Property Name   | Property Type | Property Value           |
    |-----------------|---------------|--------------------------|
    | `client-id`     | `String`      | `sample-ropc-client`     |
    | `ac-enabled`    | `Boolean`     | `true`                   |
    | `redirect-url`  | `String`      | `https://www.google.com` |

    | Property Name     | Property Type | Property Value          |
    |-------------------|---------------|-------------------------|
    | `client-id`       | `String`      | `sample-acpkce-client`  |
    | `acpkce-enabled`  | `Boolean`     | `true`                  |
    | `client-secret`   | `String`      | `https://www.google.com`|

    | Property Name   | Property Type | Property Value         |
    |-----------------|---------------|------------------------|
    | `client-id`     | `String`      | `sample-cc-client`     |
    | `cc-enabled`    | `Boolean`     | `true`                 |
    | `client-secret` | `String`      | `sample-client-secret` |

## Concepts

### OAuth 2.0

OAuth 2.0 ([RFC 6749](https://tools.ietf.org/html/rfc6749)) is a widely used authorization framework enabling applications to access resources in all kinds of services. More specifically, OAuth 2.0 allows arbitrary **clients** (for example, a highly trusted first-party mobile app or a less trusted third-party web app) to access user’s (**resource owner**’s) resources on **resource servers** via **authorization servers** in a secure, reliable, and efficient manner.

### Authorization flows

OAuth 2.0 specification defines 4 types of authorization flows:

* Authorization Code
* Resource Owner Password Credentials
* Implicit
* Client Credentials

**Implicit** and **Client Credentials** are flows typically reserved for special types of clients:


| Client Type                                                                                                   | Flow               |
|---------------------------------------------------------------------------------------------------------------|--------------------|
| Single-page Javascript Web Applications (for example, [Google Fonts](https://fonts.google.com/))              | Implicit           |
| Non-interactive programs for machine-to-machine communications, such as background services and daemons | Client Credentials |

As for other clients, depending on their trustworthiness, they can use the following flows:

| Client Type         | Flow               |
|---------------------|--------------------|
| Highly trusted apps | Implicit           |
| Less trusted apps   | Client Credentials |

This tutorial deploys a basic authorization server supporting all of the four flows; you can, however, tailor the code and drop the support for some of them based on your use case.

#### Authorization code

![AC](https://storage.googleapis.com/gcp-community/tutorials/understanding-oauth2-and-deploy-a-basic-auth-srv-to-cloud-functions/ac.png)

The Authorization Code flow includes the following steps:

1. The **client** prepares a link to the **authorization server** and opens the link for user in a **user agent** (browser). The link includes information that allows the authorization server to identify and respond to the client.
1. User enters their credentials on the new page.
1. Credentials are sent to **authorization server** via the **user agent** (browser).
1. The **authorization server** validates the credentials and redirects user back to the client with an authorization code.
1. The client talks with the **authorization server**, confirms its identify and exchanges the authorization code for an access token and optionally a refresh token.
1. The client uses the access token to access resources on the **resource server**.

Note that due to security concerns, even though both mobile app clients and web app clients can use the authorization code flow, their approaches to identify themselves in the flow are different. Web app clients use client IDs and client secrets, while **mobile app clients need to adopt the [Proof Key for Code Exchange (PKCE)](https://tools.ietf.org/html/rfc7636) technique and utilize code challenges and code verifiers**.

PKCE specification requires client generate a code verifier first, then prepare a code challenge based on the code verifier. Usually, code verifier is a cryptographically strong random long string (43-128 characters) and code challenge should be its SHA-256 hash. Both should be Base64URL encoded. Client first sends code challenge to the authorization server; after the authorization code is issued, client uses code verifier together with authorization code to request access token from authorization server. The authorization server then verifies the code challenge using the code verifier and decides if an access token can be granted.

Authorization Code flow requires that clients be able to interact with a user agent (browser) in the environment.

#### Resource Owner Password Credentials

![ROPC](https://storage.googleapis.com/gcp-community/tutorials/understanding-oauth2-and-deploy-a-basic-auth-srv-to-cloud-functions/ropc.png)

The Resource Owner Password Credentials flow includes the following steps:

1. The **client** prompts user to enter their credentials (for instance, a username/password combination).
1. The **client** sends the credentials and its own identification to the **authorization server**. The **authorization server** validates the information, then returns an access token and optionally a refresh token.
1. The **client** uses the access token to access resources on the **resource server**.

Resource Owner Password Credentials flow requires that clients be highly trustworthy. In most cases, the client should be a first-party app.

#### Implicit

Implicit flow, as said earlier, is designed for single-page Javascript apps. This flow is vastly similar to the Authorization Code flow, except for the part involving authorization code. Due to security concerns, in this flow the client no longer receives an authorization code from the authorization server; instead, after the user agent successfully transfers credentials, the authorization server returns access tokens directly to the client. Refresh tokens are not allowed in the Implicit flow.

![Implicit](https://storage.googleapis.com/gcp-community/tutorials/understanding-oauth2-and-deploy-a-basic-auth-srv-to-cloud-functions/im.png)

#### Client Credentials

Client Credentials flow, on the other hand, is closer to the Resource Owner Password Credentials flow. Clients in this flow use client IDs and secrets to identify themselves, and exchange them for access tokens with the authorization server. You should not use refresh tokens in this flow either.

![CC](https://storage.googleapis.com/gcp-community/tutorials/understanding-oauth2-and-deploy-a-basic-auth-srv-to-cloud-functions/cc.png)

### JWT

Tokens play an important part in OAuth 2.0. There are two types of tokens: access tokens and refresh tokens. Anyone with a valid access token can access protected resources; usually it is short-lived so that even if there is a security breach and the access token is leaked, the damage can be quickly controlled. When an access token expires, developers can use an optional refresh token to request a new access token without having to ask the user to enter their credentials again.

It is up to developers themselves to choose the format of token for their OAuth 2.0 authorization service. This tutorial uses [JWT](https://tools.ietf.org/html/rfc7519) (JSON Web Token), a self-contained format allowing servers to validate tokens without having to inquire a data source.

A JWT includes three parts:

* A header describing the type of the token and the hashing algorithm it uses
* A payload containing the data
* A signature for verifying the token

You can use many hashing algorithms with JWT and the payload offers a variety of pre-defined fields (also known as [registered claim names](https://tools.ietf.org/html/rfc7519#section-4.1)). This Beginner’s Guide uses the [RS256](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) (RSA Signature with SHA-256) algorithm and specifies two registered claims in the payload: `exp` (when does the token expire), and `iss` (who issues the token). Aside from the supported claims, you can also define your own claims in the payload, such as the scope of the token.

Every time a JWT arrives at a server, the system first parses the JWT, and verifies if the algorithm specified in the header is supported; then it checks the signature to make sure that the JWT is valid, and at last, confirms that registered claims (if exist) are valid. In the case of this guide, it means making sure that the JWT hasn’t expired (`exp`), and comes from an expected origin (`iss`). Custom claims, such as scopes, can be extracted from the token and manually validated.

### Client registration

OAuth 2.0 requires that clients register with the authorization server beforehand. The registration process is not considered as a part of the authorization flow and developers can implement it as they see fit. Additionally, your OAuth 2.0 authorization service must be able to verify the identity of clients. This tutorial uses client IDs and client secrets for client authentication.

## Understanding the architecture

![Architecture](https://storage.googleapis.com/gcp-community/tutorials/understanding-oauth2-and-deploy-a-basic-auth-srv-to-cloud-functions/oauth_cf.png)

This tutorial deploys 3 Cloud Functions. The `token` function is responsible for issuing access tokens while the `auth` function and the `signin` function work together to grant authorization codes. More specifically,

* Clients in the Resource Owner Password Credentials flow exchange user credentials for access token with the `token` function
* Clients in the Authorization Code flow first request an authorization code from function `auth` and `signin`, then exchange it for access token with the `token` function
* Clients in the Implicit flow directly request access token from function `auth` and `signin`
* Clients in the Client Credentials flow exchange client credentials for access token with the `token` function

## Downloading the code

Download the code [here](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/understanding-oauth2-and-deploy-a-basic-auth-srv-to-cloud-functions/code).

The sample includes the following files:

| File         | Notes                                                                                                  |
|--------------|--------------------------------------------------------------------------------------------------------|
| auth.pug     | A [pug](https://github.com/pugjs/pug) HTML template for preparing the access request page.             |
| function.js  | Functions to deploy.                                                                                   |
| package.json | [Project metadata](https://docs.npmjs.com/files/package.json).                                         |
| private.pem  | A private key for generating access tokens. **You should replace this key file with one of your own**. |
| public.pem   | A public key for verifying access tokens. **You should replace this key file with one of your own**.   |

## Deploying the code

Deploy the functions using the following commands. It may take a few minutes to finish.

```
gcloud beta functions deploy token --trigger-http
gcloud beta functions deploy auth --trigger-http
gcloud beta functions deploy signin --trigger-http
```

Your functions are available at

```
https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/token
https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/auth
https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/signin
```

Replace `[GCP_REGION]` and `[PROJECT_ID]` with values of your own. Your function addresses are also available in the output of the `gcloud beta functions deploy` command.

You can always view the details of deployed functions with the [Cloud Console](https://console.cloud.google.com/functions).

## Testing the code

### Authorization code

1. Open your browser and visit

    `https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/auth?response_type=code&client_id=sample-ac-client&redirect_url=https://www.google.com`

    Replace `[GCP_REGION]` and `[PROJECT_ID]` with values of your own. Note that parameters `response_type`, `client_id`, and `redirect_url` are added to the address.

2. Sign in with `sample-username` and `sample-password`. You will be redirected to google.com. The address should look like:

    `https://www.google.com/?authorization_code=[YOUR_AUTHORIZATION_CODE]`

    Write down the returned authorization code.

3. Run command

    `curl -d "grant_type=authorization_code&client_id=sample-ac-client&client_secret=sample-client-secret&authorization_code=[AUTHORIZATION_CODE]&redirect_url=https://www.google.com" -X POST 'https://us-central1-testbed-195403.cloudfunctions.net/token'`

    Replace `[AUTHORIZATION_CODE]` with values of your own. Note that this request includes parameters `grant_type`, `client_id`, `client_secret`, `authorization_code` and `redirect_url`.

    The output should like:

    `{"access_token":"[YOUR_ACCESS_TOKEN]","token_type":"JWT","expires_in":1800000}`

    The `access_token` attribute in the returned JSON file is the issued access token. 

### Authorization code (PKCE)

1. Generate a code verifier and its code challenge. Open the node interactive shell (`node`) and run the following code:

    ```js
    // You might need to install package crypto with npm i -g crypto first
    const crypto = require('crypto');
    var code_verifier = crypto.randomBytes(64)
                         .toString('base64')
                         .replace(/\+/g, '-')
                         .replace(/\//g, '_')
                         .replace(/=/g, '');
    var code_challenge = crypto.createHash('sha256')
                         .update(code_verifier)
                         .digest()
                         .toString('base64')
                         .replace(/\+/g, '-')
                         .replace(/\//g, '_')
                         .replace(/=/g, '');
    ```

    Write down the values of code_verifier and code_challenge.

2. Open your browser and visit
   
    `https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/auth?response_type=code&client_id=sample-acpkce-client&redirect_url=https://www.google.com&code_challenge=[CODE_CHALLENGE]&code_challenge_method=S256`

    Replace `[GCP_REGION]`, `[PROJECT_ID]` and `[CODE_CHALLENGE]` with values of your own. Note that parameters `response_type`, `client_id`, `redirect_url`, `code_challenge` and `code_verifier` are added to the address.

3. Sign in with sample-username and sample-password. You will be redirected to `google.com`. The address should look like:

    `https://www.google.com/?authorization_code=[YOUR_AUTHORIZATION_CODE]`

    Write down the returned authorization code.

4. Run command

    `curl -d "grant_type=authorization_code&client_id=sample-acpkce-clientauthorization_code=[AUTHORIZATION_CODE]&code_verfier=[CODE_VERIFIER]&redirect_url=https://www.google.com" -X POST 'https://us-central1-testbed-195403.cloudfunctions.net/token'`

    Replace `[AUTHORIZATION_CODE]` and `[CODE_VERIFIER]` with values of your own. Note that this request includes parameters `grant_type`, `client_id`, `code_verifier`, `authorization_code` and `redirect_url`.

    The output should like:

    `{"access_token":"[YOUR_ACCESS_TOKEN]","token_type":"JWT","expires_in":1800000}`

    The `access_token` attribute in the returned JSON file is the issued access token. 

### Implicit

1. Open your browser and visit

    `https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/auth?response_type=token&client_id=sample-implicit-client&redirect_url=https://www.google.com`

    Replace `[GCP_REGION]` and `[PROJECT_ID]` with values of your own. Note that parameters `response_type`, `client_id`, and `redirect_url` are added to the address.

2. Sign in with sample-username and sample-password. You will be redirected to google.com. The address should look like:

    `https://www.google.com/?access_token=[YOUR_ACCESS_TOKEN]&token_type=JWT&expires_in=1800000`

    The value of `access_token` is the issued access token.

### Resource Owner Password Credentials

1. Run command

    `curl -d "grant_type=password&client_id=sample-ropc-client&username=sample-username&password=sample-password&client_secret=sample-client-secret" -X POST 'https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/token'`

    Replace `[GCP_REGION]` and `[PROJECT_ID]` with values of your own. Note that this request includes parameters `grant_type`, `client_id`, `client_secret`, `username`, and `password`.

    The output should like:

    `{"access_token":"[YOUR_ACCESS_TOKEN]","token_type":"JWT","expires_in":1800000}`

    The `access_token` attribute in the returned JSON file is the issued access token. 

### Client Credentials

1. Run command

    `curl -d "grant_type=client_credentials&client_id=sample-cc-client&client_secret=sample-client-secret" -X POST 'https://[GCP_REGION]-[PROJECT_ID].cloudfunctions.net/token'`

    The output should like:

    `{"access_token":"[YOUR_ACCESS_TOKEN]","token_type":"JWT","expires_in":1800000}`

    The `access_token` attribute in the returned JSON file is the issued access token. 


## Understanding the code

### `auth` function

The auth function is responsible for presenting a page where users can authorize clients to access their information:

```js
exports.auth = (req, res) => {
  console.log(req.query)
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
        }))
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
}
```

Requests with response_type set to `code` and have parameter `code_challenge` and `code_challenge_method` present initiate the Authorization Code (PKCE) flow and are processed by function `handleACPKCEAuthRequest`:

```js
function handleACPKCEAuthRequest (req, res) {
  if (req.query.client_id      === undefined ||
      req.query.redirect_url   === undefined ||
      req.query.code_challenge === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('acpkce-enabled', '=', true)

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client/redirect URL.')
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
    .catch(msg => {
      if (msg === 'Invalid client/redirect URL.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': msg
        }))
      } else {
        throw msg
      }
    })
}
```

This function first checks whether all the required parameters (`client_id`, `redirect_url`, `code_challenge`) are present. The function then makes sure that
the client ID and the redirect URL exist in the database and the client is allowed to initiate the flow. Finally, the function renders a page on which the user
can sign in with their account. The user credentials, along with other information, are sent in a `POST` request to `/signin`. In this sample, parameter 
`code_challenge_method`, though required, is not used, because it is assumed that all code challenges are hashed using `SHA-256`.

Requests with `response_type` set to `code` but without the parameters `code_challenge` and `code_challenge_method` initiate the Authorization Code (PKCE) flow 
and are processed by the `handleACAuthRequest` function; and requests with the `token` response_type are sent to the `handleImplicitAuthRequest` function. The 
logic behind these two functions is largely the same as `handleACPKCEAuthRequest`:

```js
function handleACAuthRequest (req, res) {
  if (req.query.client_id      === undefined ||
      req.query.redirect_url   === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('ac-enabled', '=', true)

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client/redirect URL.')
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
    .catch(msg => {
      if (msg === 'Invalid client/redirect URL.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': msg
        }))
      } else {
        throw msg
      }
    })
}
```

```js
function handleImplicitAuthRequest (req, res) {
  if (req.query.client_id      === undefined ||
      req.query.redirect_url   === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('implicit-enabled', '=', true)

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client/redirect URL.')
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
    .catch(msg => {
      if (msg === 'Invalid client/redirect URL.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': msg
        }))
      } else {
        throw msg
      }
    })
}
```

### `signin` function

The `signin` function receives user credentials and redirects user back to the client with an authorization code (or an access token, in the case of Implicit flow):

```js
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
}
```

Similar to the `auth` function, `signin` uses functions `handleACPKCESigninRequest`, `handleACSigninRequest` and `handleImplictSigninRequest` to process requests from the Authorization Code with PKCE flow, the Authorization Code flow and the Implicit flow respectively.

The first two functions are similar to each other; both of them issue an authorization code after all the security checks are passed:

```js
function handleACPKCESigninRequest (req, res) {
  if (req.body.username       === undefined ||
      req.body.password       === undefined ||
      req.body.client_id      === undefined ||
      req.body.redirect_url   === undefined ||
      req.body.code_challenge === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password)

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('acpkce-enabled', '=', true)

  datastore
    .runQuery(userQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid user credentials.')
      }
    })
    .then(() => {
      return datastore.runQuery(clientQuery)
    })
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client and/or redirect URL.')
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

      const codeKey = datastore.key(['authorization_code', authorizationCode])
      const data = {
        'client_id': req.body.client_id,
        'redirect_url': req.body.redirect_url,
        'exp': exp,
        'code_challenge': req.body.code_challenge
      }

      return Promise.all([
        datastore.upsert({ key: codeKey, data: data }),
        Promise.resolve(authorizationCode)
      ])
    })
    .then(results => {
      res.redirect(appendQuery(req.body.redirect_url, {
        authorization_code: results[1]
      }))
    })
}
```

```js
function handleACSigninRequest (req, res) {
  if (req.body.username       === undefined ||
      req.body.password       === undefined ||
      req.body.client_id      === undefined ||
      req.body.redirect_url   === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password)

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('ac-enabled', '=', true)

  datastore
    .runQuery(userQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid user credentials.')
      }
    })
    .then(() => {
      return datastore.runQuery(clientQuery)
    })
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client and/or redirect URL.')
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

      const key = datastore.key(['authorization_code', authorizationCode])
      const data = {
        'client_id': req.body.client_id,
        'redirect_url': req.body.redirect_url,
        'exp': exp
      }

      return Promise.all([
        datastore.upsert({ key: key, data: data }),
        Promise.resolve(authorizationCode)
      ])
    })
    .then(results => {
      res.redirect(appendQuery(req.body.redirect_url, {
        authorization_code: results[1]
      }))
    })
}
```

Note that the generated authorization code is stored in the database with `client_id`, `redirect_url` and `exp`; those values are used in later steps.

`handleImplictSigninRequest`, on the other hand, returns an access token if everything looks alright:

```js
function handleImplictSigninRequest (req, res) {
  if (req.body.username       === undefined ||
      req.body.password       === undefined ||
      req.body.client_id      === undefined ||
      req.body.redirect_url   === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password)

   const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('redirect-url', '=', req.body.redirect_url)
    .filter('implicit-enabled', '=', true)

  datastore
    .runQuery(userQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid user credentials.')
      }
    })
    .then(() => {
      return datastore.runQuery(clientQuery)
    })
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client and/or redirect URL.')
      }
    })
    .then(() => {
      const token = jwt.sign({}, privateKey, {
          algorithm: 'RS256',
          expiresIn: JWT_LIFE_SPAN,
          issuer: ISSUER
        })
      res.redirect(appendQuery(req.body.redirect_url, {
        access_token: token,
        token_type: 'JWT',
        expires_in: JWT_LIFE_SPAN
      }))
    })
}
```

This sample uses the [`jsonwebtoken`](https://www.npmjs.com/package/jsonwebtoken) library to prepare JWTs. The JWT is built using the RS256 algorithm, which involves a private/public key pair. The token itself is protected by the private key; as long as the private key is safe, no one else can issue access tokens on your behalf. However, anyone can use the public key to decrypt the JWT and verify its validity, without having to request your authorization server for help.

### `token` function

The `token` function, as its name implies, is responsible for issuing tokens:

```js
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
```

Parameter `grant_type` determines how the access token is granted. Requests with grant type `password` come from clients in the Resource Owner Password Credentials flow and are processed by function `handleROPCTokenRequest`:

```js
function handleROPCTokenRequest (req, res) {
  if (req.body.username      === undefined ||
      req.body.password      === undefined ||
      req.body.client_id     === undefined ||
      req.body.client_secret === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('client-secret', '=', req.body.client_secret)
    .filter('ropc-enabled', '=', true)

  const userQuery = datastore
    .createQuery('user')
    .filter('username', '=', req.body.username)
    .filter('password', '=', req.body.password)

  datastore
    .runQuery(clientQuery)
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid client credentials.');
      }
    })
    .then(() => datastore.runQuery(userQuery))
    .then(result => {
      if (result[0].length === 0) {
        return Promise.reject('Invalid user credentials.')
      }
    })
    .then(() => {
      const token = jwt.sign({}, privateKey, {
          algorithm: 'RS256',
          expiresIn: JWT_LIFE_SPAN,
          issuer: ISSUER
        })
      res.status(200).send(JSON.stringify({
          access_token: token,
          token_type: 'JWT',
          expires_in: JWT_LIFE_SPAN
        }))
    })
    .catch(msg => {
      if (msg === 'Invalid client credentials.' ||
          msg === 'Invalid user credentials.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': msg
        }))
      } else {
        throw msg
      }
    })
}
```

Grant type `client_credentials` are reserved for clients in the Client Credentials flow. Function `handleCCTokenRequest` handles these requests:

```js
function handleCCTokenRequest (req, res) {
  if (req.body.client_id     === undefined ||
      req.body.client_secret === undefined) {
    return res.status(400).send(JSON.stringify({
      error: 'invalid_request',
      error_description: 'Required parameters are missing in the request.'
    }))
  }

  const clientQuery = datastore
    .createQuery('client')
    .filter('client-id', '=', req.body.client_id)
    .filter('client-secret', '=', req.body.client_secret)
    .filter('cc-enabled', '=', true)

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
        })
        res.status(200).send(JSON.stringify({
          access_token: token,
          token_type: 'JWT',
          expires_in: JWT_LIFE_SPAN
        }))
      }
    });
}
```

Last but not least, both Authorization Code flow and Authorization Code with PKCE flow use the grant type `authorization_code`, with the former handled by `handleACTokenRequest` and the latter `handleACPKCETokenRequest`:

```js
function handleACTokenRequest (req, res) {
  if (req.body.client_id          === undefined ||
      req.body.client_secret      === undefined ||
      req.body.authorization_code === undefined ||
      req.body.redirect_url       === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  const clientQuery = datastore
      .createQuery('client')
      .filter('client-id', '=', req.body.client_id)
      .filter('client-secret', '=', req.body.client_secret)
      .filter('ac-enabled', '=', true)
  
  datastore
    .runQuery(clientQuery)
    .then(clientQueryResult => {
      if (clientQueryResult[0].length === 0) {
        return Promise.reject('Invalid client credentials.')
      }
    })
    .then(() => {
      return verifyAuthorizationCode(req.body.authorization_code, 
                                     req.body.client_id,
                                     req.body.redirect_url)
    })
    .then(() => {
      const token = jwt.sign({}, privateKey, {
          algorithm: 'RS256',
          expiresIn: JWT_LIFE_SPAN,
          issuer: ISSUER
        })
      res.status(200).send(JSON.stringify({
          access_token: token,
          token_type: 'JWT',
          expires_in: JWT_LIFE_SPAN
        }))
    })
    .catch(msg => {
      if (msg === 'Invalid client credentials.'             ||
          msg === 'Invalid authorization code.'             ||
          msg === 'Client ID does not match the record.'    ||
          msg === 'Redirect URL does not match the record.' ||
          msg === 'Authorization code expired.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': msg
        }))
      } else {
        throw msg
      }
    })
}
```

```js
function handleACPKCETokenRequest (req, res) {
  if (req.body.client_id          === undefined ||
      req.body.authorization_code === undefined ||
      req.body.redirect_url       === undefined ||
      req.body.code_verifier      === undefined) {
    return res.status(400).send(JSON.stringify({
      'error': 'invalid_request',
      'error_description': 'Required parameters are missing in the request.'
    }))
  }

  verifyAuthorizationCode(req.body.authorization_code,
                          req.body.client_id,
                          req.body.redirect_url, 
                          req.body.code_verifier)
    .then(() => {
      const token = jwt.sign({}, privateKey, {
          algorithm: 'RS256',
          expiresIn: JWT_LIFE_SPAN,
          issuer: ISSUER
        })
      res.status(200).send(JSON.stringify({
          access_token: token,
          token_type: 'JWT',
          expires_in: JWT_LIFE_SPAN
        }))
    })
    .catch(msg => {
      if (msg === 'Invalid authorization code.'             ||
          msg === 'Client ID does not match the record.'    ||
          msg === 'Redirect URL does not match the record.' ||
          msg === 'Authorization code expired.'             ||
          msg === 'Code verifier does not match code challenge.') {
        res.status(400).send(JSON.stringify({
          'error': 'access_denied',
          'error_description': msg
        }))
      } else if (msg === 'Code challenge does not exist.') {
        res.status(400).send(JSON.stringify({
          'error': 'invalid_request',
          'error_description': msg
        }))
      } else {
        throw msg
      }
    })
}
```

Authorization code is verified with `verifyAuthorizationCode`. Note that you do not have to decrypt the authorization code; verifying the values of  `client_id` and `redirect_url` from the request against the values on the record should suffice.

```js
function verifyAuthorizationCode(authorizationCode, clientId, redirectUrl,
                                 codeVerifier = undefined) {
  const transaction = datastore.transaction();
  const key = datastore.key(['authorization_code', authorizationCode])

  return transaction
    .run()
    .then(() => transaction.get(key))
    .then(result => {
      const entry = result[0]
      if (entry === undefined ) {
        return Promise.reject('Invalid authorization code.')
      }

      if (entry.client_id !== clientId) {
        return Promise.reject('Client ID does not match the record.')
      }

      if (entry.redirect_url !== redirectUrl) {
        return Promise.reject('Redirect URL does not match the record.')
      }

      if (entry.exp <= Date.now()) {
        return Promise.reject('Authorization code expired.')
      }

      if (codeVerifier         !== undefined &&
          entry.code_challenge !== undefined) {

        let codeVerifierBuffer = new Buffer(codeVerifier);
        let codeChallenge = crypto
                              .createHash('sha256')
                              .update(codeVerifierBuffer)
                              .digest()
                              .toString('base64')
                              .replace(/\+/g, '-')
                              .replace(/\//g, '_')
                              .replace(/=/g, '');
        if (codeChallenge !== entry.code_challenge) {
          return Promise.reject('Code verifier does not match code challenge.');
        }
      } else if (codeVerifier         === undefined ||
                 entry.code_challenge === undefined) {
        // Pass
      } else {
        return Promise.reject(
          'Code challenge or code verifier does not exist.');
      }

      return transaction.delete(key)
    })
    .then(() => transaction.commit())
    .catch(msg => {
      transaction.rollback()
      throw msg
    })
}
```

## Sidenotes

* This tutorial uses Datastore, a highly scalable NoSQL database, to store user credentials, client information and authorization codes. It is also possible to use other data storage solutions, such as [memcached](https://memcached.org/), [Redis](https://redis.io/), [Cloud SQL](https://cloud.google.com/sql/docs/), etc; however, you should not store any important information in-memory with Cloud Functions.

* This tutorial assumes that client has registered with your service and provided its redirect URL. Additionally, the authorization service requires a full match between the redirect URL in the request and the redirect URL on the record. In reality, however, it is common for developers to add additional values in the redirect URL to keep states during transition; if your use case requires variable redirect URLs, you should drop the full match restriction.

* Access tokens in this sample only contains information regarding its issuer and expiration date. Depending on your use case, it might be necessary to pose more restrictions. Common fields to implement in the access token include `audience` (destinations where access token is allowed to arrive at) and `scopes` (level of access that the token grants).

* You can also use the `jsonwebtoken` library to verify JWTs. See their documentation for more information.

## Cleaning up

After you have finished this tutorial, you can clean up the resources you created on Google Cloud so that you will not be billed for them in the future. To clean up, you can delete the whole project or delete the Cloud Functions you deployed. 

### Deleting the project

Visit the [Manage resources](https://console.cloud.google.com/cloud-resource-manager) menu. Select the project you used for this tutorial and click Delete. Note that once the project is deleted, the project ID cannot be reused.

If you have Cloud SDK installed in the system, you can also [use the gcloud command-line to delete a project](https://cloud.google.com/sdk/gcloud/reference/projects/delete).

### Deleting the functions

Go to the [Cloud Functions overview](https://console.cloud.google.com/functions) page. Select the functions you would like to remove and click **Delete**.
