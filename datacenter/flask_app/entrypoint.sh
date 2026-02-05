#!/bin/bash

# Start Telegraf in the background
/usr/bin/telegraf -config /etc/telegraf/telegraf.conf &

# Start Flask app in the foreground
python app.py
