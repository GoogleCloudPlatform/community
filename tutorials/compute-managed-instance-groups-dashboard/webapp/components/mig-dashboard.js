/* A controller which is responsible for showing the charts with legends for a given MIG and
  updating it every time the data changes. */
window.angular.module('migDashboardApp').component('migDashboard', {
  templateUrl: 'components/templates/mig-dashboard.html',
  bindings: {
    messageFunction: '<',
    vmMap: '<',
    showHealthChart: '<'
  },
  controller: function ($scope) {
    var that = this;

    this.timespan = 180; // a default "length" of the timeline chart
    this.vmMap = null; // a MigHistory object containing the state of currently chosen group
    this.groupByZone = false; // indicates if we want to show machines in a common zone next to each other

    /* The default colors to be used for most common machine states. */
    this.colorsMap = {
      'CREATING': '#66AA00',
      'DELETING': '#DC3912',
      'RESTARTING': '#994499',
      'RECREATING': '#E67300'
    };

    /* The default colors to be used for machine health information charting. */
    this.colorsHealthMap = {
      'HEALTHY': '#109618',
      'UNHEALTHY': '#DC3912',
      'UNKNOWN': '#BBBBBB'
    };

    /* A helper map which is created based on vmMap;
    it contains only the information needed to create an instance state chart.
    Updated whenever vmMap changes by recomputeVmStateAndHealthHistory. */
    this.vmStateHistory = {};

    /* Another helper map created from vmMap; contains info for health charts.
    Updated by recomputeVmStateAndHealthHistory whenever vmMap changes. */
    this.vmHealthHistory = {};

    /* A list of instance names in the order in which we want to chart them, starting from top.
     Updated when vmMap changes or groupByZone changes in sortInstanceNames.
     */
    this.instancesOrder = [];

    /* Sorts instances and updates instancesOrder list.
     * Instances are ordered by:
     *   1. zone, if groupByZone is checked
     *   2. template, instances in 'newer' template (presumably the one MIG is
     *      being updated to) are further in the list
     *   3. currentAction, as defined by actionPrecedence list
     *   4. how long they've been staying in their most recent currentAction
     */
    this.sortInstanceNames = function (vmMap, groupByZone) {
      function getPropertyValueWithTimestamp (instanceHistory, propertyName) {
        var history = instanceHistory.history;
        for (var i = 0; i < history.length; i++) {
          if (!history[i][propertyName]) {
            continue;
          }

          var value = history[i][propertyName];
          var j = i + 1;
          while (j < history.length && history[j][propertyName] === value) {
            j++;
          }
          return {
            value: value,
            timestamp: history[j - 1].timestamp
          };
        }
        return {
          value: undefined,
          timestamp: Date.now()
        };
      }

      function findTemplatePrecedence (instancesMap) {
        var templateAppearTimes = {};
        for (var instanceName in instancesMap) {
          var template = getPropertyValueWithTimestamp(instancesMap[instanceName], 'template');
          if (!(template.value in templateAppearTimes) ||
              templateAppearTimes[template.value] > template.timestamp) {
            templateAppearTimes[template.value] = template.timestamp;
          }
        }
        var templateAppearOrder = Object.keys(templateAppearTimes);
        templateAppearOrder.sort(function (template1, template2) {
          return templateAppearTimes[template1] - templateAppearTimes[template2];
        });
        return templateAppearOrder;
      }

      var instancesNames = vmMap === null ? [] : Object.keys(vmMap.instancesMap);
      instancesNames.sort(function (vm1Id, vm2Id) {
        var vm1 = vmMap.instancesMap[vm1Id];
        var vm2 = vmMap.instancesMap[vm2Id];

        if (groupByZone && vm1.zone !== vm2.zone) {
          return vm1.zone < vm2.zone ? -1 : 1;
        }

        var t1 = getPropertyValueWithTimestamp(vm1, 'template').value;
        var t2 = getPropertyValueWithTimestamp(vm2, 'template').value;

        if (t1 !== t2) {
          var templatePrecedence = findTemplatePrecedence(vmMap.instancesMap);
          return templatePrecedence.indexOf(t1) - templatePrecedence.indexOf(t2);
        }

        var action1 = getPropertyValueWithTimestamp(vm1, 'currentAction');
        var action2 = getPropertyValueWithTimestamp(vm2, 'currentAction');
        if (action1.value !== action2.value) {
          var actionPrecedence = ['CREATING', 'NONE', 'RESTARTING', 'DELETING', 'gone'];
          return actionPrecedence.indexOf(action1.value) - actionPrecedence.indexOf(action2.value);
        }
        return action2.timestamp - action1.timestamp;
      });
      that.instancesOrder = instancesNames;
    };

    this.getInstanceState_ = function (instanceHistoryElement) {
      if (instanceHistoryElement.currentAction === 'NONE') {
        return instanceHistoryElement.template;
      }
      return instanceHistoryElement.currentAction;
    };

    this.recomputeVmStateAndHealthHistory = function () {
      if (that.vmMap === null || !that.vmMap.successfulFetch) {
        this.messageForUser = 'Wating for instance group data...';
        this.messageType = 'loading';
        return;
      }

      if (that.vmMap.isEmpty()) {
        this.messageForUser = 'Selected instance group is empty.';
        this.messageType = 'warning';
        return;
      }

      this.messageForUser = this.messageType = '';

      that.vmStateHistory = {};
      that.vmHealthHistory = {};
      for (var vmId in that.vmMap.instancesMap) {
        that.vmStateHistory[vmId] = {
          error: that.vmMap.instancesMap[vmId].error,
          zone: that.vmMap.instancesMap[vmId].zone,
          timeline: that.vmMap.instancesMap[vmId].history.map(
            element => ({ state: that.getInstanceState_(element), timestamp: element.timestamp }))
        };
        that.vmHealthHistory[vmId] = {
          error: that.vmMap.instancesMap[vmId].error,
          zone: that.vmMap.instancesMap[vmId].zone,
          timeline: that.vmMap.instancesMap[vmId].history.map(
            element => ({ state: element.healthState, timestamp: element.timestamp }))
        };
      }
      that.sortInstanceNames(that.vmMap, that.groupByZone);
    };

    $scope.$watch(
      function () {
        return that.vmMap;
      },
      function () {
        that.recomputeVmStateAndHealthHistory();
      },
      true);

    $scope.$watch(
      function () {
        return that.groupByZone;
      },
      function () {
        that.sortInstanceNames(that.vmMap, that.groupByZone);
      },
      true);
  }
});
