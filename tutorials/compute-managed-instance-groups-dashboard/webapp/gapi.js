function getBackendServicesListRequest (project) {
  return gapi.client.compute.backendServices.list({
    'project': project
  });
}

function getInstancesHealthRequest (project, backendService, groupUrl) {
  return gapi.client.compute.backendServices.getHealth({
    'project': project,
    'backendService': backendService,
    'group': groupUrl
  });
}

function getInstancesListRequest (project, gceScope, instanceGroupManager) {
  if (gceScope.startsWith('regions/')) {
    return gapi.client.compute.regionInstanceGroupManagers.listManagedInstances({
      'project': project,
      'instanceGroupManager': instanceGroupManager,
      'region': gceScope.substr(8)
    });
  } else if (gceScope.startsWith('zones/')) {
    return gapi.client.compute.instanceGroupManagers.listManagedInstances({
      'project': project,
      'instanceGroupManager': instanceGroupManager,
      'zone': gceScope.substr(6)
    });
  }
  return Promise.reject(new Error('Failed to parse provided gceScope: ' + gceScope));
}

function getProjectsListRequest () {
  return gapi.client.cloudresourcemanager.projects.list({});
}

function getInstanceGroupManagersListRequest (projectId) {
  return gapi.client.compute.instanceGroupManagers.aggregatedList({
    'project': projectId
  });
}

function getInitializeGapiClientRequest () {
  return gapi.client.init({
    'clientId': '<PASTE YOUR CLIENT ID HERE>',
    'scope': 'https://www.googleapis.com/auth/cloud-platform',
    'discoveryDocs': [
      'https://www.googleapis.com/discovery/v1/apis/compute/beta/rest',
      'https://www.googleapis.com/discovery/v1/apis/cloudresourcemanager/v1/rest']
  });
}

function getSignInRequest () {
  return gapi.auth2.getAuthInstance().signIn();
}

/*
 * Convenience methods for parsing data from GCE.
 */
function urlToResourceName (url) {
  if (!url || url.lastIndexOf('/') == -1) {
    return undefined;
  }
  return url.substr(url.lastIndexOf('/') + 1);
}

function getInstanceTemplate (instanceData) {
  return instanceData.version
    ? urlToResourceName(instanceData.version.instanceTemplate) : undefined;
}

function getInstanceName (instanceData) {
  return urlToResourceName(instanceData.instance);
}

function getInstanceZone (instanceData) {
  var regex = /https:.*\/(.*)\/instances\/.*/g;
  var matches = regex.exec(instanceData.instance);
  return matches[1];
}

function getInstanceError (instanceData) {
  if (instanceData.lastAttempt && instanceData.lastAttempt.errors) {
    return instanceData.lastAttempt.errors.errors[0].code;
  }
  return undefined;
}
