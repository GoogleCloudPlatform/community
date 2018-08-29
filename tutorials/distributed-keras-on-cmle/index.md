---
title: Distributed Keras on Google Cloud Machine Learning Engine
description: Learn how to use distributed Keras on Cloud Machine Learning Engine.
author: corrieelston
tags: Data Science, Cloud Machine Learning Engine, Keras, Python
date_published: 2017-09-28
---

# Distributed Keras on Google Cloud Machine Learning Engine (CMLE)

This solution connects the dots between a number of technologies with the end result of a production-grade model.

First the technologies:

* [TensorFlow](https://www.tensorflow.org/) (including [tf.contrib.learn](https://www.tensorflow.org/get_started/tflearn)) - TensorFlow is the most popular deep learning library available.  It is functional and performant, but equally importantly, has a vibrant community of users producing educational and reference materials to accelerate your progress towards adding value to your business.
* [Keras](https://keras.io/) - Keras is a high-level, Python API focused on enabling fast experimentation, with the motivation that moving from idea to result with the least possible delay is the key to good research (and machine learning in general).  It is being integrated into TensorFlow (currently as tf.contrib.keras) but is also available standalone and can run on TensorFlow, CNTK or Theano.
* [Google Cloud Machine Learning Engine (CMLE)](https://cloud.google.com/ml-engine/) - CMLE is a managed service that enables you to easily build machine learning models that work on any type of data, of any size.  It facilitates two activities: One, decreasing training time by allowing you train models using large numbers of CPUs, GPUs and TPUs, and two,
allowing you to train models in parallel.  Both of these activities further enable you to iterate faster with less overhead.

## Prerequisites

* Run through the [Cloud Datalab quickstart](https://cloud.google.com/datalab/docs/quickstarts):
  * Create a project on Google Cloud Platform.
  * Ensure Compute Engine (GCE) and CMLE APIs are enabled.
  * Create an instance of Cloud Datalab.
* Create a new notebook within Datalab and execute the following from a code cell, `!gsutil cp gs://gcp-community/tutorials/distributed-keras-on-cmle/*.ipynb .`
* Open `1-start-here.ipynb` and enjoy.

## Activities

* [You'll learn (or revise) creating custom estimators in tf.contrib.learn](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/distributed-keras-on-cmle/2-original-neural-net.ipynb) from [this tutorial](https://www.tensorflow.org/extend/estimators) by running the [original code](https://github.com/tensorflow/tensorflow/blob/r1.2/tensorflow/examples/tutorials/estimators/abalone.py).
* [You'll run a barebones version of the same model that will serve as a basis for migrating the model to Keras](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/distributed-keras-on-cmle/3-tweaked-original-neural-net.ipynb).
* [You'll run a version of the same model implemented using Keras](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/distributed-keras-on-cmle/4-keras.ipynb) for the dataflow graph definition and tf.contrib.learn for other functionality such as the loss function and utilites such as the training/evaluation loop.
* [You'll run a production-grade version of the Keras model locally](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/distributed-keras-on-cmle/5-keras-full.ipynb) that adds in the code required to train the model on CMLE.
* [You'll use CMLE via the gcloud CLI to execute the same model locally and remotely](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/distributed-keras-on-cmle/6-distributed-keras.ipynb) on Google Cloud Platform (GCP).

The remainder of this notebook includes a number of housekeeping items required to run later notebooks (upgrading Tensorflow to 1.2 and downloading training/test datasets).
