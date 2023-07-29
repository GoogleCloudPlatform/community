import os
import json
import pandas

from flask import Flask, jsonify, redirect, render_template, request

from google.cloud import secretmanager

from alpha_vantage.timeseries import TimeSeries


app = Flask(__name__)

PROJECT_ID = os.environ.get("PROJECTID")

secrets = secretmanager.SecretManagerServiceClient()

ALPHA_VANTAGE_KEY = secrets.access_secret_version(request={"name": "projects/"+PROJECT_ID+"/secrets/alpha-vantage-key/versions/1"}).payload.data.decode("utf-8")


ts = TimeSeries(key=ALPHA_VANTAGE_KEY)

@app.route("/")
def hello():
    return "Hello World!!!"



@app.route('/api/v1/symbol', methods=['POST'])
def get_time_series():
    if request.method == 'POST':
        symbol = request.args['symbol']
        data, metadata = ts.get_intraday(
                symbol, interval='15min', outputsize="25")
    return jsonify(data=data)

if __name__ == "__main__":
    app.debug=True
    app.run()