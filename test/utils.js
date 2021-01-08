/**
 * Copyright 2017, Google, Inc.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';

const childProcess = require(`child_process`);
const path = require('path');

exports.TUTORIALS_PATH = path.join(__dirname, '../tutorials');

exports.FILENAME_REGEXP = /^[a-z0-9-]+\.md$/; // e.g. setting-up-postgres.md
exports.DIR_REGEXP = /^[a-z0-9-]+$/; // e.g. using-nodejs-to-calculate-the-size-of-a-bigquery-dataset
exports.TITLE_REGEXP = /^[a-zA-Z0-9\s.,\-()&:'"/!]+$/; // e.g. How to Set Up PostgreSQL on Compute Engine
exports.DESCRIPTION_REGEXP = /^[a-zA-Z0-9\s.,\-()&#'"/!]+\.$/; // e.g. Learn how to get PostgreSQL running on Compute Engine
exports.GITHUB_REGEXP = /^[a-zA-Z0-9-,]+$/; // e.g. jimtravisgoog
exports.TAGS_REGEXP = /^[a-zA-Z0-9.,#\s-']+$/; // e.g. Compute Engine, PostgreSQL
exports.DATE_REGEXP = /^\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$/; // e.g. 2016-03-31
exports.MEDIUM_REGEXP = /^[a-zA-Z0-9\s]+$/; // e.g. BigQuery
exports.SIZE_REGEXP = /^[0-9.]+\s[A-Z]+$/; // e.g. 15 TB
exports.EMBEDMD_REGEXP = /\[embedmd]:#/g; // e.g. [embedmd]:#

// e.g.
//
// ---
// title: How to Set Up PostgreSQL on Compute Engine
// description: Learn how to get PostgreSQL running on Compute Engine.
// author: jimtravisgoog
// tags: Compute Engine, PostgreSQL
// date_published: 6/3/2016
// ---
exports.TUTORIAL_YAML_REGEXP = /^---\ntitle: (.+)\ndescription: (.+)\nauthor: (.+)\ntags: (.+)\ndate_published: (.+)\n---\n/;

exports.runAsync = (cmd, cwd, cb) => {
  return new Promise((resolve, reject) => {
    childProcess.exec(cmd, { cwd: cwd }, (err, stdout, stderr) => {
      if (err) {
        console.error(err);
        reject(err);
        return;
      }
      if (stdout) {
        stdout = stdout.toString().trim();
      } else {
        stdout = '';
      }
      if (stderr) {
        stderr = stderr.toString().trim();
      } else {
        stderr = '';
      }
      resolve(`${stdout}\n${stderr}`);
    });
  });
};
