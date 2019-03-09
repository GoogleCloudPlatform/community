#!/usr/bin/env python

# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Sample for connecting to Google Cloud IoT Core via MQTT, using JWT.
The purpose of this small agent is to demonstrate the configuration and
activation of the mender.io agent
"""

import argparse
import datetime
import json
import os
import random
import ssl
import time
import shutil
import subprocess
import sys

import jwt
import paho.mqtt.client as mqtt

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1

# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 30

# Whether to wait with exponential backoff before publishing.
should_backoff = False


# [START iot_mqtt_jwt]
def create_jwt(project_id, private_key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
        Args:
         project_id: The cloud project ID this device belongs to
         private_key_file: A path to a file containing either an RSA256 or
                 ES256 private key.
         algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
        Returns:
            An MQTT generated from the given project_id and private key, which
            expires in 20 minutes. After 20 minutes, your client will be
            disconnected, and a new JWT will have to be generated.
        Raises:
            ValueError: If the private_key_file does not contain a known key.
        """

    token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    # Read the private key file.
    with open(private_key_file, 'r') as f:
        private_key = f.read()

    print('Creating JWT using {} from private key file {}'.format(
            algorithm, private_key_file))

    return jwt.encode(token, private_key, algorithm=algorithm)


def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print('on_connect', mqtt.connack_string(rc))

    # After a successful connect, reset backoff time and stop backing off.
    global should_backoff
    global minimum_backoff_time
    should_backoff = False


def on_disconnect(unused_client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print('on_disconnect', error_str(rc))

    # Since a disconnect occurred, the next loop iteration will wait with
    # exponential backoff.
    global should_backoff
    should_backoff = True


def on_publish(unused_client, unused_userdata, unused_mid):
    """Paho callback when a message is sent to the broker."""
    print('on_publish')


def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    try:
        payload = str(message.payload)
        config = json.loads(payload)

        #  Mender template config
        mender_config = {
            "InventoryPollIntervalSeconds": 30,
            "RetryPollIntervalSeconds": 30,
            "RootfsPartA": "/dev/mmcblk0p2",
            "RootfsPartB": "/dev/mmcblk0p3",

            "ClientProtocol": "http",
              "HttpsClient": {
            #  For this demo - we use a self-signed cert
            #  if you use a proper CA signed cert remove this
                "SkipVerify": True
              },
            #  If instead you want to use a custom private cert
            #  "ServerCertificate": "/etc/mender/server.crt",
            "ServerURL": "https://mender.gcpotademo.com",
            "TenantToken": "dummy",
            "UpdatePollIntervalSeconds": 30,
        }

        mender_config["ServerURL"] = config["mender_server"]
        mender_config["HttpsClient"]["SkipVerify"] = json.loads(config.get("SkipVerify", "true"))

        with open('/etc/mender/mender.conf', "w") as f:
            json.dump(mender_config, f)

        with open('/data/mender/preauth_true', "w") as f:
            f.write("ok")
        print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
                payload, message.topic, str(message.qos)))
        with open('/etc/hosts') as f:
            current_hosts = f.read()

        # add artifact alias
        if not 'gcs' in current_hosts:
            with open('/etc/hosts', 'a') as f:
                f.write("{}  gcs.mender.gcpotademo.com\n".format(config["mender_server"].lstrip('https://')))

        subprocess.call(["/bin/systemctl", "restart", "mender.service"])
        sys.exit(0)
    except ValueError:
        print("no valid config")



def get_client(
        project_id, cloud_region, registry_id, device_id, private_key_file,
        algorithm, ca_certs, mqtt_bridge_hostname, mqtt_bridge_port):
    """Create our MQTT client. The client_id is a unique string that identifies
    this device. For Google Cloud IoT Core, it must be in the format below."""
    with open("/data/gcp/mender-google-machine-id") as f:
        device_id = "g-%s" % f.readline().strip()
    print('projects/{}/locations/{}/registries/{}/devices/{}'
                       .format(
                               project_id,
                               cloud_region,
                               registry_id,
                               device_id))
    client = mqtt.Client(
            client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                       .format(
                               project_id,
                               cloud_region,
                               registry_id,
                               device_id)))

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    pw = create_jwt(project_id, private_key_file, algorithm)
    client.username_pw_set(
            username='unused',
            password=pw
            )

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connect to the Google MQTT bridge.
    client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

    # This is the topic that the device will receive configuration updates on.
    mqtt_config_topic = '/devices/{}/config'.format(device_id)

    # Subscribe to the config topic.
    client.subscribe(mqtt_config_topic, qos=1)

    return client



def main():
    global minimum_backoff_time

    # wait until the mender agent has created the device private key
    while not os.path.exists("/var/lib/mender/mender-agent.pem"):
        time.sleep(1)

    if not os.path.exists("/data/gcp/mender-google-machine-id"):
        while not os.path.exists("/etc/machine-id"):
            time.sleep(1)
        shutil.copy("/etc/machine-id", "/data/gcp/mender-google-machine-id")

    registry_id = None
    project_id = None
    cloud_region = None
    try:
        with open("/data/gcp/gcp-config.sh","r") as config_file:
            for line in config_file:
                if "export REGISTRY_ID=" in line:
                    registry_id = line.replace("export REGISTRY_ID=", "").replace('"', "").strip()
                if "export PROJECT_ID=" in line:
                    project_id = line.replace("export PROJECT_ID=", "").replace('"', "").strip()
                if "export REGION_ID=" in line:
                    cloud_region = line.replace("export REGION_ID=", "").replace('"', "").strip()
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
    except:
        print "Unexpected error:", sys.exc_info()[0]
    else:
        if registry_id == None:
            sys.exit("Error. REGISTRY_ID undefined")
        if project_id == None:
            sys.exit("Error. PROJECT_ID undefined")
        if cloud_region == None:
            sys.exit("Error. REGION_ID undefined")

    # Publish to the events or state topic based on the flag.
    sub_topic = 'state'
    device_id = subprocess.check_output(['/usr/share/mender/identity/mender-device-identity']).split('=')[1].strip()



    mqtt_topic = '/devices/{}/{}'.format(device_id, sub_topic)

    jwt_iat = datetime.datetime.utcnow()
    jwt_exp_mins = 20

    def make_client():
        client = get_client(
            project_id,
            cloud_region,
            registry_id,
            device_id,
            "/var/lib/mender/mender-agent.pem", #  private_key_file
            'RS256',
            #  TODO include this in bake at a different path
            "/data/gcp/roots.pem",
            "mqtt.googleapis.com",
            "443")
        return client
    client = make_client()
    while True:
        # Process network events.
        client.loop()

        # Wait if backoff is required.
        if should_backoff:
            # If backoff time is too large, give up.
            if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
                print('Reached maximum backoff time.')
                #  here we don't want to break, as we are awaiting auth completion break
            else:
                minimum_backoff_time *= 2

            # Otherwise, wait and connect again.
            delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
            print('Waiting for {} before reconnecting.'.format(delay))
            time.sleep(delay)
            jwt_iat = datetime.datetime.utcnow()
            client = make_client()


        seconds_since_issue = (datetime.datetime.utcnow() - jwt_iat).seconds
        if seconds_since_issue > 60 * jwt_exp_mins:
            print('Refreshing token after {}s').format(seconds_since_issue)
            jwt_iat = datetime.datetime.utcnow()
            client = make_client()

        time.sleep(1)


    print('Finished.')


if __name__ == '__main__':
    main()
