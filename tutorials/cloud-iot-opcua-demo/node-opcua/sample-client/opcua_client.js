/*
# Copyright Google Inc. 2019
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
*/
const opcua = require("node-opcua");
const config = require("./client_config.json");

module.exports = class OPCUAClientWrapper {

  constructor() {
    this.client = new opcua.OPCUAClient();
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.client.connect(config.opcServer.endpointUrl,function (err) {
        if(err) {
          reject(`Cannot connect to endpoint: ${config.opcServer.endpointUrl}`);
        } else {
          resolve("Connected to OPC-UA server!");
        }
      });
    });
  }

  createSession() {
    return new Promise((resolve, reject) => {
    this.client.createSession((err,session) => {
        if(err) {
          reject(`Failed to establish session with error: ${err}`);
        } else {
          this.opcuaSession = session;
          resolve('Session established!');
        }
      });
    });
  }

  createSubscription(changeCallback, nodeId) {
    this.subscription = new opcua.ClientSubscription(this.opcuaSession,config.opcServer.subscriptionConfig);
    return new Promise((resolve, reject) => {
      this.subscription.on("started",() => {
        resolve(`subscription started for 2 seconds - subscriptionId=${this.subscription.subscriptionId}`);
      }).on("keepalive",() => {
        console.log("keepalive");
      }).on("terminated",() => {});
    });
  }

  createMonitorItem(changeCallback, nodeId) {
    this.monitorItem = this.subscription.monitor({
      nodeId: opcua.resolveNodeId(nodeId),
      attributeId: opcua.AttributeIds.Value
    },
    config.opcServer.monitorItem.config,
    opcua.read_service.TimestampsToReturn.Both
    );
    this.monitorItem.on("changed", changeCallback);
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        resolve();
      },config.opcServer.monitorItem.monitoringTime);
    });
  }

  getNodeIdFrom(browseName) {
    return new Promise((resolve, reject) => {
      this.opcuaSession.translateBrowsePath([opcua.makeBrowsePath("RootFolder",`/Objects/1:${config.opcServer.sensor.browseName}/1:${browseName}`)],
      function (err, results) {
        if (!err
          && results.length > 0
          && results[0].targets[0]
          && results[0].targets[0].targetId) {
            resolve(results[0].targets[0].targetId.toString());
        } else {
          reject(`Unable to get Node with browseName: ${browseName}`);
        }
      });
    });
  }

  readVariableValueBy(nodeId) {
    return new Promise((resolve, reject) => {
      this.opcuaSession.readVariableValue(nodeId,
      function(err, data) {
        if (!err
          && data.value
          && data.value.value) {
            resolve(data.value.value.toString());
        } else {
          reject(`Unable to get value for node with id: ${nodeId}`);
        }
      });
    });
  }

  async getVariableValue(browseName) {
    const nodeId = await this.getNodeIdFrom(browseName);
    return this.readVariableValueBy(nodeId);
  }
}