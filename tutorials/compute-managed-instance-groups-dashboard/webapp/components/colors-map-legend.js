/* Draws a chart legend (each machine state has its own color). */
window.angular.module('migDashboardApp').component('colorMapLegend', {
  templateUrl: 'components/templates/color-map-legend.html',
  bindings: {
    colorsMap: '<'
  },
  controller: function ($interval) {
    var that = this;

    this.updateColorMapArray = function () {
      that.colorsMapArray = [];
      window.angular.forEach(that.colorsMap, function (value, key) {
        that.colorsMapArray.push({'state': key, 'color': value});
      });
    };

    this.$postLink = function () {
      $interval(this.updateColorMapArray, 300);
    };
  }
});
