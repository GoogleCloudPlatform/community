"use strict";
/**
 * Copyright 2018 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const fs = require("fs");
const jwt = require("jsonwebtoken");
var SignAlgorithm;
(function (SignAlgorithm) {
    SignAlgorithm["ES256"] = "ES256";
    SignAlgorithm["RS256"] = "RS256";
})(SignAlgorithm = exports.SignAlgorithm || (exports.SignAlgorithm = {}));
class TokenGenerator {
    constructor(projectId, privateKeyFile, algorithm = SignAlgorithm.ES256) {
        this.projectId = projectId;
        this.privateKeyFile = privateKeyFile;
        this.algorithm = algorithm;
        this.privateKey = fs.readFileSync(String(this.privateKeyFile));
    }
    create() {
        let token = {
            'iat': Number(new Date()) / 1000,
            'exp': Number(new Date()) / 1000 + (20 * 60),
            'aud': this.projectId
        };
        return jwt.sign(token, this.privateKey, { algorithm: this.algorithm });
    }
}
exports.TokenGenerator = TokenGenerator;
