---
title: Monitor Compute Engine managed instance groups with Simple MIG Dashboard
description: Learn how to monitor state of a managed instance group and visualize it in a JavaScript application.
author: lopekpl
tags: Compute Engine, Cloud Endpoints, OAuth
date_published: 2018-02-06
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Simple MIG Dashboard is a tool for monitoring the state of instances of
a managed instance group (MIG). For each instance it visualizes its current
action (e.g. `CREATING`, `RESTARTING`) and its instance template. It can be
especially useful to monitor progress of a rolling update: it shows how
the state (including health) of each instance is changing over time.

This tutorial explains how to set up and use Simple MIG Dashboard on
your local machine with your Google Cloud project. It walks you
through the process of setting up a Google Cloud web application and granting it
all necessary permissions to access your project data.

Simple MIG Dashboard is implemented in JavaScript using Angular
framework. It uses Google Charts library for visualization purposes and
Google API Client Library for JavaScript to communicate with Google
Cloud.

## Before you begin

In this tutorial, we assume that you have a Google Cloud
project with an existing managed instance group that you want to monitor.

## Running the dashboard

To run the dashboard locally, you need to set up a new Google Cloud application.
[Set up OAuth](https://support.google.com/cloud/answer/6158849) to obtain the client ID that will be used to identify your application when
making API calls. Choose **Web application** as application type, and add
[http://localhost:8080](http://localhost:8000) to the list
of authorized JavaScript origins for your app.

After you have obtained the client ID for your application, you are ready to run
the dashboard locally:

1.  `git clone https://github.com/GoogleCloudPlatform/community`

2.  `cd community/tutorials/compute-managed-instance-groups-dashboard/webapp/`

3.  Edit `gapi.js` file: replace *clientId* in line 44 with your Client ID

4.  From `webapp/` run: `python -m SimpleHTTPServer 8080`

Now go to [http://localhost:8080](http://localhost:8080)
in your browser, and you'll be greeted with a window which allows you to
log in to your Google account. Choose the account which has the access
to your Google Cloud project. The next window asks for your
permission to allow the Dashboard to view and manage your data across
Google Cloud services.

Once you grant the necessary permissions, you'll see an error stating
that Google Cloud Resource Manager API has not been used in your project
before. Follow the link from the error message to enable it. Give it a
few minutes to propagate, go back to your Simple MIG Dashboard and
refresh the page. Your Dashboard is ready to use.

## Overview of the dashboard

It's time to learn how to use the dashboard to monitor the state of your
MIG:

**Step 1.** Choose the name of the project and click **Load Instance Groups**.

![Picking project](https://storage.googleapis.com/gcp-community/tutorials/compute-managed-instance-groups-dashboard/step1.png)

**Step 2.** From the list of managed instance groups in this project, select
the one you want to monitor.

![Picking instance group](https://storage.googleapis.com/gcp-community/tutorials/compute-managed-instance-groups-dashboard/step2.png)

**Step 3.** You are now monitoring your MIG.

![MIG Dashboard main view](https://storage.googleapis.com/gcp-community/tutorials/compute-managed-instance-groups-dashboard/step3.png)

1.  **Timespan** adjusts horizontal axis of *Instance status* chart.

2.  **Group by zone** is visible only if your MIG is regional. When selected, it will change the order of the machines in the chart to display all machines in one zone together.

3.  **Instance status** tab contains a chart that visualises how instances in your MIG were changing their state over time. In the example from the screenshot above:

    -   Top three instances are using *regional-instance-7* instance template and have been stable for at least 3 minutes.

    -   Three instances in the middle were running *regional-instance-7* instance template, but they are now being deleted for about 2 minutes and 30 seconds.

    -   Bottom three instances were created around 2 minutes and 40 seconds ago from *regional-instance-1* instance template. They were in *CREATING* state for about 10 seconds, and then became stable.

4.  **Summary** displays cumulative information about the status of the machines in the MIG. It allows you to check how many instances there are in each state. Together with *Group by zone*, the Summary tab allows you to see what is happening with your machines in each of the zones.

5.  **Instance health** tab is visible only if your MIG is connected to a Backend Service and has a Health Check configured. In this case, each machine reports its health periodically. The chart displays the changes of health in time for each of the machines.

6.  **Legend** provides information about the colors in the chart.

## Code walkthrough

### Initialization and authentication using gapi

Once the user opens the page, Angular's `ng-init` embedded in the
[`body` element of *index.html*][index] runs our `initialize()` function from
[*main-controller.js*][main-controller].

`initialize()` is a chain of promises that:

1.  Initializes the JavaScript Google Compute API client with OAuth client ID, scope, and API discovery documents.

2.  Calls Google Authenticator's `signIn()`, which checks if user is logged in with their Google account. If not, it will show a pop up to sign in.

3.  Fetches the list of Google Cloud projects that the user has access to and stores all project IDs.

Once done, `initialize()` clears the message box by calling
`$scope.setMessage()`, unless one of the steps described above threw an
error, in which case the error is displayed to the user.

```js
$scope.initialize = function() {
  $scope.setMessage('Authorizing...', 'loading');

  function onGapiLoaded() {
    getInitializeGapiClientRequest()
      .then(getSignInRequest)
      .then($scope.getProjectIds)
      .then(
          function() {
            $scope.setMessage();
          },
          function(error) {
            $scope.setMessage(
                error.details || error.error || error, 'error');
          });
  }
  gapi.load('client:auth2', onGapiLoaded);
};
```

The component responsible for project choice is defined in
[*components/mig-picker.js*][mig-picker]. Once the user chooses the project ID, function
`loadInstanceGroups()` is called. It makes several calls to Google Cloud
Compute API to fetch data about managed instance groups belonging to the
project. Progress is reported to the user with calls to `messageFunction`,
which is injected into the [`mig-picker` component in *index.html*][index].

Next, the user chooses the managed instance group to monitor. New object
of `MigHistory` class, defined in [*mig-history.js*][mig-history], is created. `MigHistory`
stores state and health status changes for all instances that belong to
the managed instance group. Every second, `MigHistory` is updated by
`fetchInstancesInfo()` method that fetches the current state of all the
machines calling the Google Compute API.

`MigHistory` object is injected into
[`mig-dashboard` component in *index.html*][index] as `vmMap`, and is used to
periodically redraw the status charts.

### Calls to Google Compute API

[*gapi.js*][gapi] contains all the API requests used by Simple MIG Dashboard. Once the user chooses the project, the Dashboard fetches the list of managed instance groups that belong to this project using [*compute.instanceGroupManagers.aggregatedList*][igms-list]. The call returns both zonal and regional managed instance groups. Next, the user chooses the managed instance group they want to monitor. The dashboard fetches the list of instances in the selected managed instance group. Depending on the type of the managed instance group, it either makes a call to [*compute.regionInstanceGroupManagers.listManagedInstances*][rmig-list] for regional managed instance group or [*compute.instanceGroupManagers.listManagedInstances*][mig-list] for zonal managed instance group. Both methods return a single `managedInstances` object that lists all the instances from the managed instance group together with their  `currentAction` (e.g. CREATING, RUNNING) and `version`, which defines which instance template was used to create the instance.

To display health of instances, the Dashboard first fetches all Backend Services defined in the project using [*compute.backendServices.list*][bs-list]. Then it finds the particular Backend Service connected to the selected managed instance group by looking at *group* field of Backend Service resources. It gets health statuses of managed instance group instances by calling [*compute.backendServices.getHealth*][get-health]. The request returns a list of *healthStatus* objects that map instances from the managed instance group to their *healthState*.


[index]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/compute-managed-instance-groups-dashboard/webapp/index.html

[main-controller]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/compute-managed-instance-groups-dashboard/webapp/main-controller.js

[mig-picker]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/compute-managed-instance-groups-dashboard/webapp/components/mig-picker.js

[mig-history]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/compute-managed-instance-groups-dashboard/webapp/mig-history.js

[gapi]: https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/compute-managed-instance-groups-dashboard/webapp/gapi.js

[igms-list]: https://cloud.google.com/compute/docs/reference/rest/beta/instanceGroupManagers/aggregatedList

[mig-list]: https://cloud.google.com/compute/docs/reference/rest/beta/instanceGroupManagers/listManagedInstances

[rmig-list]: https://cloud.google.com/compute/docs/reference/rest/beta/regionInstanceGroupManagers/listManagedInstances

[bs-list]: https://cloud.google.com/compute/docs/reference/rest/beta/backendServices/list

[get-health]: https://cloud.google.com/compute/docs/reference/rest/beta/backendServices/getHealth
