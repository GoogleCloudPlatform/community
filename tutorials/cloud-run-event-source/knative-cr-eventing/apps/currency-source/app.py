#!/usr/bin/env python

import os
import json
import requests

from pathlib import Path  # python3 only

from google.cloud import secretmanager

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.foreignexchange import ForeignExchange


#sink_url = os.environ['SINK']+'/curerncy'
sink_url = os.environ['SINK']

PROJECT_ID = os.environ['PROJECT_ID']

ALPHAVANTAGE_KEY = secrets.access_secret_version("projects/"+PROJECT_ID+"/secrets/alpha-vantage-key/versions/1").payload.data.decode("utf-8")


ts = TimeSeries(key=ALPHAVANTAGE_KEY)


def make_msg(message):
    msg = '{"msg": "%s"}' % (message)
    return msg

def get_goog():
    data, meta_data = ts.get_intraday('GOOG')
    return data, meta_data



#if __name__ == "__main__":
#    app.debug=True
#    app.run()

headers = {'Content-Type': 'application/cloudevents+json'}

while True:
    body = get_goog()
    requests.post(sink_url, data=json.dumps(body), headers=headers)
    time.sleep(15)