# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# tested with TF1.14
import sys
import tensorflow as tf

from absl import app
from absl import flags
from tensorflow.core.protobuf import saved_model_pb2
from tensorflow.python.summary import summary

FLAGS = flags.FLAGS

flags.DEFINE_string('saved_model', '', 'The location of the saved_model.pb to visualize.')
flags.DEFINE_string('output_dir', '', 'The location for the Tensorboard log to begin visualization from.')

def import_to_tensorboard(saved_model, output_dir):
  """View an imported saved_model.pb as a graph in Tensorboard.

  Args:
    saved_model: The location of the saved_model.pb to visualize.
    output_dir: The location for the Tensorboard log to begin visualization from.

  Usage:
    Call this function with your model location and desired log directory.
    Launch Tensorboard by pointing it to the log directory.
    View your imported `.pb` model as a graph.
  """
  with open(saved_model, "rb") as f:
    sm = saved_model_pb2.SavedModel()
    sm.ParseFromString(f.read())
    if 1 != len(sm.meta_graphs):
      print('More than one graph found. Not sure which to write')
      sys.exit(1)
    graph_def = sm.meta_graphs[0].graph_def

    pb_visual_writer = summary.FileWriter(output_dir)
    pb_visual_writer.add_graph(None, graph_def=graph_def)
    print("Model Imported. Visualize by running: "
          "tensorboard --logdir={}".format(output_dir))


def main(argv):
  import_to_tensorboard(FLAGS.saved_model, FLAGS.output_dir)


if __name__ == '__main__':
  app.run(main)
