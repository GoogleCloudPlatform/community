"""Binary for running Mosquitto MQTT bridge with credential rotation."""
import datetime
import os
import signal
import subprocess
import time
import jwt
import psutil


def create_jwt_token():
  """Creates a JWT (https://jwt.io) to establish an MQTT connection.

  Returns:
      An MQTT auth token generated from the given project_id and private
      key
  Raises:
      ValueError: If the private_key_file does not contain a known key.
  """

  token = {
      # The time that the token was issued at
      'iat':
          datetime.datetime.utcnow(),
      # The time the token expires.
      'exp':
          datetime.datetime.utcnow() +
          datetime.timedelta(minutes=int(os.environ["JWT_EXPIRATION_MINUTES"])),
      # The audience field should always be set to the GCP project id.
      'aud':
          os.environ["PROJECT_ID"]
  }

  # Read the private key file.
  with open("/etc/mqtt/ec_private.pem", 'r') as f:
    private_key = f.read()

  print ('Creating JWT from private key file')
  return jwt.encode(token, private_key, algorithm='ES256').decode('utf-8')


def update_config(config):
  """Updates mosquitto condig file on disk.

  Args:
    config: path to the Mosquitto config
  """
  # TODO proper template tooling?
  config = config.replace('GOOGLE_CLOUD_JWT', create_jwt_token()).replace(
      'CONFIG_DEVICE_ID', os.environ["BRIDGE_DEVICE_ID"]).replace(
          'CONFIG_PROJECT_ID', os.environ["PROJECT_ID"]).replace(
              'CONFIG_LOCATION', os.environ["CLOUD_REGION"]).replace(
                  'CONFIG_REGISTRY', os.environ["REGISTRY_ID"]).replace(
                      'BASE_DIR', '/etc/mqtt')

  with open("/mosquitto/config/mosquitto.conf", 'w') as dst_conf:
    dst_conf.write(config)

  print ('Wrote config to {}'.format("/mosquitto/config/mosquitto.conf"))


def main():
  with open("/etc/mqtt/bridge.conf.tmpl", 'r') as src_conf:
    config_template = src_conf.read()

  update_config(config_template)

  while True:
    time.sleep(int(os.environ["CONFIG_REFRESH_MINUTES"]) * 60)
    print ('Restarting MQTT Bridge')
    update_config(config_template)
    procs = [procObj for procObj in psutil.process_iter() if 'mosquitto' in procObj.name().lower() ]
    if len(procs):
      procs[0].send_signal(signal.SIGTERM)


if __name__ == '__main__':
  main()