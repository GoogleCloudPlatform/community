#! /bin/bash

# Simple installer script for COAP Proxy
# It's not very smart, but it will set things up for testing purposes
#
# The script will look for the JAR file where it is normally built or
# the path to the JAR can be passed as an argument to this script.
# 
# Tested on Debian 9
# 

if [ "$1" != "" ]; then
  JARFILE="$1"
else
  JARFILE="../target/coap-iot-core-1.0-SNAPSHOT.jar"
fi

if [ ! -f "$JARFILE" ]; then
  echo "JAR file not found. Specify it as the first argument or try building it with this command (from the project root):"
  echo "mvn clean package"
  exit 1
fi

if [ $UID -ne 0 ]; then
  echo "Please run this installer as root."
  exit 1
fi
INSTALL_DIR="/usr/local/coap-proxy"
LOG_DIR="/var/log/coap-proxy"

mkdir -p $INSTALL_DIR

cp -v $JARFILE $INSTALL_DIR
adduser --disabled-password --gecos "" --no-create-home --home $INSTALL_DIR coap-proxy
chown coap-proxy.coap-proxy $INSTALL_DIR
cp -v -n coap-proxy.conf /etc/

# Copy init script
cp coap-proxy-init /etc/init.d/coap-proxy
chmod +x /etc/init.d/coap-proxy
update-rc.d coap-proxy defaults

# Setup Log Dir
mkdir -p $LOG_DIR
chown coap-proxy.coap-proxy $LOG_DIR
cp -v coap-proxy-logrotate /etc/logrotate.d/coap-proxy

echo
echo "Make sure to edit /etc/coap-proxy.conf to change the DTLS shared secret config!"

