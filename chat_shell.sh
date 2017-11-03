#!/bin/bash

#PATH=/bin;/sbin;/usr/bin;/usr/sbin;/usr/local/bin;/usr/local/sbin;~/bin
#export PATH
#echo -e 'Hello World!\n'


PATH=$PATH:/opt/lampp:
sudo env "PATH=$PATH" xampp restart

RESULT=$(pgrep ngrok || echo no)
if [ "${RESULT}" = "no" ] ; then
    gnome-terminal -x ./ngrok http 5000
fi

sleep 3

python3 app.py
exit 0
