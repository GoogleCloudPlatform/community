#!/usr/bin/env python3

from faker import Faker
from flask import Flask
from google.cloud import pubsub_v1
import datetime
import logging
import os
import random
import uuid


PUBSUB_TOPIC_NAME = 'YOUR_TOPIC_NAME'
PROJECT_ID = 'YOUR_PROJECT_ID'

DEVICE_ID_VALUES = 50000000
TIMESTAMP_RANGE_DAYS = 30

# Number of fields of type string.
RANDOM_STR_FIELDS = 200

# Set and subset size for calculating string permutations based on ascii
# characters from value 97 (character 'a') to value 122 (character 'z').
# PERMUTATION_SET_SIZE and PERMUTATION_SUBSET_SIZE should not be larger than 23
# PERMUTATION_SUBSET_SIZE should be smaller than PERMUTATION_SET_SIZE.
PERMUTATION_SET_SIZE = 7
PERMUTATION_SUBSET_SIZE = 5

# Number of fields of type integer and number of possible random values.
RANDOM_INT_FIELDS = 200
RANDOM_INT_VALUES = 30

# Number of fields of type string that will be nested and number of levels.
# The number of possible values will be taken from RANDOM_STRING_FIELDS.
NESTED_STR_FIELDS = 20
NESTED_STR_LEVELS = 6

# Number of fields of type integer that will be nested and number of levels.
# The number of possible values will be taken from RANDOM_INT_FIELDS.
NESTED_INT_FIELDS = 3
NESTED_INT_LEVELS = 2


# Create Pub/Sub publisher client.
batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=1, max_messages=10
)
publisher = pubsub_v1.PublisherClient(batch_settings)
topic_name = 'projects/{project_id}/topics/{topic}'.format(
    project_id = PROJECT_ID, 
    topic = PUBSUB_TOPIC_NAME
)

# Create Faker client.
fake = Faker()
Faker.seed(0)

# Auxiliary functions to generate random data.
def generate_string(set_size, subset_size):
    string = ''
    for _ in range(subset_size):
        string += chr(fake.random_int(min=97, max=97 + subset_size, step=1))
    return string

def generate_int_field(field_number):
    return {
        'int_field_{}'.format(field_number): fake.random_int(
            min=0, max=RANDOM_INT_VALUES, step=1)
    }

def generate_str_field(field_number):
    return {
        'str_field_{}'.format(field_number): generate_string(
            PERMUTATION_SET_SIZE, PERMUTATION_SUBSET_SIZE)
    }

def generate_nested_int_field(field_number):
    return _generate_nested_int_field(field_number, 0)

def _generate_nested_int_field(field_number, level):
    if level == NESTED_INT_LEVELS:
        return {
            'nested_int_field_{}_level_{}'.format(field_number, level):
            fake.random_int(min=0, max=RANDOM_INT_VALUES, step=1)
        }
    else:
        return {
            'nested_int_field_{}_level_{}'.format(field_number, level):
            _generate_nested_int_field(field_number, level+1)
        } 

def generate_nested_str_field(field_number):
    return _generate_nested_str_field(field_number, 0)

def _generate_nested_str_field(field_number, level):
    if level == NESTED_STR_LEVELS:
        return {
            'nested_str_field_{}_level_{}'.format(field_number, level):
            generate_string(PERMUTATION_SET_SIZE, PERMUTATION_SUBSET_SIZE)
        }
    else:
        return {
            'nested_str_field_{}_level_{}'.format(field_number, level):
            _generate_nested_str_field(field_number, level+1)
        } 

# Main function to create a record with random data.
def fake_record():
    unix_time = fake.unix_time(start_datetime='-30d', end_datetime='now')
    millis = fake.numerify(text='###')
    record = {
        'device_id': fake.random_int(min=0, max=DEVICE_ID_VALUES, step=1),
        'random_timestamp': fake.unix_time(start_datetime='-30d',
            end_datetime='now'),
        'current_timestamp': datetime.datetime.now().timestamp(),
        'row_id': str(uuid.uuid4()),
	'ip': fake.ipv4(),
        'country': fake.country(),
        'user_name': fake.name()
    }

    for field_number in range(0, RANDOM_INT_FIELDS):
        record.update(generate_int_field(field_number))

    for field_number in range(0, RANDOM_STR_FIELDS):
        record.update(generate_str_field(field_number))

    for field_number in range(0, NESTED_INT_FIELDS):
        record.update(generate_nested_int_field(field_number))

    for field_number in range(0, NESTED_STR_FIELDS):
        record.update(generate_nested_str_field(field_number))

    return record

# Publish a message to Pub/Sub.
def publish(message):
    future = publisher.publish(topic_name, str.encode(str(message)))
    print('pubsub published')
    print(future.result())

# Create Flask client.
app = Flask(__name__)

@app.route('/publish', methods=['GET'])
def publish_route():
    record = fake_record()
    publish(record)
    return 'Message published to Pub/Sub {}'.format(record)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
