---
title: Using an AutoML single-label classification model with Python
description: Learn how to use a TensorFlow model trained with AutoML to classify images into different labels.
author: harshithdwivedi
tags: machine learning, image classification
date_published: 2020-05-06
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial describes how to use a TensorFlow model trained with AutoML to classify images with different labels.

The ability to load and run models in a Python environment is extremely useful, considering that most machine learning 
applications are built in Python because of its rich tool support.

This tutorial assumes that you have a TensorFlow image classification saved model trained on AutoML and a machine running
Python 3. If you don’t have access to a saved classification model, you can train a new image classification model with 
AutoML.

## Challenges solved

TensorFlow models can be served through AI Platform Prediction, TensorFlow Serving API, the tf.contrib.predictor library, or
loading them directly in Python. Since this tutorial aims for local prediction without dependence on a connection to the
internet, we have discarded the first option.

This solution can be useful for use in desktop applications where the predictions are to be run locally on a user's machine.

## Objectives

- Install TensorFlow and its dependencies.
- Download a TensorFlow saved model.
- Read images from a local folder.
- Write a script to deploy the saved model and run predictions.
- Understand the output and map it to the resulting labels.
- Implement batching for increased performance.

## Costs

If you decide to train your own model, you will incur costs of training an AutoML Edge image classification model. 
Otherwise, there are no billable costs involved in this tutorial.

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your 
projected usage.

## Before you begin

1.  Install `pip`:
    
        sudo apt-get install python-pip

## Installing TensorFlow and its dependencies

1.  Install TensorFlow:

        pip install tensorflow

## Downloading a trained saved model

1.  Create a directory to which to deploy the model, such as `/saved_model`:
	
        mkdir /tf_python/saved_model/1
    
