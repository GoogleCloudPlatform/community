---
title: Connect Container Builder to GitHub through Cloud Functions
description: Learn how to create GitHub statuses from Container Builder events using Cloud Functions.
author: cbuchacher
tags: Cloud Functions, GitHub, Node.js
date_published: 2018-05-14
---

This tutorial demonstrates how to use [Cloud Build][gcb] as
a continuous integration service for GitHub repositories. You will implement a
[Cloud Function][gcf] that listens to build events and updates the
build status in GitHub using the [Status API][statuses]. The function is
implemented in [Node.js][node].

[gcb]: https://cloud.google.com/container-builder/docs/
[gcf]: https://cloud.google.com/functions/docs/
[statuses]: https://developer.github.com/v3/repos/statuses/
[node]: https://nodejs.org/en/

## Prerequisites

1.  Create a project in the [Cloud Console][console].
1.  [Enable billing][billing] for your project.
1.  Install the [Cloud SDK][sdk].

[console]: https://console.cloud.google.com/
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing
[sdk]: https://cloud.google.com/sdk/

## Set up automated builds with a build trigger

You will use [Cloud Build][gcb] and its
[build triggers](https://cloud.google.com/cloud-build/docs/running-builds/create-manage-triggers)
to upload your website automatically every time you push a new git
commit to the source repository.

If you do not have a repository on GitHub, you can fork
[this sample repository][sample-repo] for this tutorial.

1. Go to the Cloud Build &rarr; [**Triggers**][p6n-triggers] page.

2. Click **Create trigger**.

3. Enter a name for your trigger (e.g., `publish-website`).

4. If you forked the [sample repository][sample-repo] for this tutorial,
   select **Push to a branch** as your repository event.

5. Select the repository that contains your source code and build
   configuration file.

6. Specify the regular expression for the branch that will start your trigger (e.g., `^master$`).

7. Choose **Cloud build configuration (yaml or json)** as your build configuration
   file type.

8. Set the file location to `cloudbuild.yaml`.

9. Click **Create** to save your build trigger.

Now, create a `cloudbuild.yaml` file with the following contents in your
repository. Note that you can add files to your repository on the GitHub website, or
by cloning the repository on your development machine:

```yaml
steps:
  - name: gcr.io/cloud-builders/git
    args: ["show", "README.md"]
```

This YAML file declares a build step with the `git show` command. It prints
the contents of the `README.md` file to the build logs.

After saving the file, commit and push the changes:

    $ git add cloudbuild.yaml
    $ git commit -m 'Add build configuration'
    $ git push

[bt]: https://cloud.google.com/container-builder/docs/running-builds/automate-builds
[sample-repo]: https://github.com/GoogleCloudPlatform/web-docs-samples
[triggers]: https://console.cloud.google.com/gcr/triggers

### Start the first build

After you push the `cloudbuild.yaml` file to your repository and create the build
trigger, you can start the first build manually. Go to the Cloud Console
[**Triggers**][triggers] section, click **Run trigger**, and choose the the branch
(e.g., master) to build.

![Trigger the first build manually](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-github-container-builder/trigger-build.png)

Now click **Build history** on the left and watch the build job execute and
succeed.

Remember that after now, every commit pushed to any branch of your GitHub
repository will trigger a new build. If you need to change which git branches
or tags you use for publishing, you can update the build trigger configuration.

## Preparing the Cloud Function

1.  Run the following commands in a new empty directory.
1.  Create a `package.json` file by running the following command:

        $ npm init

1.  Run the following command to install the dependencies that the function
    uses to make REST calls to the GitHub API:

        $ npm install --save --save-exact @octokit/rest@15.2.6

### Writing the Function code

Create a file named `index.js` with the following contents:

[embedmd]:# (index.js)
```js
'use strict';

const octokit = require('@octokit/rest')();
const GITHUB_ACCESS_TOKEN = '[TOKEN]';

/**
 * Background Cloud Function to be triggered by cloud-builds Pub/Sub topic.
 *
 * @param {object} event The Cloud Functions event.
 */
exports.gcb_github = (event) => {
  const build = eventToBuild(event.data.data);
  return postBuildStatus(build);
};

// eventToBuild transforms pubsub event message to a build object.
const eventToBuild = (data) => {
  return JSON.parse(new Buffer(data, 'base64').toString());
}

function postBuildStatus(build) {
  octokit.authenticate({
    type: 'token',
    token: GITHUB_ACCESS_TOKEN
  });

  let repo = getRepo(build);
  if (repo === null || repo.site !== 'github') {
    return Promise.resolve();
  }
  let [ state, description ] = buildToGithubStatus(build);
  return octokit.repos.createStatus({
    owner: repo.user,
    repo: repo.name,
    sha: build.sourceProvenance.resolvedRepoSource.commitSha,
    state: state,
    description: description,
    context: 'gcb',
    target_url: build.logUrl
  });
}

function getRepo(build) {
  let repoNameRe = /^([^-]*)-([^-]*)-(.*)$/;
  let repoName = build.source.repoSource.repoName;
  let match = repoNameRe.exec(repoName);
  if (!match) {
    console.error(`Cannot parse repoName: ${repoName}`);
    return null;
  }
  return {
    site: match[1],
    user: match[2],
    name: match[3]
  };
}

function buildToGithubStatus(build) {
  let map = {
    QUEUED: ['pending', 'Build is queued'],
    WORKING: ['pending', 'Build is being executed'],
    FAILURE: ['error', 'Build failed'],
    INTERNAL_ERROR: ['failure', 'Internal builder error'],
    CANCELLED: ['failure', 'Build cancelled by user'],
    TIMEOUT: ['failure', 'Build timed out'],
    SUCCESS: ['success', 'Build finished successfully']
  }
  return map[build.status];
}
```

The container builder publishes messages in the `cloud-builds`
[Pub/Sub][pubsub] topic. Each message triggers the function with the
message contents passed as input data. The message contains the [build][build]
response. Here is an example of a build response, reduced to the most relevant
fields:

```json
{
  "id": "3e3c9152-6ba9-b562-e9c6-a49651c076ce",
  "projectId": "my-google-cloud-project-1234",
  "status": "WORKING",
  "source": {
      "repoSource": {
          "projectId": "my-google-cloud-project-1234",
          "repoName": "github-myowner-myreponame",
          "branchName": "master"
      }
  },
  "sourceProvenance": {
    "resolvedRepoSource": {
      "commitSha": "29d39613fa9958598228f7f162b3f03ab4189ece"
    }
  },
  "logUrl": "https://console.cloud.google.com/gcr/builds/3e3c9152-6ba9-b562-e9c6-a49651c076ce?project=1234567890"
};
```

The function then determines the GitHub repository owner and name, maps the
build status (`WORKING`, `FAILURE`, `SUCCESS`) to a commit state (`pending`,
`error`, `success`), and POST's to the Statuses API.

[pubsub]: https://cloud.google.com/pubsub/docs/
[build]: https://cloud.google.com/container-builder/docs/api/reference/rest/v1/projects.builds

### Generating a GitHub personal access token

1. Read about [Creating a personal access token for the command line][token].
1. Select `repo:status` from the scopes.
1. Substitute the generated token for `[TOKEN]` in `index.js`.

To create statuses, you must have write access to the target repository.
`POST` calls to the Status API will return a `NOT FOUND` error otherwise.

[token]: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/

## Deploying the Cloud Function

1.  Read about [deploying Cloud Functions][deploying].
1.  Run the following command to deploy the function:

        $ gcloud beta functions deploy gcb_github --stage-bucket [YOUR_STAGE_BUCKET] --trigger-topic cloud-builds

    Replace `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket (e.g., `gs://[PROJECT_ID]_cloudbuild`).

[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem

## Testing the integration

Trigger another build manually. The commit status is shown as a check mark or X mark in
the commit log in GitHub. More details of the build status are shown in Pull Requests.

![GitHub status check](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-github-container-builder/github-status-check.png)

You can check the [logs][logs] for errors.

[logs]: https://console.cloud.google.com/logs/viewer

## Credits

Section [Set up automated builds](#set-up-automated-builds) is derived from
@ahmetb's [Automated Static Website Publishing with Cloud Container
Builder](https://cloud.google.com/community/tutorials/automated-publishing-cloud-build) tutorial.
