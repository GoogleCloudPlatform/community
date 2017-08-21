#  Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""DNNRegressor with custom estimator for abalone dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import argparse
import multiprocessing

import six

import numpy as np

import tensorflow as tf
from tensorflow.python.estimator.model_fn import ModeKeys as Modes
from tensorflow.contrib.keras.python.keras.layers import Dense

from tensorflow.contrib.learn import learn_runner
from tensorflow.contrib.learn.python.learn.utils import (saved_model_export_utils)
from tensorflow.contrib.training.python.training import hparam

tf.logging.set_verbosity(tf.logging.INFO)

CSV_COLUMNS = [
    'length', 'diameter', 'height', 'whole_weight', 'shucked_weight',
    'viscera_weight', 'shell_weight', 'num_rings'
]
CSV_COLUMN_DEFAULTS = [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0]]

PREDICTED_COLUMN = 'num_rings'
INPUT_COLUMNS = [
    tf.feature_column.numeric_column('length'),
    tf.feature_column.numeric_column('diameter'),
    tf.feature_column.numeric_column('height'),
    tf.feature_column.numeric_column('whole_weight'),
    tf.feature_column.numeric_column('shucked_weight'),
    tf.feature_column.numeric_column('viscera_weight'),
    tf.feature_column.numeric_column('shell_weight'),
]

UNUSED_COLUMNS = set(CSV_COLUMNS) - {col.name for col in INPUT_COLUMNS} - {PREDICTED_COLUMN}

def parse_csv(rows_string_tensor):
    columns = tf.decode_csv(rows_string_tensor, record_defaults=CSV_COLUMN_DEFAULTS)
    features = dict(zip(CSV_COLUMNS, columns))

    for col in UNUSED_COLUMNS:
        features.pop(col)

    for key, value in six.iteritems(features):
        features[key] = tf.expand_dims(features[key], -1)
    return features

def generate_input_fn(filenames,
                      num_epochs=None,
                      shuffle=True,
                      skip_header_lines=0,
                      batch_size=64):
  
    def _input_fn():
  
        filename_queue = tf.train.string_input_producer(filenames, num_epochs=num_epochs, shuffle=shuffle)
        reader = tf.TextLineReader(skip_header_lines=skip_header_lines)

        _, rows = reader.read_up_to(filename_queue, num_records=batch_size)

        features = parse_csv(rows)

        if shuffle:
            features = tf.train.shuffle_batch(
                features,
                batch_size,
                min_after_dequeue=2 * batch_size + 1,
                capacity=batch_size * 10,
                num_threads=multiprocessing.cpu_count(),
                enqueue_many=True,
                allow_smaller_final_batch=True
            )
        else:
            features = tf.train.batch(
                features,
                batch_size,
                capacity=batch_size * 10,
                num_threads=multiprocessing.cpu_count(),
                enqueue_many=True,
                allow_smaller_final_batch=True
            )

        return features, features.pop(PREDICTED_COLUMN)
  
    return _input_fn

def generate_model_fn(learning_rate):
    
    def _model_fn(mode, features, labels):

        (length, diameter, height, whole_weight, shucked_weight, viscera_weight, shell_weight) = INPUT_COLUMNS

        transformed_columns = [
            length, diameter, height, whole_weight, shucked_weight, viscera_weight, shell_weight
        ]

        inputs = tf.feature_column.input_layer(features, transformed_columns)

        first_hidden_layer = Dense(10, activation='relu')(inputs)
        second_hidden_layer = Dense(10, activation='relu')(first_hidden_layer)
        output_layer = Dense(1, activation='linear')(second_hidden_layer)

        if mode in (Modes.PREDICT, Modes.EVAL):
            predictions = tf.reshape(output_layer, [-1])
            predictions_dict = {"ages": predictions}

        if mode in (Modes.TRAIN, Modes.EVAL):
            loss = tf.losses.mean_squared_error(labels, output_layer)

        if mode == Modes.TRAIN:
            train_op = tf.contrib.layers.optimize_loss(
                loss=loss,
                global_step=tf.contrib.framework.get_global_step(),
                learning_rate=learning_rate,
                optimizer="SGD")
        
        if mode == Modes.TRAIN:
            return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)
        
        if mode == Modes.EVAL:
            eval_metric_ops = {
                "rmse": tf.metrics.root_mean_squared_error(
                    tf.cast(labels, tf.float32), predictions)
            }
            return tf.estimator.EstimatorSpec(mode, loss=loss, eval_metric_ops=eval_metric_ops)
        
        if mode == Modes.PREDICT:
            export_outputs = {
                'prediction': tf.estimator.export.RegressionOutput(predictions)
            }
            return tf.estimator.EstimatorSpec(
                mode, predictions=predictions_dict, export_outputs=export_outputs)
    
    return _model_fn

def generate_experiment_fn(**experiment_args):  
  
    def _experiment_fn(run_config, hparams):

        train_input = generate_input_fn(
            hparams.train_files,
            num_epochs=hparams.num_epochs,
            batch_size=hparams.train_batch_size,
        )

        test_input = generate_input_fn(
            hparams.eval_files,
            shuffle=False
        )

        return tf.contrib.learn.Experiment(
            tf.estimator.Estimator(
                generate_model_fn(learning_rate=hparams.learning_rate),
                config=run_config
            ),
            train_input_fn=train_input,
            eval_input_fn=test_input,
            **experiment_args
        )

    return _experiment_fn

def example_serving_input_fn():
    example_bytestring = tf.placeholder(
        shape=[None],
        dtype=tf.string,
    )
    features = tf.parse_example(
        example_bytestring,
        tf.feature_column.make_parse_example_spec(INPUT_COLUMNS)
    )
    return tf.estimator.export.ServingInputReceiver(
        features, {'example_proto': example_bytestring})

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--train-files',
        nargs='+',
        required=True
    )
    parser.add_argument(
        '--num-epochs',
        type=int
    )
    parser.add_argument(
        '--train-batch-size',
        type=int,
        default=1
    )
    parser.add_argument(
        '--eval-batch-size',
        type=int,
        default=1
    )
    parser.add_argument(
        '--eval-files',
        nargs='+',
        required=True
    )
    parser.add_argument(
        '--learning-rate',
        default=0.001,
        type=float
    )
    parser.add_argument(
        '--job-dir',
        required=True
    )
    parser.add_argument(
        '--eval-delay-secs',
        default=10,
        type=int
    )
    parser.add_argument(
        '--min-eval-frequency',
        default=1,
        type=int
    )
    parser.add_argument(
        '--train-steps',
        type=int
    )
    parser.add_argument(
        '--eval-steps',
        default=None,
        type=int
    )

    # For the purposes of running in a notebook hardcoding arguments
    '''args = parser.parse_args([
        '--train-files', 'gs://smiling-beaming-abalone/abalone_train.csv',
        '--eval-files', 'gs://smiling-beaming-abalone/abalone_test.csv',
        '--job-dir', 'abalone_output',
        '--train-steps', '5000',
        '--eval-steps', '100'
      ])'''
    args = parser.parse_args()

    learn_runner.run(
        generate_experiment_fn(
            min_eval_frequency=args.min_eval_frequency,
            eval_delay_secs=args.eval_delay_secs,
            train_steps=args.train_steps,
            eval_steps=args.eval_steps,
            export_strategies=[saved_model_export_utils.make_export_strategy(
                example_serving_input_fn,
                exports_to_keep=1
            )]
        ),
        run_config=tf.contrib.learn.RunConfig(model_dir=args.job_dir),
        hparams=hparam.HParams(**args.__dict__)
    )