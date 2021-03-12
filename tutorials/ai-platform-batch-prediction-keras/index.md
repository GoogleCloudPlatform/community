---
title: Use Keras models for batch predictions on AI Platform
description: Learn about using Keras models for batch predictions on AI Platform.
author: enakai00
tags: TensorFlow, ML, machine learning
date_published: 2020-02-01
---

Etsuji Nakai | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how you can modify machine learning models defined with Keras so that you can use them for batch predictions on AI Platform.

## Objectives

* Understand how batch predictions work on AI Platform.
* Learn how to modify Keras models for batch predictions.
* Go through example notebooks using AI Platform Notebooks.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [AI Platform](https://cloud.google.com/ai-platform)
* [AI Platform Notebooks](https://cloud.google.com/ai-platform-notebooks)
* [Cloud Storage](https://cloud.google.com/storage)

Use the [pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage.

## Before you begin

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project) for your project.
1.  Open [Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell).
1.  Set the project ID for the Cloud SDK:

        gcloud config set project [YOUR_PROJECT_ID]

1.  Enable APIs:

        gcloud services enable ml.googleapis.com notebooks.googleapis.com

## How batch predictions work on AI Platform

[AI Platform](https://cloud.google.com/ai-platform) provides a serverless platform for training and serving machine learning (ML) models. When you have a large 
number of instances, you can use the [batch prediction](https://cloud.google.com/ai-platform/prediction/docs/batch-predict) feature to get predictions. You store
prediction input files in the storage bucket and submit a batch prediction job. The prediction results are recorded in text files and stored in the storage 
bucket.

When using batch prediction, you need to consider the fact that the order of prediction results in the output files can be different from the order of instances
in the prediction input files. This difference is because batch prediction is conducted with multiple workers in a distributed manner. Therefore, you need to 
modify your machine learning model so that it accepts a unique identifier as a part of the input features and outputs the same identifier as a part of the 
prediction result.

The following example shows input and the corresponding output.

Input file:

        {"features": [18.0846, 0.0, 18.1, 0.0, 0.679, 6.434, 100.0, 1.8347, 24.0, 666.0, 20.2, 27.25, 29.05], "key": 0}
        {"features": [0.12329, 0.0, 10.01, 0.0, 0.547, 5.913, 92.9, 2.3534, 6.0, 432.0, 17.8, 394.95, 16.21], "key": 1}
        {"features": [0.05497, 0.0, 5.19, 0.0, 0.515, 5.985, 45.4, 4.8122, 5.0, 224.0, 20.2, 396.9, 9.74], "key": 2}
        {"features": [1.27346, 0.0, 19.58, 1.0, 0.605, 6.25, 92.6, 1.7984, 5.0, 403.0, 14.7, 338.92, 5.5], "key": 3}
        {"features": [0.07151, 0.0, 4.49, 0.0, 0.449, 6.121, 56.8, 3.7476, 3.0, 247.0, 18.5, 395.15, 8.44], "key": 4}
        {"features": [0.27957, 0.0, 9.69, 0.0, 0.585, 5.926, 42.6, 2.3817, 6.0, 391.0, 19.2, 396.9, 13.59], "key": 5}
        {"features": [0.03049, 55.0, 3.78, 0.0, 0.484, 6.874, 28.1, 6.4654, 5.0, 370.0, 17.6, 387.97, 4.61], "key": 6}
        {"features": [0.03551, 25.0, 4.86, 0.0, 0.426, 6.167, 46.7, 5.4007, 4.0, 281.0, 19.0, 390.64, 7.51], "key": 7}
        {"features": [0.09299, 0.0, 25.65, 0.0, 0.581, 5.961, 92.9, 2.0869, 2.0, 188.0, 19.1, 378.09, 17.93], "key": 8}
        {"features": [3.56868, 0.0, 18.1, 0.0, 0.58, 6.437, 75.0, 2.8965, 24.0, 666.0, 20.2, 393.37, 14.36], "key": 9}

Output file:

        {"prediction": [8.061697959899902], "key": 0}
        {"prediction": [21.562673568725586], "key": 1}
        {"prediction": [22.76498031616211], "key": 2}
        {"prediction": [29.869117736816406], "key": 3}
        {"prediction": [25.40222930908203], "key": 4}
        {"prediction": [21.52297019958496], "key": 5}
        {"prediction": [28.398698806762695], "key": 6}
        {"prediction": [24.931306838989258], "key": 7}
        {"prediction": [19.04778289794922], "key": 8}
        {"prediction": [20.156259536743164], "key": 9}

In this example, integer keys are used as a unique identifier and both input and output are sorted by the key. You can match the input and output using the key 
value even if the output is randomly ordered.

## Modify Keras models for batch predictions

If you use Keras to define a model, you can use one of the following approaches to add a unique key to the model:

- Use the functional API to create a wrapper model that adds a key field to an existing model.
- Use the `@tf.function` decorator to define a wrapper function to make predictions with keys.

The following sections explain each of these approaches for adding unique keys for a Keras model that you have defined and trained. The model object is stored
in the variable `model`.

### Using the functional API

You can define and compile a wrapper model `wrapper_model` using the Keras functional API:

    key = layers.Input(shape=(), name='key', dtype='int32')
    pred = layers.Concatenate(name='prediction_with_key')(
        [model.output, tf.cast(layers.Reshape((1,))(key), tf.float32)])
    wrapper_model = models.Model(inputs=[model.input, key], outputs=pred)
    wrapper_model.compile()

The following diagram shows the architecture of the wrapper model:

![wrapper model](https://storage.googleapis.com/gcp-community/tutorials/ai-platform-batch-prediction-keras/wrapper_model.png)

In this diagram, the upper part is the original model that accepts features and outputs a prediction. The lower part simply passes through a unique key. The
prediction and key are concatenated to generate a combined result.

You export `wrapper_model` in the saved_model format and deploy it to AI Platform. The following code snippet shows how you use the deployed model to make an 
online prediction. The model accepts the `key` field in addition to `features`.

    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials
    import json
        
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build('ml', 'v1', credentials=credentials, cache_discovery=False)
        
    request_data =  {'instances':
      [
        {"features": [18.0846, 0, 18.1, 0, 0.679, 6.434, 100, 1.8347, 24, 666, 20.2, 27.25, 29.05], "key": 0},
        {"features": [0.12329, 0, 10.01, 0, 0.547, 5.913, 92.9, 2.3534, 6.0, 432, 17.8, 394.95, 16.21], "key": 1},
      ]
    }
        
    parent = 'projects/%s/models/%s/versions/%s' % (PROJECT, 'housing_price1', 'v1')
    response = api.projects().predict(body=request_data, name=parent).execute()
    print(json.dumps(response, sort_keys = True, indent = 4))

The output contains the prediction and key values as follows:

    {
        "predictions": [
            {
                "prediction_with_key": [
                    11.821846961975098,
                    0.0
                ]
            },
            {
                "prediction_with_key": [
                    18.870054244995117,
                    1.0
                ]
            }
        ]
    }

The [`functional_API_example` notebook](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/ai-platform-batch-prediction-keras/notebooks/functional_API_example.ipynb)
explains the whole procedure to use this approach for batch prediction. To run the notebook, follow the instructions in the last section of this document.

### Using the `@tf.function` decorator

You can define a wrapper function as follows:

    @tf.function(input_signature=[tf.TensorSpec([None, 13]), 
                                  tf.TensorSpec([None], dtype=tf.int32)])
    def add_key(features, key):
        pred = model(features, training=False)
        return {'prediction': pred, 'key': key}

The `input_signature` option specifies the parameter types of the function `add_key`. In this case, the parameter `features` corresponds to a list of 13 float
values that is an input feature of the original model, and the parameter `key` corresponds to an integer key. In other words, the function `add_key` accepts 
features of the original model and an integer key. It returns the dictionary containing prediction and key values.

The `@tf.function` decorator builds a TensorFlow graph containing the specified function.

You export the model in the saved_model format using the wrapper function as `serving_default`:

    export_path = './export'
    model.save(export_path, signatures={'serving_default': add_key}, save_format='tf')

This ensures that the function `add_key` is used to make predictions when you deploy it to AI Platform. The following code snippet shows how you use the 
deployed model to make an online prediction. The model accepts the `key` field in addition to `features`.

    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials
    import json
        
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build('ml', 'v1', credentials=credentials, cache_discovery=False)
    
    request_data =  {'instances':
      [
        {"features": [18.0846, 0, 18.1, 0, 0.679, 6.434, 100, 1.8347, 24, 666, 20.2, 27.25, 29.05], "key": 0},
        {"features": [0.12329, 0, 10.01, 0, 0.547, 5.913, 92.9, 2.3534, 6.0, 432, 17.8, 394.95, 16.21], "key": 1},
      ]
    }
        
    parent = 'projects/%s/models/%s/versions/%s' % (PROJECT, 'housing_price2', 'v1')
    response = api.projects().predict(body=request_data, name=parent).execute()
    print(json.dumps(response, sort_keys = True, indent = 4))

The output contains the prediction and key values as follows:

    {
        "predictions": [
            {
                "key": 0,
                "prediction": [
                    8.061708450317383
                ]
            },
            {
                "key": 1,
                "prediction": [
                    21.562681198120117
                ]
            }
        ]
    }

**Note**: The output format is different from the output of the functional API approach in the previous section.

The [`decorator_example` notebook](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/ai-platform-batch-prediction-keras/notebooks/decorator_example.ipynb)
explains the whole procedure to use this method for batch prediction. To run the notebook, follow the instructions in the next section of this document.

## Go through example notebooks using AI Platform Notebooks

1.  Go to the [AI Platform Notebooks](https://console.cloud.google.com/ai-platform/notebooks/) page in the Cloud Console.
1.  Start a new notebook instance by choosing **TensorFlow Enterprise 2.3 without GPUs** for the instance type.
1.  Open JupyterLab and execute the following command from the JupyterLab terminal:

        curl -OL https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/ai-platform-batch-prediction-keras/notebooks/functional_API_example.ipynb
        curl -OL https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/ai-platform-batch-prediction-keras/notebooks/decorator_example.ipynb

1.  Open the following notebooks and follow the instructions.

    - Using the functional API: `functional_API_example.ipynb`
    - Using the `@tf.function` decorator: `decorator_example.ipynb`

In these notebooks, you define a model to predict average housing prices using the
[Boston Housing price regression dataset](https://keras.io/api/datasets/boston_housing/#load_data-function) as an example.
