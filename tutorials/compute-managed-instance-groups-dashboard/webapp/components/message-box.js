/* Allows to show a message alert for certain message type */
window.angular.module('migDashboardApp').component('messageBox', {
  templateUrl: 'components/templates/message-box.html',
  bindings: {
    message: '<',
    type: '<'
  },
  controller: function () {
    var that = this;

    this.getClass = function () {
      switch (that.type) {
        case 'error':
          return 'alert alert-danger';
        case 'warning':
          return 'alert alert-warning';
        default:
          return 'alert alert-info';
      }
    };
  }
});
