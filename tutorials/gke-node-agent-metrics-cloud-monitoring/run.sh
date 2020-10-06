#!/bin/bash

configuration_file="/etc/collectd/collectd.conf"
monitored_resource=$(curl --silent -f -H 'Metadata-Flavor: Google' http://169.254.169.254/computeMetadata/v1/instance/id 2>/dev/null)

sed -i "s/%MONITORED_RESOURCE%/$monitored_resource/" "$configuration_file"

/opt/stackdriver/collectd/sbin/stackdriver-collectd -f -C "$configuration_file"
