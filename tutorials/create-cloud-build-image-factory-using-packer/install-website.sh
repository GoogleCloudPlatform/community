#!/bin/sh 
sudo yum install -y epel-release
sudo yum install -y nginx
sudo chkconfig nginx on
LOCATION_OF_INDEX=/usr/share/nginx/html/index.html
sudo bash -c "cat <<A_VERY_SPECIAL_MESSAGE>$LOCATION_OF_INDEX
<html>
<h2> Hello, from the image factory! </h2>
</html> 

A_VERY_SPECIAL_MESSAGE
"
