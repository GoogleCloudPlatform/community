# -*- coding: utf-8 -*-

# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from flask import Flask, request
from middleware import jwt_authenticated


app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello world service. '


@app.route('/hello-world-service/api/v1/hello', methods=['POST'])
@jwt_authenticated
def hello():
    json_data = request.get_json()
    name = 'World'
    if 'name' in json_data.keys():
        name = json_data['name']
    resp = {
        'message': 'Hello, {}!'.format(name)
    }
    return resp, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
