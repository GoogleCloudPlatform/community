/*
# Copyright Google Inc. 2018

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

import fs = require('fs');
import jwt = require('jsonwebtoken');

export enum SignAlgorithm {
  ES256 = 'ES256',
  RS256 = 'RS256',
}

export class TokenGenerator {
  private privateKey: Buffer;
  constructor(
    private projectId: string,
    private privateKeyFile: string,
    private algorithm: SignAlgorithm = SignAlgorithm.ES256
  ) {
    this.privateKey = fs.readFileSync(String(this.privateKeyFile));
  }

  create() {
    const token = {
      iat: Number(new Date()) / 1000,
      exp: Number(new Date()) / 1000 + 20 * 60, // 20 minutes
      aud: this.projectId,
    };
    return jwt.sign(token, this.privateKey, {algorithm: this.algorithm});
  }
}
