/* A controller which displays the Summary chart for a MIG; Summary chart groups
 * instances by their current state and shows how many instances there are in
 * each of the groups.
 */
angular.module('migDashboardApp').component('instancesSummaryChart', {
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

        var summaryData = [['Zone' ]];
        for (var i = 0; i < Object.keys(possibleStates).length; i++) {
          summaryData[0].push(Object.keys(possibleStates)[i]);
        }

        for (var i = 0; i < Object.keys(instancesSummary).length; i++) {
          var zone = Object.keys(instancesSummary)[i];
          var row = [zone ];
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

        for (var j = 0; j < Object.keys(possibleStates).length; j++) {
          var state = Object.keys(possibleStates)[j];
          colors.push(that.colorsMap[state]);
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

        var summaryData = [['State', 'Count', { role: 'style' }]];
        for (var i = 0; i < Object.keys(instancesSummary).length; i++) {
          var state = Object.keys(instancesSummary)[i];
          summaryData.push([state, instancesSummary[state], that.colorsMap[state]]);
          that.summaryInfo.push(
            {'state': state, 'count': instancesSummary[state]});
        }
      }

      var summaryDataTable = google.visualization.arrayToDataTable(summaryData);
      var summaryView = new google.visualization.DataView(summaryDataTable);

      var defaults = {
        title: 'Summary',
        legend: { position: 'none' },
        tooltip: {
          trigger: 'none'
        },
        backgroundColor: '#f2f9fc'
      };
      var summaryOptions = $.extend({}, defaults, chartOptions);

      var summaryChart = new google.visualization.ColumnChart(summaryContainer);
      summaryChart.draw(summaryView, summaryOptions);
    };

    this.$postLink = function () {
      var that = this;
      google.charts.setOnLoadCallback(function () {
        that.drawChartIntervalPromise = $interval(that.drawChart, 300);
      });
    };

    this.$onDestroy = function () {
      $interval.cancel(this.drawChartIntervalPromise);
    };
  }
});
