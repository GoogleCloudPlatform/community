class InstanceHistoryElement {
  constructor (instanceData, healthState) {
    this.template = window.getInstanceTemplate(instanceData);
    this.currentAction = instanceData.currentAction;
    this.healthState = healthState;
    this.timestamp = Date.now();
  }
}

class InstanceHistory {
  constructor (zone) {
    this.zone = zone;
    this.history = [];
    this.healthState = 'UNKNOWN';
  }

  consumeInstanceInfo (instance) {
    var historyElement = new InstanceHistoryElement(instance, this.healthState);
    if (this.history.length === 0 ||
        this.history[0].template !== historyElement.template ||
        this.history[0].currentAction !== historyElement.currentAction ||
        this.history[0].healthState !== historyElement.healthState) {
      this.history.unshift(historyElement);
    }
    this.error = window.getInstanceError(instance);
  }

  setHealthState (healthState) {
    this.healthState = healthState;
  }

  markInstanceAsGone () {
    this.consumeInstanceInfo(
      {template: undefined, currentAction: 'gone'}, undefined);
  }
}

window.MigHistory = class {
  constructor (migResourceURL, managerResourceURL, backendServiceResourceURL, projectId, gceScope) {
    this.migResourceURL = migResourceURL; // the url of the (managed) instance group
    this.managerResourceURL = managerResourceURL; // the url of manager of the instance group
    this.backendServiceResourceURL = backendServiceResourceURL; // the url of the backend service of the group (can be undefined)
    this.projectId = projectId;
    this.gceScope = gceScope; // regional or zonal
    this.instancesMap = {}; // maps an instance name to its InstanceHistory
    this.successfulFetch = false;
    this.migName = window.urlToResourceName(migResourceURL);
  }

  isEmpty () {
    return Object.keys(this.instancesMap).length === 0;
  }

  fetchInstancesInfo () {
    var that = this;

    window.getInstancesListRequest(this.projectId, this.gceScope, this.managerResourceURL).then(
      function (response) {
        that.updateInstancesMap_(response.result.managedInstances || []);
        that.successfulFetch = true;
        if (that.backendServiceResourceURL) {
          that.updateHealthStatuses_();
        }
      },
      function (error) {
        console.error('Failed to fetch instances data: ' + error);
      }
    );
  }

  updateHealthStatuses_ () {
    var that = this;

    function handleGetHealthResponse (response) {
      if (!response.result.healthStatus) {
        return;
      }
      var instances = response.result.healthStatus.map(
        data => ({ name: window.urlToResourceName(data.instance), healthState: data.healthState }));

      for (var i = 0; i < instances.length; i++) {
        if (!(instances[i].name in that.instancesMap)) {
          console.warn('We have a missing instance ' + instances[i].name);
          continue;
        }

        that.instancesMap[instances[i].name].setHealthState(instances[i].healthState);
      }
    }

    function handleError (error) {
      console.warn(error);
    }

    window.getInstancesHealthRequest(this.projectId, this.backendServiceResourceURL, this.migResourceURL)
      .then(handleGetHealthResponse, handleError);
  }

  updateInstancesMap_ (instances) {
    var instancesUp = [];
    for (var i = 0; i < instances.length; i++) {
      var inst = window.getInstanceName(instances[i]);
      instancesUp.push(inst);
      if (!(inst in this.instancesMap)) {
        this.instancesMap[inst] = new InstanceHistory(window.getInstanceZone(instances[i]));
      }
      this.instancesMap[inst].consumeInstanceInfo(instances[i]);
    }

    for (var oldInst in this.instancesMap) {
      if (instancesUp.indexOf(oldInst) === -1) {
        this.instancesMap[oldInst].markInstanceAsGone();
      }
    }
  }
};
