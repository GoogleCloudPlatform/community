---
title: Using Cloud Functions to auto-assign reviewers to GitHub pull requests
description: Learn how to use Cloud Functions to automatically assign reviewers to new GitHub pull requests.
author: jmdobry
tags: Node.js, Cloud Functions, GitHub
date_published: 2017-02-03
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using [Cloud Functions][functions] to
automatically assign a reviewer to [GitHub pull requests][pr] as they are
opened. The Cloud Function is implemented in [Node.js][node].

The sample Cloud Function is triggered by webhook request from GitHub when a
pull request is opened, and then attempts to assign to the pull request the
reviewer with the smallest review workload from a supplied list of eligible
reviewers. The review workload of the eligible reviewers is inferred from the
reviews that have already been assigned to them on other open pull requests in
the repository.

[functions]: https://cloud.google.com/functions
[pr]: https://help.github.com/articles/about-pull-requests/
[node]: https://nodejs.org/en/

## Prerequisites

1. Create a GitHub account and acquire administrative rights to a repository.
1. Create a project in the [Cloud Console][console].
1. Enable billing for your project.
1. Install the [Cloud SDK][sdk].

[console]: https://console.cloud.google.com/
[sdk]: https://cloud.google.com/sdk/

## Preparing the GitHub webhook

### Adding the webhook

1.  Go to your repository's settings page on GitHub and click **Webhooks**.
1.  Click **Add webhook**.
1.  In the **Payload URL** field enter:

        https://us-central1-[YOUR_PROJECT_ID].cloudfunctions.net/handleNewPullRequest

    replacing `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

1.  For **Content type** select `application/json`.
1.  In the **Secret** enter a long secret string of your choosing.
1.  For **Which events would you like to trigger this webhook?** select
    **Let me select individual events.**

    1. Check the box for the **Pull request** event.
1.  Check the box for **Active** at the bottom.
1.  Click **Add webhook**.

### Creating a personal access token

The sample Cloud Functions relies on a personal access token to access the
GitHub API and retrieve pull request review data from your repository. It
doesn't matter what GitHub user the access token comes from, as long as the user
has access to the repository.

1.  Go to the user's settings page on GitHub and click
    **Personal Access Tokens**.
1.  Click **Generate new token**.
1.  Enter a description of your choosing in the **Token description** field.
1.  Check the box for the **repo** scope.
1.  Click **Generate token**.
1.  Take note of the generated token value, because you won't be able to
    see the token's value again after you leave the page. You need the token's
    value later in this tutorial.

## Writing the function

### Preparing the settings file

Create a file named `settings.json` which will store the secret token used by
GitHub to make the webhook request, the personal access token used by the
function to access the GitHub API, and the list of reviewers.

Here's an example:

```json
{
  "secretToken": "[YOUR_SECRET_TOKEN]",
  "accessToken": "[YOUR_ACCESS_TOKEN]",
  "reviewers": [
    "bob",
    "alice"
  ]
}
```

In your `settings.json` file, replace `[YOUR_SECRET_TOKEN]` with the secret
token you used when you created the GitHub webhook, and replace
`[YOUR_ACCESS_TOKEN]` with the value of the personal access you generated
earlier.

Set the `reviewers` array to a list of GitHub usernames representing the
reviewers that should be eligible for assignment to new pull requests on your
repository.

**Warning**: Avoid committing your `settings.json` to source control.

### Preparing the module

1.  Create a `package.json` file by running the following:

        npm init

    or

        yarn init

1.  Install the single dependency used by the sample Cloud Function:

        npm install --save got

    or

        yarn add got

    This dependency is used by the Cloud Function to make requests to the GitHub
    API.

### Writing the function code

Create a file named `index.js` and paste in the following code:

[embedmd]:# (index.js /const crypto/ /;\s};/)
```js
const crypto = require('crypto');
const got = require('got');
const url = require('url');

const settings = require('./settings.json');

/**
 * Assigns a reviewer to a new pull request from a list of eligible reviewers.
 * Reviewers with the least assigned reviews on open pull requests will be
 * prioritized for assignment.
 *
 * @param {object} req
 * @param {object} res
 */
