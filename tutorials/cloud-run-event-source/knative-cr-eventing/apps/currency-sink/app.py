import os
import json
import logging
import time

from flask import Flask, jsonify, redirect, render_template, request, Response

from google.cloud import secretmanager


app = Flask(__name__)

def info(msg):
    app.logger.info(msg)

stock = []

@app.route('/')
def default_route():    
    return stock[-1]


@app.route('/currency/', methods=['POST'])
def currency_route():
    if request.method == 'POST':
        content = request.data.decode('utf-8')
        info(f'Event Display received event: {content}')
        stock.append(stock)
        return jsonify(hello=str(content))
    else:

    #app.logger.debug(‘this is a DEBUG message’)
    #app.logger.info(‘this is an INFO message’)
    #app.logger.warning(‘this is a WARNING message’)
    #app.logger.error(‘this is an ERROR message’)
    #app.logger.critical(‘this is a CRITICAL message’)
        return jsonify('hello world')


#if __name__ == "__main__":
#    app.debug=True
#    app.run()

if __name__ != '__main__':
    # Redirect Flask logs to Gunicorn logs
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    info('Event Display starting')
else:
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))