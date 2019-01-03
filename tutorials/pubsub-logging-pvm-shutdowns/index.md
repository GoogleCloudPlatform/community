---
title: Pub/Sub API Logging for Preemptible VM Shutdowns
description: Send notifications of pVM shutdowns to Pub/Sub for logging.
author: mkahn5
tags: PubSub, Compute Engine
date_published: 2017-10-03
---

## Pub/Sub API logging for Preemptible VM (pVM) shutdowns

This tutorial demonstrates sending notifications from [Preemptible Virtual Machines (pVMS)](https://cloud.google.com/preemptible-vms/) to Google Cloud Pub/Sub for logging purposes.

## Creating the instance

To get started, we'll use a regular instance and will configure the Python
libraries and the script to make sure it works as expected. We'll then copy the
disk to an image for use in pVMs that we create in the future.

## Creating the Pub/Sub topic via Google Cloud Shell

Next, create a topic called `shutdown-log` to hold all of the shutdown
timestamps for the pVMs:

```bash
mikekahn@mikekahn-sandbox:~$ gcloud beta pubsub topics create shutdown-log
Created topic [shutdown-log].mikekahn@mikekahn-sandbox:~$
```

## Creating a device credential

To enable auth for the Pub/Sub API, click the **IAM & admin** section of the
console. Then, in the **Service accounts** section, click
**Create service account**.

![Pubsub Role](https://storage.googleapis.com/gcp-community/tutorials/pubsub-logging-pvm-shutdowns/iam.png)

Give the service account a Pub/Sub role. If this script is just publishing, you
can just give it the Publisher role. If you plan to manage subscriptions from
the instance, then give it Admin or a higher privileged role.

Be sure to download a new JSON key. Now the device has a credential in the form
of a file. Copy the JSON key on your instance. Copy and paste the JSON from the
key exported in the last step, or move it over via SCP to your instance.

### Using the credential on the device

We are going to use a Google client library to talk to Pub/Sub. In order for
this client library to find and use the credential file we copied it will look
for an environment variable which we set on the device. Add the variable to
bashrc so it loads on its own (debian).

```bash
mikekahn@instance-1:/$ echo "export GOOGLE_APPLICATION_CREDENTIALS=/shutdown-log-key.json" >> ~/.bashrc
```

We are now good to go with the Pub/Sub API. Next, make sure you have the most
updated Google Cloud Python library via pip and it works:

```bash
mikekahn@instance-1:/$ sudo wget https://bootstrap.pypa.io/get-pip.py
mikekahn@instance-1:/$ sudo python get-pip.py
Collecting pip
Downloading pip-9.0.1-py2.py3-none-any.whl (1.3MB)    100% |████████████████████████████████| 1.3MB 1.0MB/s
Collecting setuptools  
Downloading setuptools-36.5.0-py2.py3-none-any.whl (478kB)    100% |████████████████████████████████| 481kB 2.4MB/s
Collecting wheel  
Downloading wheel-0.30.0-py2.py3-none-any.whl (49kB)    100% |████████████████████████████████| 51kB 9.8MB/s
Installing collected packages: pip, setuptools, wheel
Successfully installed pip-9.0.1 setuptools-36.5.0 wheel-0.30.0
```

```bash
mikekahn@instance-1:/$ sudo apt-get install python-dev
mikekahn@instance-1:/$ sudo pip install --upgrade google-cloud
Successfully installed dill-0.2.7.1 future-0.16.0
gapic-google-cloud-datastore-v1-0.15.3
gapic-google-cloud-error-reporting-v1beta1-0.15.3
gapic-google-cloud-logging-v2-0.91.3
gapic-google-cloud-pubsub-v1-0.15.4
gapic-google-cloud-spanner-admin-database-v1-0.15.3
gapic-google-cloud-spanner-admin-instance-v1-0.15.3
gapic-google-cloud-spanner-v1-0.15.3
google-cloud-0.27.0 google-cloud-bigquery-0.26.0 google-cloud-bigtable-0.26.0 google-cloud-core-0.26.0
google-cloud-datastore-1.2.0 google-cloud-dns-0.26.0 google-cloud-error-reporting-0.26.0 google-cloud-language-0.27.0 google
cloud-logging-1.2.0 google-cloud-monitoring-0.26.0 google-cloud-pubsub-0.27.0 google-cloud-resource-manager-0.26.0 google
cloud-runtimeconfig-0.26.0 google-cloud-spanner-0.26.0 google-cloud-speech-0.28.0 google-cloud-storage-1.3.2 google-cloud
translate-1.1.0 google-cloud-videointelligence-0.25.0 google-cloud-vision-0.26.0 google-gax-0.15.15 google-resumable-media
0.2.3 grpc-google-iam-v1-0.11.4 httplib2-0.10.3 monotonic-1.3 oauth2client-3.0.0 ply-3.8 proto-google-cloud-datastore-v1
0.90.4 proto-google-cloud-error-reporting-v1beta1-0.15.3 proto-google-cloud-logging-v2-0.91.3 proto-google-cloud-pubsub-v1
0.15.4 proto-google-cloud-spanner-admin-database-v1-0.15.3 proto-google-cloud-spanner-admin-instance-v1-0.15.3 proto-google
cloud-spanner-v1-0.15.3 tenacity-4.4.0
mikekahn@instance-1:/$
mikekahn@instance-1:/$ sudo pip install --upgrade google-cloud-pubsub
```

At the time of writing this article I had an issue with the Python pubsub module
0.27.1. If you are having issues, try using 0.28.3, as it worked fine for me.

```bash
mikekahn@instance-1:/$ sudo pip install google-cloud-pubsub==0.28.3
```

## Pub/Sub publish script

```python
import socket
import os
import time

from google.cloud import pubsub_v1
from datetime import datetime

from subprocess import check_output

publisher = pubsub_v1.PublisherClient()

hostname = socket.gethostname()
ips = check_output(['hostname', '--all-ip-addresses'])
timestamp = time.strftime("%c")

topic = 'projects/{project_id}/topics/{topic}'.format(
    project_id='mikekahn-sandbox',
    topic='shutdown-log',  # Set this to something appropriate.
)
publisher.publish(topic, timestamp, ips=ips)
```

Very simply, this script publishes a message to the pubsub topic shutdown-log
with a timestamp and ip address of the server. IPs can be interchangeable with
hostname in the publisher statement. Replace the `project_id` and topic
variables if you use the above script. Now run the script and check the topic to
see if your message came through.

## Check the topic for your messages

```bash
mikekahn@mikekahn-sandbox:~$ gcloud beta pubsub subscriptions list
┌──────────────────┬──────────────┬──────────────┬──────┬──────────────┐
│     PROJECT      │ SUBSCRIPTION │    TOPIC     │ TYPE │ ACK_DEADLINE
│├──────────────────┼──────────────┼──────────────┼──────┼──────────────┤
│ mikekahn-sandbox │ shutdown-log │ shutdown-log │ PULL │ 10
│└──────────────────┴──────────────┴──────────────┴──────┴──────────────┘
mikekahn@mikekahn-sandbox:~$


mikekahn@mikekahn-sandbox:~$ gcloud beta pubsub subscriptions pull projects/mikekahn-sandbox/subscriptions/shutdown-log
┌──────────────────────────┬─────────────────┬──────────────────┬────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│           DATA           │    MESSAGE_ID   │    ATTRIBUTES    │  ACK_ID
│├──────────────────────────┼─────────────────┼──────────────────┼───────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────────────────────────────
┤│ Mon Sep 25 23:50:57 2017 │ 155794142007574 │ ips=10.128.0.3   │
XkASTCcYRElTK0MLKlgRTgQhIT4wPkVTRFAGFixdRkhRNxkIaFEOT14jPzUgKEUVCQgUBXx9cEJTdV9UcmhRDRlyfWBwPwgbUwoXB35cURIHaE5tdSVuDBx3emhxa
14RAQJCVnlbc_SJyvQ2ZiU9XxJLLD5-LC1FQQ
│└──────────────────────────┴─────────────────┴──────────────────┴───────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Here our pubsub message shows the timestamp Mon Sept 25… and the instance IP
10.128.0.3. Great, everything works! So now let's move this over to a pVM and
test once more.

## Configure shutdown script

You can invoke a shutdown script directly or provide a shutdown script file for
instances on GCE. In this case the script is on the image so I am providing
contents directly. Next step (not shown) I saved the python pubsub api message
script above, configured tested python library and the json API key to a compute
image called shutdown-log. So now with my image created I can start building
pVMs ready to notify me when they go offline.

## Build a pVM with the shutdown script

```bash
mikekahn@mikekahn-sandbox:~$ gcloud compute instances create pubsubshutdown6 --preemptible --image shutdown-log --zone us
west1-a --metadata shutdown-script="#! /bin/bash
sudo su -
python /pub-sub-publish.py"

Created [https://www.googleapis.com/compute/v1/projects/mikekahn-sandbox/zones/us-west1-a/instances/pubsubshutdown2].
NAME             ZONE        MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP     STATUS
pubsubshutdown2  us-west1-a  n1-standard-1  true         10.138.0.4   35.203.140.135  RUNNING
mikekahn@mikekahn-sandbox:~$
```

Result:
![pVM Instance Details - Shutdown Script](https://storage.googleapis.com/gcp-community/tutorials/pubsub-logging-pvm-shutdowns/pvm.png)

## Verify logging is setup

Now pVM instances built with image that contains the script in this post will
publish their IP and timestamp to the Pub/Sub topic as they are shut down. This
can be used for logging and notification whenever pVMs are taken offline for
infrastructure managers or to trigger other events in application workflow.

```bash
mikekahn@mikekahn-sandbox:~$ gcloud beta pubsub subscriptions pull projects/mikekahn-sandbox/subscriptions/shutdown-log
┌──────────────────────────┬─────────────────┬──────────────────┬─────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────────────────────────────────────────┐│   DATA │
MESSAGE_ID   │    ATTRIBUTES    │ ACK_ID
│├──────────────────────────┼─────────────────┼──────────────────┼───────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────────────────────────────┤│ Fri Sep 29 00:53:54
2017 │ 156359192560439 │ ips=10.138.0.4   │
XkASTCcYRElTK0MLKlgRTgQhIT4wPkVTRFAGFixdRkhRNxkIaFEOT14jPzUgKEUaCQgUBXx9cVtedV5ZGgdRDRlyfGQgOQsVUAURUy1VWhENem1cVzhQCB9xeGh0Y
gWBwJBUHd32cmqwsBtZho9XxJLLD5-LC1FQQ
│└──────────────────────────┴─────────────────┴──────────────────┴───────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
