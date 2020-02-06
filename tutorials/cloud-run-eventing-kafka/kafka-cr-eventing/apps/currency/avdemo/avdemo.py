import uuid
import pandas

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.foreignexchange import ForeignExchange
from confluent_kafka import Producer, Consumer
from flask import jsonify

class AlphaKafka(object):

    def __init__(self, host, ckey, csecret, akey):
        self.host = host
        self.key = ckey
        self.secret = csecret
        #self.producer = KafkaProducer(bootstrap_servers=self.host)
        self.p = Producer({
            'bootstrap.servers': host,
            'broker.version.fallback': '0.10.0.0',
            'api.version.fallback.ms': 0,
            'sasl.mechanisms': 'PLAIN',
            'security.protocol': 'SASL_SSL',
            'sasl.username': ckey,
            'sasl.password': csecret,
        })
        self.c = Consumer({
            'bootstrap.servers': host,
            'broker.version.fallback': '0.10.0.0',
            'api.version.fallback.ms': 0,
            'sasl.mechanisms': 'PLAIN',
            'security.protocol': 'SASL_SSL',
            'sasl.username': ckey,
            'sasl.password': csecret,
            # this will create a new consumer group on each invocation.
            'group.id': str(uuid.uuid1()),
            'auto.offset.reset': 'earliest'
        })
        self.ts = TimeSeries(key=akey, output_format='pandas')
        self.fx = ForeignExchange(key=akey)


    def acked(self, err, msg):
        """Delivery report callback called (from flush()) on successful or failed delivery of the message."""
        if err is not None:
            report = "failed to deliver message: {}".format(err.str())
        else:
            report = "produced to: {} [{}] @ {}".format(
                msg.topic(), msg.partition(), msg.offset())
        return report


    def produce(self, topic, message):
        client = self.p
        msg = client.produce(topic, value=message, callback=self.acked)
        return msg


    def timeseries(self, symbol):
        client = self.ts
        data, metadata = client.get_intraday(
            symbol, interval='15min', outputsize='compact')
        return data, metadata
        #return data.head(2)
        #return jsonify(data=data, metatdata=metadata)

    def curex(self, curr1, curr2):
        client = self.fx
        data, _ = client.get_currency_exchange_rate(
            from_currency=curr1, to_currency=curr2)
        return data
        #return data.head(2)
        #return jsonify(data=data, metatdata=metadata)
