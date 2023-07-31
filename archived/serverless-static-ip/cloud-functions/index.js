// Copyright 2021 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const http = require('http');

exports.function_ip = (req, res) => {
  http.get('http://checkip.dyndns.org', response => {
    let data = '';
    response.on('data', d => {
      data += d;
    });
    response.on('end', () => {
      const regexp = RegExp('[0-9]+(?:.[0-9]+){3}', 'g');
      let ip = regexp.exec(data);
      res.status(200).send(`The Cloud Function's external IP address is: ${ip}\n`);
    });
  });
};
