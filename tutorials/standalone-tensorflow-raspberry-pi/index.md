---
title: Setting up a standalone TensorFlow prediction device with Raspberry Pi and Google Cloud
description: Learn how to set up a standalone TensorFlow server in Raspberry Pi with a model trained in Cloud ML Engine.
author: arieljassan
tags: TensorFlow, Raspberry Pi, MLEngine
date_published: 2018-12-27
---

Ariel Jassan | Data Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to set up a TensorFlow server in a Raspberry Pi 3B and deploy on it a TensorFlow saved model. 

The architecture of a machine learning model trained in the cloud and served locally is particularly useful when the IoT device has poor connectivity or when the serving availability is critical. 

This tutorial assumes you have a Raspberry Pi with SD card and Raspbian installed on it, that you are familiar with Python and TensorFlow, and that you have available a TensorFlow saved model. If you don’t have access to a saved model, you can alternatively use the saved model resulting from the Image Classification using Flowers dataset tutorial that is provided in this guide for download.

## Challenges solved

TensorFlow models can be served via AI Platform Prediction, TensorFlow Serving API, or with the tf.contrib.predictor library in Python. Since we aim for local prediction without dependency of a connection to the internet, we have discarded the first option. Due to the ARM architecture of the chip in the Raspberry Pi, installing the TensorFlow Serving API requires us to first solve the challenges associated with compiling the solution in that architecture.
The tf.contrib.predictor library in Python allows for serving the model in a straightforward fashion, and therefore we have chosen this method for the solution.

This solution can be useful for applications in agricultural industries where there might be low connectivity to the internet or in other industries that cannot afford the roundtrip of an API call to the internet. 

## Objectives

- Install TensorFlow 1.8 and its dependencies.
- Install software to capture images from a webcam.
- Download a TensorFlow saved model.
- Write a script to serve a TensorFlow model.

## Costs

If you decide to train your own model, you will incur costs of running Cloud ML Engine, Dataflow, and Google Cloud Storage. Otherwise, there are no billable costs involved in this tutorial.
Use the Pricing Calculator to generate a cost estimate based on your projected usage.

## Reference architecture

The following diagram shows the architecture of the solution

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/standalone-tensorflow-raspberry-pi/standalone_tensorflow_img1.png)

1. Data as pictures, CSV files, and so on is originally stored in Google Cloud Storage.
1. The TensorFlow model training is executed in Cloud ML Engine.
1. The resulting saved model is stored in a bucket in Google Cloud Storage.
1. The saved model is transferred to the IoT device.
1. Serving of the model (for example, image recognition) is done locally in the IoT device.

## Before you begin

1. Log into the Raspberry Pi

1. Install required system packages. Several packages are required to successfully install gsutil from PyPI. You can install them with the following command:
    
        sudo apt-get install gcc python-dev python-setuptools libffi-dev
    

1. Install pip. We recommend using the pip installer. You can install it with the following command:
    
        sudo apt-get install python-pip
	

1. Install gsutil from PyPI. To install gsutil from PyPI, use the following command:
	
        sudo pip install gsutil
    

## Installing TensorFlow and its dependencies

1. Install TensorFlow for Raspberry Pi:

        wget https://github.com/lhelontra/tensorflow-on-arm/releases/download/v1.8.0/tensorflow-1.8.0-cp27-none-linux_armv7l.whl
            sudo pip install tensorflow-1.8.0-cp27-none-linux_armv7l.whl
            sudo pip uninstall mock
            sudo pip install mock
	

1. Install fswebcam and fbi:
    
        sudo apt-get install fswebcam
        sudo apt-get install fbi
	

## Downloading a trained saved model and the script for serving

1.  Create a directory where to deploy the model, such as `/flowers_model`:
	
        mkdir /tf_server/flowers_model/1
    

1.  Download the model:

        gsutil cp gs://standalone-tensorflow-raspberry-pi/* /tf_server/flowers_model/1/


1.  Open the Python file that does the serving and customize the model directory if needed:

        nano /standalone-tensorflow-raspberry-pi/tf_server.py

    The variable *`model_dir`* in line 16 of the python file `tf_server.py` identifies the directory where the model is saved. You can edit this if you download a model in a different location.
    
    ```py
    print '--- importing packages'
    
    from tensorflow.contrib import predictor
    import base64
    import sys
    import json
    import subprocess
    import datetime
    
    # In the line below, specify the directory where you hosted your model.
    # This is the directory where the .pb file and variables directory are hosted.
    model_dir = '/tf_server/flowers_model/1'
    ```


## Running the TensorFlow server

Enter the line below to start the TensorFlow server. Note that loading the TensorFlow libraries and TensorFlow saved model may take several minutes.

    python /standalone-tensorflow-raspberry-pi/tf_server.py

Once the model is loaded and you read “press enter to take picture”, press “Enter” to predict the type of flower. The lines of the response represent the probability that each of the flower types in the order below was photographed:

daisy
dandelion
roses
sunflowers
tulips

## Testing the solution

You can test the solution by capturing the images below with the camera attached to the Raspberry Pi. The exact values of the prediction may vary depending on the quality of the image.

| Flower type | Sample image | Expected result |
| ----------- | ------------ | --------------- |
| Daisy | [Link to daisy image](https://www.publicdomainpictures.net/pictures/40000/velka/daisy-flowers-white.jpg) | First line of the results with highest probability |
| Dandelion | [Link to dandelion image](https://cdn.pixabay.com/photo/2013/07/25/16/21/dandelion-167112_960_720.jpg) | Second line of the results with highest probability |
| Rose | [Link to rose image](http://storage.googleapis.com/cloud-ml-data/img/flower_photos/roses/921984328_a60076f070_m.jpg) | Third line of the results with highest probability |
| Sunflower | [Link to sunflower image](https://cdn.pixabay.com/photo/2016/08/28/23/24/sunflower-1627193_960_720.jpg) | Fourth line of the results with highest probability |
| Tulip | [Link to tulip image](https://www.publicdomainpictures.net/pictures/20000/velka/single-tulip-29612970075253BV.jpg) | Fifth line of the results with highest probability |

## Extensions to this lab

This lab can be extended to a more comprehensive solution that can learn fast by incorporating new input data from hundreds of devices and processing it by leveraging the power of the cloud. Other components of Google Cloud can allow for analytics and team collaboration.

In the architecture diagram below, we have incorporated IoT Core and Pub/Sub that allow you to connect and manage hundreds of IoT devices and ingest millions of messages per second. In addition, Dataflow, BigQuery, Dataproc, and Data Studio enable building powerful analytics solutions based on managed services and collaborating with team members. 

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/standalone-tensorflow-raspberry-pi/standalone_tensorflow_img2.png)

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete the project you created.

To delete the project, follow the steps below:
1. In the Cloud Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1. In the project list, select the project you want to delete and click **Delete project**.
![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/standalone-tensorflow-raspberry-pi/img_delete_project.png) 
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.
 
## What's next

- Reference guide: Install Tensorflow for Raspberry Pi (guide from [this article](http://www.instructables.com/id/Google-Tensorflow-on-Rapsberry-Pi/))
- Reference guide: Install fswebcam and fbi executables (as explained [here](https://www.raspberrypi.org/documentation/usage/webcams/) and [here](https://www.raspberrypi-spy.co.uk/2017/02/how-to-display-images-on-raspbian-command-line-with-fbi/))
- Try out other Google Cloud Platform features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials). 
