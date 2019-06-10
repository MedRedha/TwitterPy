#!/bin/bash

# This is a script to mitigate possibility of multiple parallel cron jobs being triggered(discussed here: https://github.com/timgrossmann/TwitterPy/issues/1235)
# The following is an example of a cron scheduled every 10 mins
# */10 * * * * bash /path/to/TwitterPy/run_twitterpy_only_once_for_mac.sh /path/to/TwitterPy/quickstart.py $USERNAME $PASSWORD

TEMPLATE_PATH=$1
USERNAME=$2
PASSWORD=$3
EMAIL=$4
if [ -z "$4" ]
then
   echo "Error: Missing arguments"
   echo "Usage: bash $0 <script-path> <username> <password>"
   exit 1
fi

if ps aux | grep $TEMPLATE_PATH | awk '{ print $11 }' | grep python
then
   echo "$TEMPLATE_PATH is already running"
else
   echo "Starting $TEMPLATE_PATH"
   # /Users/ishandutta2007/.pyenv/shims/python $TEMPLATE_PATH -u $USERNAME -p $PASSWORD -e $EMAIL --disable_image_load
   /Users/ishandutta2007/.pyenv/shims/python $TEMPLATE_PATH -u $USERNAME -p $PASSWORD -e $EMAIL --headless-browser --disable_image_load
fi
