window.getBackendServicesListRequest = function (project) {
  return window.gapi.client.compute.backendServices.list({
    'project': project
  });
};

window.getInstancesHealthRequest = function (project, backendService, groupUrl) {
  return window.gapi.client.compute.backendServices.getHealth({
    'project': project,
    'backendService': backendService,
    'group': groupUrl
  });
};

window.getInstancesListRequest = function (project, gceScope, instanceGroupManager) {
  if (gceScope.startsWith('regions/')) {
    return window.gapi.client.compute.regionInstanceGroupManagers.listManagedInstances({
      'project': project,
      'instanceGroupManager': instanceGroupManager,
      'region': gceScope.substr(8)
    });
  } else if (gceScope.startsWith('zones/')) {
    return window.gapi.client.compute.instanceGroupManagers.listManagedInstances({
      'project': project,
      'instanceGroupManager': instanceGroupManager,
      'zone': gceScope.substr(6)
    });
  }
  return Promise.reject(new Error('Failed to parse provided gceScope: ' + gceScope));
};

window.getProjectsListRequest = function () {
  return window.gapi.client.cloudresourcemanager.projects.list({});
};

window.getInstanceGroupManagersListRequest = function (projectId) {
  return window.gapi.client.compute.instanceGroupManagers.aggregatedList({
    'project': projectId
  });
};

window.getInitializeGapiClientRequest = function () {
  return window.gapi.client.init({
    'clientId': 'PASTE YOUR CLIENT ID HERE',
    'scope': 'https://www.googleapis.com/auth/cloud-platform',
    'discoveryDocs': [
      'https://www.googleapis.com/discovery/v1/apis/compute/beta/rest',
      'https://www.googleapis.com/discovery/v1/apis/cloudresourcemanager/v1/rest']
  });
};

window.getSignInRequest = function () {
  return window.gapi.auth2.getAuthInstance().signIn();
};

/*
 * Convenience methods for parsing data from GCE.
 */
window.urlToResourceName = function (url) {
  if (!url || url.lastIndexOf('/') === -1) {
    return undefined;
  }
  return url.substr(url.lastIndexOf('/') + 1);
};

window.getInstanceTemplate = function (instanceData) {
  return instanceData.version
    ? window.urlToResourceName(instanceData.version.instanceTemplate) : undefined;
};

window.getInstanceName = function (instanceData) {
  return window.urlToResourceName(instanceData.instance);
};

window.getInstanceZone = function (instanceData) {
  var regex = /https:.*\/(.*)\/instances\/.*/g;
  var matches = regex.exec(instanceData.instance);
  return matches[1];
};

window.getInstanceError = function (instanceData) {
  if (instanceData.lastAttempt && instanceData.lastAttempt.errors) {
    return instanceData.lastAttempt.errors.errors[0].code;
  }
  return undefined;
};
