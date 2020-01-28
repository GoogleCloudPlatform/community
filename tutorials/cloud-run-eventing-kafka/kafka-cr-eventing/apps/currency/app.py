import os
import json

from flask import Flask, jsonify, redirect, render_template, request

from pathlib import Path  # python3 only

from avdemo.avdemo import AlphaKafka

app = Flask(__name__)


CONFLUENT_HOST = os.environ.get("CONFLUENT_HOST")
CONFLUENT_KEY = os.environ.get("CONFLUENT_KEY")
CONFLUENT_SECRET = os.environ.get("CONFLUENT_SECRET")
ALPHAVANTAGE_KEY = os.environ.get("ALPHAVANTAGE_KEY")



origin = AlphaKafka(CONFLUENT_HOST, CONFLUENT_KEY, CONFLUENT_SECRET, ALPHAVANTAGE_KEY)

@app.route("/")
def hello():
    return "Hello World!"



@app.route('/api/v1/currency', methods=['POST'])
def get_exchange_rate():
    if request.method == 'POST':
        curr1 = request.args['currency1']
        curr2 = request.args['currency2']
        exchange = origin.curex(curr1, curr2)
        exchangeObj = json.dumps(exchange)
        exrate = float(exchange['5. Exchange Rate'])
        if exrate > 105.00:
            resp = origin.produce("cloudevents", str(
                exchange['5. Exchange Rate']))
            return jsonify(ping="higher", message=exrate)
        else:
            return jsonify(ping="lower", message=exrate)

    else:
        return "Error"



if __name__ == "__main__":
    app.debug=True
    app.run()
