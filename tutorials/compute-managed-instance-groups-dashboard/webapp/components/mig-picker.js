/* A controller which allows the user to choose the project and the MIG to be
 * monitored. */
window.angular.module('migDashboardApp').component('migPicker', {
  templateUrl: 'components/templates/mig-picker.html',
  bindings: {
    onMigSelected: '&',
    projectList: '<',
    messageFunction: '<'
  },
  controller: function () {
    /*
     * Describes how many projects should be shown in the drop down when the
     * user is typing a project name.
     */
    this.maxTypeaheadHints = 10;

    /*
     * A list of all managers for a certain project the user has chosen.
     */
    this.instanceGroupManagers = undefined;

    /*
     * A boolean variable used to collapse mig-picker widget.
     */
    this.expandPicker = true;

    var that = this;

    this.filter = function (namePrefix, numberOfResults) {
      var results = [];
      for (var i = 0; i < that.projectList.length; i++) {
        if (that.projectList[i].indexOf(namePrefix) > -1) {
          results.push(that.projectList[i]);
        }
        if (results.length >= numberOfResults) {
          break;
        }
      }
      return results;
    };

    /* Run when the user clicks on a specific instance group;
     * sets this group as the default. */
    this.onInstanceGroupManagerSelected = function (gceScope, igm) {
      var migId = that.projectId + '/' + igm.name + '/' + gceScope;
      that.expandPicker = false;
      that.onMigSelected({
        projectId: that.projectId,
        gceScope: gceScope,
        igm: igm,
        migId: migId
      });
    };

    this.getInstanceGroupManagersFromResponse = function (response) {
      var igms = {};
      for (var gceScopeName in response.items) {
        var gceScope = response.items[gceScopeName];
        var instanceGroupManagers = gceScope.instanceGroupManagers;
        if (!instanceGroupManagers) {
          continue;
        }
        igms[gceScopeName] = instanceGroupManagers;
      }
      return igms;
    };

    this.getMigToBackendServiceMapFromResponse = function (response) {
      var migBackendMap = {};
      var backendServices = response.items || [];
      for (var i = 0; i < backendServices.length; i++) {
        if (backendServices[i].backends !== undefined) {
          for (var j = 0; j < backendServices[i].backends.length; j++) {
            var migName =
                window.urlToResourceName(backendServices[i].backends[j].group);
            migBackendMap[migName] = backendServices[i].name;
          }
        }
      }
      return migBackendMap;
    };

    this.addBackendServiceInfo = function (igms, migBackendMap) {
      Object.keys(igms).forEach(function (gceScopeName) {
        var igmList = igms[gceScopeName];
        for (var i = 0; i < igmList.length; i++) {
          igmList[i].backendService =
              (igmList[i].name in migBackendMap) ? migBackendMap[igmList[i].name] : undefined;
        }
      });
      return igms;
    };

    this.loadInstanceGroups = function (projectId) {
      that.messageFunction('Loading your instance groups...', 'loading');
      window.getInstanceGroupManagersListRequest(projectId)
        .then(function (response) {
          that.instanceGroupManagers =
              that.getInstanceGroupManagersFromResponse(response.result);
          that.projectId = projectId;
        })
        .then(function () { return window.getBackendServicesListRequest(projectId); })
        .then(function (response) {
          var migBackendMap = that.getMigToBackendServiceMapFromResponse(response.result);
          that.instanceGroupManagers =
              that.addBackendServiceInfo(that.instanceGroupManagers, migBackendMap);
          that.messageFunction();
        },
        function (response) {
          that.messageFunction(
            'Failed to load instance groups: ' +
                response.result.error.message +
                '. Maybe you don\'t have any instance groups in your project?',
            'error');
        });
    };
  }
});