exports.handleNewPullRequest = (req, res) => {
  // We only care about newly opened pull requests
  if (req.body.action !== 'opened') {
    res.end();
    return;
  }

  const pullRequest = req.body.pull_request;
  console.log(`New PR: ${pullRequest.title}`);

  // Validate the request
  return validateRequest(req)
    // Download all pull requests
    .then(() => getPullRequests(pullRequest.base.repo))
    // Figure out who should review the new pull request
    .then((pullRequests) => getNextReviewer(pullRequest, pullRequests))
    // Assign a reviewer to the new pull request
    .then((nextReviewer) => assignReviewer(nextReviewer, pullRequest))
    .then(() => {
      res
        .status(200)
        .end();
    })
    .catch((err) => {
      console.error(err.stack);
      res
        .status(err.statusCode ? err.statusCode : 500)
        .send(err.message)
        .end();
    });
};
```

Notice the named export `handleNewPullRequest`—this is the function that will
be executed whenever a new pull request is opened on your repository.

The `handleNewPullRequest` function does the following:

1.  Checks to make sure that it received a new pull request event.
1.  Validates that the request came from GitHub with the correct secret token.
1.  Downloads all open pull requests of the repository with their associated
    reviews.
1.  Assigns a reviewer to the new pull request based on the amount of reviews
    already assigned to other reviewers for the open pull requests.

Note that `handleNewPullRequest` makes several function calls. You will add
those functions to your code below.

### Validating the request from GitHub

It's a good idea to [secure your webhook][secure]. Add the following to your
`index.js` file:

[secure]: https://developer.github.com/webhooks/securing/

[embedmd]:# (index.js /function validateRequest/ /}\);\s}/)
```js
function validateRequest (req) {
  return Promise.resolve()
    .then(() => {
      const digest = crypto
        .createHmac('sha1', settings.secretToken)
        .update(JSON.stringify(req.body))
        .digest('hex');

      if (req.headers['x-hub-signature'] !== `sha1=${digest}`) {
        const error = new Error('Unauthorized');
        error.statusCode = 403;
        throw error;
      } else {
        console.log('Request validated.');
      }
    });
}
```

### Retrieving all open pull requests

In order to figure out how many pull requests the eligible receivers are already
reviewing, you need to retrieve all of the repository's open pull requests. Add
a GitHub API helper function to your `index.js` file:

[embedmd]:# (index.js /function makeRequest/ /body\);\s}/)
```js
function makeRequest (uri, options) {
  options || (options = {});

  // Add appropriate headers
  options.headers || (options.headers = {});
  options.headers.Accept = 'application/vnd.github.black-cat-preview+json,application/vnd.github.v3+json';

  // Send and accept JSON
  options.json = true;
  if (options.body) {
    options.headers['Content-Type'] = 'application/json';
    if (typeof options.body === 'object') {
      options.body = JSON.stringify(options.body);
    }
  }

  // Add authentication
  const parts = url.parse(uri);
  parts.auth = `jmdobry:${settings.accessToken}`;

  // Make the request
  return got(parts, options).then((res) => res.body);
}
```

Add the following function for retrieving pull requests:

[embedmd]:# (index.js /function getPullRequests/ /}\);\s}/)
```js
function getPullRequests (repo, page) {
  const PAGE_SIZE = 100;

  if (!page) {
    page = 1;
  }

  // Retrieve a page of pull requests
  return makeRequest(`${repo.url}/pulls`, {
    query: {
      sort: 'updated',
      page: page,
      per_page: PAGE_SIZE
    }
  }).then((pullRequests) => {
    // Filter out requested reviews who are not found in "settings.reviewers"
    pullRequests.forEach((pr) => {
      pr.requested_reviewers || (pr.requested_reviewers = []);
      // Filter out reviewers not found in "settings.reviewers"
      pr.requested_reviewers = pr.requested_reviewers.filter((reviewer) => {
        return settings.reviewers.includes(reviewer.login);
      });
    });

    // If more pages exists, recursively retrieve the next page
    if (pullRequests.length === PAGE_SIZE) {
      return getPullRequests(repo, page + 1)
        .then((_pullRequests) => pullRequests.concat(_pullRequests));
    }

    // Finish by retrieving the pull requests' reviews
    return getReviewsForPullRequests(pullRequests);
  });
}
```

And add the following for retrieving a pull requests reviews:

[embedmd]:# (index.js /function getReviewsForPullRequests/ /}\);\s}/)
```js
function getReviewsForPullRequests (pullRequests) {
  console.log(`Retrieving reviews for ${pullRequests.length} pull requests.`);
  // Make a request for each pull request's reviews
  const tasks = pullRequests.map((pr) => makeRequest(`${pr.url}/reviews`));
  // Wait for all requests to complete
  return Promise.all(tasks)
    .then((responses) => {
      responses.forEach((reviews, i) => {
        reviews || (reviews = []);
        // Attach the reviews to each pull request
        pullRequests[i].reviews = reviews
          // Filter out reviews whose reviewers are not found in
          // "settings.reviewers"
          .filter((review) => settings.reviewers.includes(review.user.login))
          // Only reviews with changes requested count against a reviewer's
          // workload
          .filter((review) => review.state === 'CHANGES_REQUESTED');
      });
      return pullRequests;
    });
}
```

### Calculating the current workloads of all reviewers

Now that you have the open pull requests and their reviews, you can calculate
the current review workload of eligible receivers. The following function figures
out how many reviews are already assigned to the eligible reviewers. It then
sorts the reviewers by least-assigned reviews to most-assigned reviews. Add it
to your `index.js` file:

[embedmd]:# (index.js /function calculateWorkloads/ /workloads;\s}/)
```js
function calculateWorkloads (pullRequests) {
  // Calculate the current workloads of each reviewer
  const reviewers = {};
  settings.reviewers.forEach((reviewer) => {
    reviewers[reviewer] = 0;
  });
  pullRequests.forEach((pr, i) => {
    // These are awaiting the reviewer's initial review
    pr.requested_reviewers.forEach((reviewer) => {
      reviewers[reviewer.login]++;
    });
    // For these the reviewer has requested changes, and has yet to approve the
    // pull request
    pr.reviews.forEach((review) => {
      reviewers[review.user.login]++;
    });
  });

  console.log(JSON.stringify(reviewers, null, 2));

  // Calculate the reviewer with the smallest workload
  let workloads = [];
  Object.keys(reviewers).forEach((login) => {
    workloads.push({
      login: login,
      reviews: reviewers[login]
    });
  });
  workloads.sort((a, b) => a.reviews - b.reviews);

  console.log(`Calculated workloads for ${workloads.length} reviewers.`);

  return workloads;
}
```

### Choosing the next reviewer

With the reviewers sorts by current workload, you can choose the reviewer for
the new pull request, taking care to not assign a reviewer to their own pull
request. Add the following to your `index.js` file:

[embedmd]:# (index.js /function getNextReviewer/ /login;\s}/)
```js
function getNextReviewer (pullRequest, pullRequests) {
  let workloads = calculateWorkloads(pullRequests);

  workloads = workloads
    // Remove reviewers who have a higher workload than the reviewer at the
    // front of the queue:
    .filter((workload) => workload.reviews === workloads[0].reviews)
    // Remove the opener of the pull request from review eligibility:
    .filter((workload) => workload.login !== pullRequest.user.login);

  const MIN = 0;
  const MAX = workloads.length - 1;

  // Randomly choose from the remaining eligible reviewers:
  const choice = Math.floor(Math.random() * (MAX - MIN + 1)) + MIN;

  return workloads[choice].login;
}
```

### Assigning a reviewer to the pull request

Finally you can make the request to the GitHub API to assign the chosen reviewer
to the pull request. Add the following to your `index.js` file:

[embedmd]:# (index.js /function assignReviewer/ /}\);\s}/)
```js
function assignReviewer (reviewer, pullRequest) {
  console.log(`Assigning pull request to ${reviewer}.`);
  return makeRequest(`${pullRequest.url}/requested_reviewers`, {
    body: {
      reviewers: [reviewer]
    }
  });
}
```

## Deploying and testing the function

1.  Read about [deploying Cloud Functions][deploying].
1.  Run the following to deploy the function:

        gcloud alpha functions deploy handleNewPullRequest --trigger-http --stage-bucket [YOUR_STAGE_BUCKET]

    Replacing `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.

1.  Open a new pull request on your repository, which should be assigned a
    reviewer by the Cloud Function.

To view the logs for the Cloud Function, run the following:

    gcloud alpha functions logs view handleNewPullRequest
[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem
