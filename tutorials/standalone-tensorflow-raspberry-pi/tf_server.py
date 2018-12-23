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


print '--- loading model'

predict_fn = predictor.from_saved_model(model_dir)

while True:

    k = raw_input('press enter to take picture')

    t = datetime.datetime.now()
    img_file_name =  '/tf_server/images/{0.year}_{0.month}_{0.day}_{0.hour}{0.minute}_{0.second}_{0.microsecond}.jpg'.format(t)
    print 'to be saved as: ', img_file_name

    print '--- taking picture ...'
    subprocess.call('fswebcam ' + img_file_name, shell=True)
    subprocess.call('fbi '+ img_file_name, shell=True)

    img = open(img_file_name, "rb").read()


    print '--- analyzing image...'
    predictions = predict_fn(
        {
        "key": ["0"],
        "image_bytes": [img]
        })
    for score in predictions['scores'][0]:
        print round(score, 5)
