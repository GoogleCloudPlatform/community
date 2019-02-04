#!/bin/sh
webserv=$1
keyword=$2
echo "curl " http://$webserv " | grep '" $keyword "'"
if curl http://"$webserv"/health | grep "$keyword" > /dev/null
then
    # if the keyword is in the content
    echo "success" 
    exit 0
else
    echo "error"
    exit 1 
fi