1.  Download the model by going to the corresponding dataset in the
    [Vision Dashboard](https://console.cloud.google.com/vision/dashboard) and exporting the model. 
    
    ![](https://storage.googleapis.com/gcp-community/tutorials/tensorflow-automl-classification-python/export_model.png)

    This exports the resulting `.pb` file in the specified Google Cloud Storage bucket that you can download for
    use locally.

## Create starter script to load the saved model

Now that you have the model and your development environment ready, the next step is to create a Python snippet that allows 
you to load this model and perform inference with it.

1.  Create a new python file in the project directory and add the following code snippet to it:

        # you want to run the inference on Tf 1.x instead of 2.x
        import tensorflow.compat.v1 as tf
        tf.disable_v2_behavior()

        # path to the folder containing your downloaded .pb file.
        # you can change this if you downloaded the model to a different location
        model_path = '/tf_python/saved_model/1'

        # creating a tensorflow session (used to make predictions later)
        session = tf.Session(graph=tf.Graph())

        # loading the model into the session created above
        tf.saved_model.loader.load(session, ['serve'], model_path)

1.  Run the script above with the command `python main.py`. If you don’t get any errors, you’re good to go!

## Reading the images and providing input to the ML model

To test whether the model works as expected, place some images on which to run the prediction on in a folder,
such as `test_images`. You will be iterating through this folder and passing each image to your loaded model.

    # you want to run the inference on Tf 1.x instead of 2.x
    import tensorflow.compat.v1 as tf
    tf.disable_v2_behavior()

    import pathlib

    # path to the folder containing your downloaded .pb file
    model_path = "/tf_python/saved_model/1"

    # path to the folder containing test images
    image_path = "test_images"

    # creating a tensorflow session (used to make predictions later)
    session = tf.Session(graph=tf.Graph())

    # loading the model into the session created above
    tf.saved_model.loader.load(session, ['serve'], model_path)

    for file in pathlib.Path(image_path).iterdir():
      # get the current image path
      current_image_path = str(file.resolve())
  
      # get the image byte-array since this is what the ML model needs as its input
      img_bytes = open(current_image_path, 'rb').read()
  
      # pass the image as input to the ML model and get the result
      result = session.run('scores:0', feed_dict={
                'Placeholder:0': [img_bytes]})
  
      print("File {} has result {}".format(file.stem, result))

The code might look complex, but it’s actually not! Let’s break down it to see what’s happening here:

- Lines 1–14: Initialization, discussed earlier.
- Line 16: Iterating through the directory in which the images are placed using PathLib.
- Line 18–21: Converts each image to a byte array, which is a format that TensorFlow understands.
- Line 24–27: Passes each byte array to the session variable and gets the output. The `scores:0` node in
  the model stores the prediction scores (the output). The `Placeholder:0` node stores the input.

After running the code above and printing the result, the output should look something like the following:

![](https://storage.googleapis.com/gcp-community/tutorials/tensorflow-automl-classification-python/result_probabilities.png)

Though you can see that TensorFlow does spew out some numbers that look like probabilities, it's a bit hard to make sense
of them at first glance.

## Formatting the results obtained with TensorFlow

Because the image classification model used here was trained to detect 2 labels (underexposed images and overexposed 
images), it’s not a surprise that the resulting output array also has only 2 elements. And naturally, each one of them 
belongs to either of the 2 labels.

To know which one is which, go to the **Dataset** page in the Cloud Console and from there go to the **Images** tab.

![](https://storage.googleapis.com/gcp-community/tutorials/tensorflow-automl-classification-python/label.png)

Overexposed is the first entry, followed by the underexposed entry; in your output array, the first entry is the probability
that the given image is overexposed, and the second entry is the probability that the given image is underexposed.

To convert this output into human-readable labels, get the largest value from the array (which corresponds to the highest
probability) and map it to a label: 

    # you want to run the inference on Tf 1.x instead of 2.x
    import tensorflow.compat.v1 as tf
    tf.disable_v2_behavior()

    import pathlib

    # path to the folder containing your downloaded .pb file
    model_path = "/tf_python/saved_model/1"

    # path to the folder containing images
    image_path = "test_images"

    # creating a tensorflow session (used to make predictions later)
    session = tf.Session(graph=tf.Graph())

    # loading the model into the session created above
    tf.saved_model.loader.load(session, ['serve'], model_path)

    for file in pathlib.Path(image_path).iterdir():
      # get the current image path
      current_image_path = str(file.resolve())
  
      # image bytes since this is what the ML model needs as its input
      img_bytes = open(current_image_path, 'rb').read()
  
      # pass the image as input to the ML model and get the result
      result = session.run('scores:0', feed_dict={
                'Placeholder:0': [img_bytes]})
  
      probabilities = result[0]
  
      if probabilities[0] > probabilities[1]:
        # the first element in the array is largest
        print("Image {} is OverExposed".format(file.stem))
      else: 
        # the second element in the array is largest
        print("Image {} is UnderExposed".format(file.stem))

Running the code snippet above again should provide the following result: 

![](https://storage.googleapis.com/gcp-community/tutorials/tensorflow-automl-classification-python/result_label.png)

Notice how the output is now formatted to human-readable labels.

## Batching the images for better performance

Though the code snippet outlined above works well, it might not be the most ideal or provide the highest performance when 
dealing with a large number of images.

Batching can help to reduce the prediction latency in such scenarios.

Here's an extension on the code snippet above that collects all the images from the folder in an array and then runs the 
session on all of them at once: 

    # you want to run the inference on Tf 1.x instead of 2.x
    import tensorflow.compat.v1 as tf
    tf.disable_v2_behavior()

    import pathlib

    # path to the folder containing your downloaded .pb file
    model_path = "/tf_python/saved_model/1"

    # path to the folder containing images
    image_path = "test_images"

    # creating a tensorflow session (used to make predictions later)
    session = tf.Session(graph=tf.Graph())

    # loading the model into the session created above
    tf.saved_model.loader.load(session, ['serve'], model_path)

    # arrays to maintaining the images and their names for batching purpose
    images = []
    image_names = []

    for file in pathlib.Path(image_path).iterdir():
      # get the current image path
      current_image_path = str(file.resolve())
  
      # image bytes since this is what the ML model needs as its input
      img_bytes = open(current_image_path, 'rb').read()
  
      images.append(img_bytes)
      image_names.append(file.stem)

    # pass the image as input to the ML model and get the result
    batch_results = session.run('scores:0', feed_dict={'Placeholder:0': images})
  
    # iterate through the results
    for index, result in enumerate(batch_results):
      if result[0] > result[1]:
        # the first element in the array is largest
        print("Image {} is OverExposed".format(image_names[index]))
      else: 
        # the second element in the array is largest
        print("Image {} is UnderExposed".format(image_names[index]))

Testing this code on the author's local machine (a MacBook Pro) with 50 images, batching made the overall inferencing 
process around 30% faster, compared to non-batched code.

However, setting a very large batch size might cause out of memory errors, and your app might crash! Keep this in mind while
batching your requests, and be conservative with your batch sizes.

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete
the project you created.

To delete the project, follow the steps below:

1.  In the Cloud Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1.  In the project list, select the project you want to delete and click **Delete project**.

    ![](https://storage.googleapis.com/gcp-community/tutorials/standalone-tensorflow-raspberry-pi/img_delete_project.png) 

1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
