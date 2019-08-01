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
const config = require("./client_config.json");
const OPCUAClient = require("./opcua_client.js");
const cloudClient = require("./cloud_iot_client.js");
const Accumulator = require("./data_accumulator.js");

async function run() {
  let opcuaClient = new OPCUAClient();
  let mqttClient;
  try {
    console.log(await opcuaClient.connect());
    console.log(await opcuaClient.createSession());
    let metaData = await getMetaData(opcuaClient);
    if(config.cloudEnabled) {
      mqttClient = await cloudClient.initializeIoTCoreClient();
    }
    let nodeId = await opcuaClient.getNodeIdFrom(config.opcServer.monitorItem.browseName);
    let dataAccumulator =  new Accumulator(config.cloud.messageInterval, generateSendCallback(mqttClient, metaData));
    let changeCallback = getOnMonitorItemChangeCallback(dataAccumulator);
    console.log(await opcuaClient.createSubscription(changeCallback, nodeId));
    await opcuaClient.createMonitorItem(changeCallback, nodeId);

    opcuaClient.subscription.terminate();
    dataAccumulator.runFulfill();

  } catch(err) {
    console.log(err);
  } finally {
    opcuaClient.client.disconnect();
    if (config.cloudEnabled) {
      mqttClient.end();
    }
  }
}

async function getMetaData(opcuaClient) {
  let metaData = {};
  for(let metaBrowseName of config.opcServer.metaData.browseName) {
    let value = await opcuaClient.getVariableValue(metaBrowseName);
    metaData[metaBrowseName] = value;
  }
  return metaData;
}

function generateSendCallback(mqttClient, metaData) {
  return (total, max, min, timestamp, intervalLength) => {
    let message = generateDataMessage(total, max, min, timestamp, intervalLength, metaData);
    if (config.cloudEnabled) {
      if (mqttClient && mqttClient.connected) {
        mqttClient.publish(cloudClient.eventTopic, message, {qos: 1});
      } else {
        console.log('No established cloud connection. Counter value not send.');
      }
    }
    console.log(message);
  };
}

function generateDataMessage(total, max, min, timestamp, intervalLength, metaData) {
  let msgObj = {};
  const keys = Object.keys(metaData);
  for(const key of keys) {
    msgObj[key] = metaData[key];
  }
  msgObj[config.opcServer.monitorItem.browseName] = {
    "total": total,
    "max": max,
    "min": min,
    "interval":  intervalLength,
    "timestamp": timestamp
  };
  return JSON.stringify(msgObj);
}

function formatTime(dateTime) {
  return `${dateTime.getHours()}:${dateTime.getMinutes()}:${dateTime.getSeconds()}.${dateTime.getMilliseconds()}`;
}

function getOnMonitorItemChangeCallback(accumulator) {
  return (dataValue) => {
    console.log(` ${config.opcServer.monitorItem.browseName} = ${dataValue.value.value} at:${formatTime(dataValue.serverTimestamp)}`);
    accumulator.update(dataValue.value.value, dataValue.serverTimestamp);
  };
}

run();