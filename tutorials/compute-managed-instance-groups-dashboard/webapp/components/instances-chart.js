/* Controller which draws the Timeline chart from Google Charts and
 * post-processes the chart to add additional elements which aren't available by default in the library.
 */
window.angular.module('migDashboardApp').component('instancesChart', {
  templateUrl: 'components/templates/instance-chart.html',
  bindings: {
    colorsMap: '<',
    historyMap: '<',
    instancesOrder: '<',
    groupByZone: '<',
    timespan: '<',
    containerId: '@' /* Id of the DOM element that Google Charts Timeline will render in. */
  },
  controller: function ($interval) {
    /* A list of colors to be used to mark different machine states. */
    this.availableColors =
    ['#3366CC', '#1D3C5B', '#6633CC', '#5574A6', '#22AA99', '#0099C6',
      '#FF9900', '#3B3EAC', '#d35e0a', '#0b6811', '#8B0707', '#600060',
      '#ad5701'];

    var that = this;

    /* Draw vertical red line, that marks the beginning of time. */
    this.drawVerticalRedLine = function (svg, gTags) {
      var children = gTags[0].children;
      var pathsToModify = [];
      for (var i = 0; i < children.length; i++) {
        var tableChild = children[i];
        if (tableChild.tagName === 'rect') {
          if (i + 2 < children.length && children[i + 2].tagName === 'path') {
            pathsToModify.push(children[i + 2]);
          }
        }
      }
      for (var j = 0; j < pathsToModify.length; j++) {
        if (!pathsToModify[j]) continue;
        pathsToModify[j].setAttribute('class', 'redLine');
        pathsToModify[j].setAttribute('id', 'nowPath' + j + that.containerId);

        // move to front
        var useSVG = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        useSVG.setAttributeNS(
          'http://www.w3.org/1999/xlink', 'href', '#nowPath' + j + that.containerId);
        svg.appendChild(useSVG);
      }
    };

    /* Replace the default label for time axis beginning (0:00) wit styled word
     * 'now'.
     */
    this.drawRedNow = function (svg) {
      var textTags = Array.from(svg.getElementsByTagName('text'));
      for (var $i = 0; $i < textTags.length; $i++) {
        if (textTags[$i].textContent === '0:00') {
          textTags[$i].textContent = 'Now';
          textTags[$i].setAttribute('class', 'redBoldText');
        } else if (
          textTags[$i].textContent.startsWith('59:') ||
            textTags[$i].textContent === '0:01') {
          textTags[$i].textContent = '';
        }
      }
    };

    /* Change backgrounds of groups of rows to distinguish VMs that live in
     * common zone with the same color.
     */
    this.drawGroupByHighlights = function (gTags) {
      const highlightColorsCount = 3;
      if (!that.groupByZone) {
        return;
      }
      var zoneSizes = [{zone: '', size: 0}];
      for (var k = 0; k < that.instancesOrder.length; k++) {
        var zone = that.historyMap[that.instancesOrder[k]].zone;
        if (zoneSizes.slice(-1)[0].zone !== zone) {
          zoneSizes.push({zone: zone, size: 0});
        }
        zoneSizes.slice(-1)[0].size++;
      }
      zoneSizes.shift();

      var rects = gTags[0].getElementsByTagName('rect');
      var currentRect = 0;
      for (var i = 0; i < zoneSizes.length; i++) {
        for (var j = 0; j < zoneSizes[i].size; j++) {
          if (!rects[currentRect]) continue;
          rects[currentRect++].setAttribute(
            'class',
            'overlayHighlightColor' + (i % highlightColorsCount + 1));
        }
      }
    };

    this.addOverlays = function () {
      var container = document.getElementById(that.containerId);
      var svg = container.getElementsByTagName('svg')[0];
      var gTags = Array.from(svg.getElementsByTagName('g'));

      that.drawVerticalRedLine(svg, gTags);
      that.drawRedNow(svg);
      that.drawGroupByHighlights(gTags);
    };

    this.prepareDataTable = function () {
      var dataTable = new window.google.visualization.DataTable();
      dataTable.addColumn({type: 'string', id: 'Name'}); // row label
      dataTable.addColumn({type: 'string', id: 'State'}); // bar label
      dataTable.addColumn({type: 'date', id: 'Start'});
      dataTable.addColumn({type: 'date', id: 'End'});

      for (var i = 0; i < that.instancesOrder.length; i++) {
        var vmId = that.instancesOrder[i];
        var vmStates = that.historyMap[vmId].timeline;
        var currentTime = Date.now();
        var prevTimestamp = currentTime + 4000;
        for (var j = 0; j < vmStates.length; j++) {
          var state = vmStates[j].state;
          var timestamp = vmStates[j].timestamp;

          var start = Math.floor((currentTime - prevTimestamp) / 1000);
          var end =
              Math.min(that.timespan, Math.floor((currentTime - timestamp) / 1000));
          if (start >= end) {
            continue;
          }
          if (vmStates[j].state !== 'gone') {
            var label = '';
            if (that.historyMap[vmId].error) {
              label += ' \u26A0'; // show a warning sign when there is an error
            }
            dataTable.addRow([
              vmId + label,
              state,
              new Date(0, 0, 0, 0, 0, start),
              new Date(0, 0, 0, 0, 0, end)
            ]);
          }
          prevTimestamp = timestamp;
        }
      }

      return dataTable;
    };

    /* How to choose color for each segment of each timeline
       bar. */
    this.getColorList = function (dataTable) {
      var colors = [];
      for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
        var state = dataTable.getValue(i, 1);
        if (!(state in that.colorsMap)) {
          if (that.availableColors.length > 0) {
            that.colorsMap[state] = that.availableColors[0];
            that.availableColors.splice(0, 1);
          } else {
            that.colorsMap[state] = '#BBBBBB';
            console.warn('run out of colors');
          }
        }
        var color = that.colorsMap[state];
        if (colors.indexOf(color) === -1) {
          colors.push(color);
        }
      }
      return colors;
    };

    /* The following code is used only to calculate the appropriate height of
     * the chart. It is defined by how many rows are visible at a certain
     * moment in time + some margin. `dataTable` holds multiple rows for each
     * timeline bar, so we need to merge those into a single chart row. If the
     * start moment of a machine does not fit in our range anymore, the row is
     * not visible.
     */
    this.calculateChartHeight = function (dataTable) {
      var visibleRows = 0;
      var distinctMachines = {};
      for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
        var machine = dataTable.getValue(i, 0);
        var start = dataTable.getValue(i, 2);
        if (machine in distinctMachines) {
          distinctMachines[machine] =
              Math.min(distinctMachines[machine], start);
        } else {
          distinctMachines[machine] = start;
        }
      }

      for (var distinctMachine in distinctMachines) {
        var machineStart = distinctMachines[distinctMachine];
        if (machineStart <= that.timespan) visibleRows += 1;
      }

      var paddingHeight = 50; // set a padding value to cover the height of
      // title and axis values
      var rowHeight =
          visibleRows * 32; // set the height to be covered by the rows
      return rowHeight + paddingHeight;
    };

    this.drawChart = function () {
      if (!that.instancesOrder) {
        return;
      }

      var dataTable = that.prepareDataTable();

      var options = {
        hAxis: {
          format: 'm:ss',
          minValue: new Date(0, 0, 0, 0, 0, -4),
          maxValue: new Date(0, 0, 0, 0, 0, that.timespan)
        },
        timeline: {
          showBarLabels: false,
          barLabelStyle: {
            fontSize: 9
          }
        },
        tooltip: {
          trigger: 'none'
        },
        colors: that.getColorList(dataTable),
        avoidOverlappingGridLines: false,
        height: that.calculateChartHeight(dataTable),
        backgroundColor: '#f2f9fc'
      };

      var instanceHistoryContainer = document.getElementById(that.containerId);
      var instanceHistoryChart =
          new window.google.visualization.Timeline(instanceHistoryContainer);
      window.google.visualization.events.addListener(
        instanceHistoryChart, 'ready', that.addOverlays.bind(that));
      instanceHistoryChart.draw(dataTable, options);
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
