// Copyright 2021 Google, LLC.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const express = require('express');
const app = express();

const { ExecutionsClient } = require('@google-cloud/workflows');
const client = new ExecutionsClient();

const { HTTP } = require('cloudevents');
const { toLogEntryData } = require('@google/events/cloud/audit/v1/LogEntryData');

const GOOGLE_CLOUD_PROJECT = process.env.GOOGLE_CLOUD_PROJECT;
const WORKFLOW_REGION = process.env.WORKFLOW_REGION;
const WORKFLOW_NAME = process.env.WORKFLOW_NAME;

app.use(express.json());
app.post('/', async (req, res) => {
  const cloudEvent = HTTP.toEvent({ headers: req.headers, body: req.body });
  console.log('Received CloudEvent:');
  console.log(cloudEvent);

  // "protoPayload" : {"resourceName":"projects/_/buckets/events-atamel-images-input/objects/atamel.jpg}";
  const logEntryData = toLogEntryData(cloudEvent.data);
  console.log(logEntryData);

  const tokens = logEntryData.protoPayload.resourceName.split('/');
  const bucket = tokens[3];
  const file = tokens[5];

  try {
    console.log(`Workflow path: ${GOOGLE_CLOUD_PROJECT}, ${WORKFLOW_REGION}, ${WORKFLOW_NAME}`);
    const execResponse = await client.createExecution({
      parent: client.workflowPath(GOOGLE_CLOUD_PROJECT, WORKFLOW_REGION, WORKFLOW_NAME),
      execution: {
        argument: JSON.stringify({ bucket: bucket, file: file })
      }
    });
    console.log(`Execution response: ${JSON.stringify(execResponse)}`);

    const execName = execResponse[0].name;
    console.log(`Created execution: ${execName}`);

    res.status(200).send(`Created execution: ${execName}`);
  } catch (e) {
    console.error(`Error executing workflow: ${e}`);
    res.status(500).send(`Error executing workflow: ${e}`);
    throw e;
  }
});

module.exports = app;
