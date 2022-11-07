# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return 'Home'

@app.route("/run-ip")
def ip():
    response = requests.get('http://checkip.dyndns.org').text
    ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', response)
    return f"The Cloud Run app's external IP address is: {ip[0]}\n"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))