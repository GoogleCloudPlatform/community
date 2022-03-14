#!/usr/bin/env sh

set -eu

SETTINGS_FILE=/var/www/html/app/config/parameters.php

# set database
sed -i "/'database_host'/c\    'database_host' => '$DB_SERVER'," $SETTINGS_FILE 
sed -i "/'database_name'/c\    'database_name' => '$DB_NAME'," $SETTINGS_FILE
sed -i "/'database_user'/c\    'database_user' => '$DB_USER'," $SETTINGS_FILE
sed -i "/'database_password'/c\    'database_password' => '$DB_PASSWD'," $SETTINGS_FILE

exec /sbin/runit-init
