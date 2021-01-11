# Copyright 2020 Google Inc.
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
import uuid

import apache_beam as beam


PROJECT_ID = os.getenv('PROJECT_ID') 


def to_csv(rowdict):
    import copy
    import hashlib
    # pull columns from BQ and create a line
    CSV_COLUMNS = 'weight_pounds,is_male,mother_age,plurality,gestation_weeks'.split(',')
    
    # create synthetic data where we assume that no ultrasound has been performed
    # and so we don't know sex of the baby. Let's assume that we can tell the difference
    # between single and multiple, but that the errors rates in determining exact number
    # is difficult in the absence of an ultrasound.
    no_ultrasound = copy.deepcopy(rowdict)
    w_ultrasound = copy.deepcopy(rowdict)

    no_ultrasound['is_male'] = 'Unknown'
    if rowdict['plurality'] > 1:
        no_ultrasound['plurality'] = 'Multiple(2+)'
    else:
        no_ultrasound['plurality'] = 'Single(1)'
      
    # Change the plurality column to strings
    w_ultrasound['plurality'] = \
        ['Single(1)', 'Twins(2)', 'Triplets(3)', 'Quadruplets(4)', 'Quintuplets(5)'][rowdict['plurality']-1]
    
    # Write out two rows for each input row, one with ultrasound and one without
    for result in [no_ultrasound, w_ultrasound]:
        data = ','.join([str(result[k]) if k in result else 'None' for k in CSV_COLUMNS])
        key = hashlib.sha224(data.encode('utf-8')).hexdigest()  # hash the columns to form a key
        yield str('{},{}'.format(data, key))


def preprocess(limit, output_dir, job_name, region):
    options = {
        'region': region,
        'staging_location': os.path.join(output_dir, 'tmp', 'staging'),
        'temp_location': os.path.join(output_dir, 'tmp'),
        'job_name': job_name,
        'project': PROJECT_ID,
        'max_num_workers': 3,   # CHANGE THIS IF YOU HAVE MORE QUOTA
        'setup_file': './setup.py'
    }
    opts = beam.pipeline.PipelineOptions(flags=[], **options)
    RUNNER = 'DataflowRunner'
    p = beam.Pipeline(RUNNER, options=opts)
    query = """
SELECT
  weight_pounds,
  is_male,
  mother_age,
  plurality,
  gestation_weeks,
  FARM_FINGERPRINT(CONCAT(CAST(YEAR AS STRING), CAST(month AS STRING))) AS hashmonth
FROM
  publicdata.samples.natality
WHERE year > 2000
AND weight_pounds > 0
AND mother_age > 0
AND plurality > 0
AND gestation_weeks > 0
AND month > 0
    """
  
    if limit:
        query = query + ' LIMIT {}'.format(limit)
  
    for step in ['train', 'eval']:
        if step == 'train':
            selquery = 'SELECT * FROM ({}) WHERE ABS(MOD(hashmonth, 4)) < 3'.format(query)
        else:
            selquery = 'SELECT * FROM ({}) WHERE ABS(MOD(hashmonth, 4)) = 3'.format(query)

        (p 
         | '{}_read'.format(step) >> beam.io.Read(beam.io.BigQuerySource(query=selquery, use_standard_sql=True))
         | '{}_csv'.format(step) >> beam.FlatMap(to_csv)
         | '{}_out'.format(step) >> beam.io.Write(beam.io.WriteToText(os.path.join(output_dir, '{}.csv'.format(step))))
        )

    return p.run()
