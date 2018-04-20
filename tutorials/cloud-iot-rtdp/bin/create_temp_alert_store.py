import os
from google.cloud import datastore

client = datastore.Client(os.environ['PROJECT'])
for i in range(30):
    incomplete_key = client.key('device')
    device = datastore.Entity(key=incomplete_key)
    device.update({
        'name':u'device'+str(i+1),
        'tempAlertThredshold':i+1
    })
    client.put(device)
