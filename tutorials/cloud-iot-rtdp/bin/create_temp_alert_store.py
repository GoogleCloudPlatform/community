import os
from google.cloud import datastore

client = datastore.Client(os.environ['GCLOUD_PROJECT'])
for i in range(30):
    incomplete_key = client.key('device')
    device = datastore.Entity(key=incomplete_key)
    device.update({
        'name':u'device{}'.format(str(i+1)),
        'tempAlertThredshold':i+1
    })
    client.put(device)
