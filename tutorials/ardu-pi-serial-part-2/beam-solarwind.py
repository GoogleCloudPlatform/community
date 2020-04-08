# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import argparse
import logging
import json
from sets import Set

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText

from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.io import BigQueryDisposition

import time
import calendar
import strict_rfc3339


# Set event timestamp from json body
class AddTimestampToDict(beam.DoFn):
    def process(self, element):
        logging.debug('AddTimestampToDict: %s %r' % (type(element), element))
        return [beam.window.TimestampedValue(
            element,
            strict_rfc3339.rfc3339_to_timestamp(element['timestamp']))]


# Emit as KV with the clientid as key
class AddKeyToDict(beam.DoFn):
    def process(self, element):
        logging.debug('AddKeyToDict: %s %r' % (type(element), element))
        return [(element['clientid'], element)]


# BigQuery table schemas
class Schema(object):
    @staticmethod
    def get_warehouse_schema():
        schema_str = ('timestamp:TIMESTAMP, '
                      'clientid:STRING, '
                      'temperature:FLOAT, '
                      'pressure:FLOAT, '
                      'humidity:FLOAT, '
                      'uv:INTEGER, '
                      'airqual:FLOAT, '
                      'windgen:FLOAT, '
                      'solargen:FLOAT')
        return schema_str

    @staticmethod
    def get_avg_schema():
        schema_avg = ('timestamp:TIMESTAMP, '
                      'clientid:STRING, '
                      'temperature:FLOAT, '
                      'pressure:FLOAT, '
                      'humidity:FLOAT, '
                      'uv:FLOAT, '
                      'airqual:FLOAT, '
                      'windgen:FLOAT, '
                      'solargen:FLOAT')
        return schema_avg


# Aggregate for each metric in the window
class CountAverages(beam.DoFn):
    def process(self, element):
        logging.info('CountAverages start: %s %r' % (type(element), element))
        stat_names = ["temperature",
                      "pressure",
                      "humidity",
                      "windgen",
                      "solargen"]

        avg_e = {}
        aggr = {}
        for k in stat_names:
            aggr[k] = (0, 0)

        avg_e['clientid'] = element[0]
        avg_e['timestamp'] = strict_rfc3339.now_to_rfc3339_localoffset()

        # Emit sum and count for each metric
        for elem_map in element[1]:
            for key in stat_names:
                if key in elem_map:
                    value = elem_map[key]
                    aggr[key] = (aggr[key][0] + value, aggr[key][1] + 1)

        # Calculate average and set in return map
        for key, value in aggr.iteritems():
            if value[1] == 0:
                avg_e[key] = 0
            else:
                avg_e[key] = value[0] / value[1]
        logging.info('CountAverages end: {}'.format(avg_e))

        return [avg_e]


def run(argv=None):
    """Build and run the pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--topic',
        type=str,
        default='projects/markku-iot-smartcity/topics/smartcity',
        help='Pub/Sub topic to read from')
    parser.add_argument(
        '--output',
        default='smartcity.greenhouse',
        help=(
            'Output BigQuery table for results specified as: '
            'PROJECT:DATASET.TABLE '
            'or DATASET.TABLE.'))
    parser.add_argument(
        '--output_avg',
        default='smartcity.greenhouse_avg',
        help=(
            'Output BigQuery table for windowed averages specified as: '
            'PROJECT:DATASET.TABLE or DATASET.TABLE.'))

    args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)
    options.view_as(SetupOptions).save_main_session = True
    options.view_as(StandardOptions).streaming = True

    p = beam.Pipeline(options=options)

    records = (p | 'Read from PubSub' >> beam.io.ReadFromPubSub(
        topic=args.topic) | 'Parse JSON to Dict' >> beam.Map(
            json.loads))

    # Write to the warehouse table
    records | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
        args.output,
        schema=Schema.get_warehouse_schema(),
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

    # Compute average in a sliding window and write to BQ average table
    (records | 'Add timestamp' >> beam.ParDo(AddTimestampToDict()) |
     'Window' >> beam.WindowInto(beam.window.SlidingWindows(
         300, 60, offset=0)) |
     'Dict to KeyValue' >> beam.ParDo(AddKeyToDict()) |
     'Group by Key' >> beam.GroupByKey() |
     'Average' >> beam.ParDo(CountAverages()) |
     'Write Avg to BigQuery' >> beam.io.WriteToBigQuery(
         args.output_avg,
         schema=Schema.get_avg_schema(),
         create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
         write_disposition=BigQueryDisposition.WRITE_APPEND))

    result = p.run()
    result.wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
