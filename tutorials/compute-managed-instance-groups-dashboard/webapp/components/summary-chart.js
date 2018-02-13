/* A controller which displays the Summary chart for a MIG; Summary chart groups
 * instances by their current state and shows how many instances there are in
 * each of the groups.
 */
window.angular.module('migDashboardApp').component('instancesSummaryChart', {
  templateUrl: 'components/templates/summary-chart.html',
  bindings: {
    colorsMap: '<',
    historyMap: '<',
    groupByZone: '<'
  },
  controller: function ($interval) {
    this.$onInit = function () {
      if (this.containerId === undefined) {
        /* Id of the DOM element that Google Charts Timeline will render in. */
        this.containerId = 'instances-chart-' + Date.now();
      }
    };

    var that = this;

    that.drawChart = function () {
      if (!that.historyMap) {
        return;
      }
      var summaryContainer = document.getElementById(that.containerId);
      var instancesSummary = {};
      var instancesNames = Object.keys(that.historyMap);
      var chartOptions = {};
      that.summaryInfo = [];

      var summaryData = [];
      if (that.groupByZone) {
        var possibleStates = {};
        var colors = [];

        instancesNames.forEach(function (vmId) {
          var state = that.historyMap[vmId].timeline[0].state;
          var zone = that.historyMap[vmId].zone;
          if (!(zone in instancesSummary)) {
            instancesSummary[zone] = {};
          }
          if (state === 'gone') { return; }

          if (state in instancesSummary[zone]) {
            instancesSummary[zone][state] += 1;
          } else {
            instancesSummary[zone][state] = 1;
          }
          possibleStates[state] = true;
        });

        summaryData = [['Zone']];
        Object.keys(possibleStates).forEach(
          function (possibleState) { summaryData[0].push(possibleState); });

        for (var i = 0; i < Object.keys(instancesSummary).length; i++) {
          var zone = Object.keys(instancesSummary)[i];
          var row = [zone];
          for (var j = 0; j < Object.keys(possibleStates).length; j++) {
            var state = Object.keys(possibleStates)[j];
            row.push(instancesSummary[zone][state]);
            that.summaryInfo.push({
              'zone': zone,
              'state': state,
              'count': instancesSummary[zone][state] === undefined ? 0 : instancesSummary[zone][state],
              'possibleStates': Object.keys(possibleStates).length
            });
          }
          summaryData.push(row);
        }

        for (var k = 0; k < Object.keys(possibleStates).length; k++) {
          var possibleState = Object.keys(possibleStates)[k];
          colors.push(that.colorsMap[possibleState]);
        }
        chartOptions['colors'] = colors;
      } else {
        instancesNames.forEach(function (vmId) {
          var state = that.historyMap[vmId].timeline[0].state;
          if (state === 'gone') { return; }
          if (state in instancesSummary) {
            instancesSummary[state] += 1;
          } else {
            instancesSummary[state] = 1;
          }
        });

        summaryData = [['State', 'Count', { role: 'style' }]];
        Object.keys(instancesSummary).forEach(
          function (state) {
            summaryData.push([state, instancesSummary[state], that.colorsMap[state]]);
            that.summaryInfo.push(
              { 'state': state, 'count': instancesSummary[state] });
          });
      }

      var summaryDataTable = window.google.visualization.arrayToDataTable(summaryData);
      var summaryView = new window.google.visualization.DataView(summaryDataTable);

      var defaults = {
        title: 'Summary',
        legend: { position: 'none' },
        tooltip: {
          trigger: 'none'
        },
        backgroundColor: '#f2f9fc'
      };
      var summaryOptions = window.$.extend({}, defaults, chartOptions);

      var summaryChart = new window.google.visualization.ColumnChart(summaryContainer);
      summaryChart.draw(summaryView, summaryOptions);
    };

    this.$postLink = function () {
      var that = this;
      window.google.charts.setOnLoadCallback(function () {
        that.drawChartIntervalPromise = $interval(that.drawChart, 300);
      });
    };

    this.$onDestroy = function () {
      $interval.cancel(this.drawChartIntervalPromise);
    };
  }
});
