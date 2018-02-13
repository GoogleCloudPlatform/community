window.angular.module('migDashboardApp').controller('mainController', [
  '$scope', '$timeout',
  function ($scope, $timeout) {
    $scope.showHealthChart = false;
    $scope.migHistoryMap = {};
    $scope.vmMap = undefined;
    $scope.projectList = [];

    $scope.setMessage = function (message, type) {
      $scope.messageForUser = message;
      $scope.messageType = type;
    };

    $scope.initialize = function () {
      $scope.setMessage('Authorizing...', 'loading');

      function onGapiLoaded () {
        window.getInitializeGapiClientRequest()
          .then(window.getSignInRequest)
          .then($scope.getProjectIds)
          .then(
            function () {
              $scope.setMessage();
            },
            function (error) {
              $scope.setMessage(
                error.details || error.error || error, 'error');
            });
      }
      window.gapi.load('client:auth2', onGapiLoaded);
    };

    /* Retrieves a list of project names for typeahead widget. */
    $scope.getProjectIds = function () {
      return window.getProjectsListRequest().then(
        function (response) {
          $scope.setMessage();
          if (response.result.projects) {
            $scope.projectList = response.result.projects.map(
              project => project.projectId
            );
          }
        },
        function (result) {
          throw new Error('Failed to load projects: ' + result.result.error.message);
        });
    };

    $scope.onInstanceGroupManagerSelected = function (projectId, gceScope, igm, migId) {
      if (!(migId in $scope.migHistoryMap)) {
        $scope.migHistoryMap[migId] =
            new window.MigHistory(igm.instanceGroup, igm.name, igm.backendService, projectId, gceScope);
      }
      $scope.vmMap = $scope.migHistoryMap[migId];
      $scope.showHealthChart = igm.backendService !== undefined;
    };

    $scope.fetchInstancesInfo = function () {
      for (var migId in $scope.migHistoryMap) {
        $scope.migHistoryMap[migId].fetchInstancesInfo();
      }
      $timeout($scope.fetchInstancesInfo, 1000);
    };

    $scope.fetchInstancesInfo();
  }
]);
