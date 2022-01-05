# Base this image on core-image-base
include recipes-core/images/core-image-base.bb

SUMMARY = "A console-only image to demonstrate Google Cloud IOT integration \
with Mender OTA Update capability."

SPLASH_rpi = "psplash-raspberrypi"

IMAGE_FEATURES += "ssh-server-openssh"

IMAGE_INSTALL_append = " \
                     kernel-image \
                     kernel-devicetree \
                     kernel-modules \
                     networkmanager \
                     mender-wait-for-timesync \
                     python-paho-mqtt \
                     python-pip \
                     python-grpcio-tools \
                     python-cryptography \
                     python-pyjwt \
                     mender-gcp-delay-server-connection \
                     mender-google-activation-agent \
"

###DISTRO_FEATURES_append += " wifi"
### IMAGE_INSTALL_append += " \
###                      linux-firmware-bcm43430
### "

inherit extrausers
EXTRA_USERS_PARAMS = "usermod -P mender_gcp_ota root;"

MENDER_DATA_PART_DIR = "${DEPLOY_DIR_IMAGE}/persist"
