#!/bin/bash

# Define the name of the daemon
DAEMON_NAME="eggcounter"

# Copy the daemon executable to the appropriate location

# Create a systemd service file for the daemon
File_txt='
[Unit]
Description = "Egg counter service"

[Service]
Type = simple
WorkingDirectory=/home/pi/EggCounter
User=pi
ExecStart=/usr/bin/python3 /home/pi/EggCounter/eggcounter.py
Restart=always

[Install]
WantedBy=multi-user.target'

sudo printf "$File_txt" > /etc/systemd/system/$DAEMON_NAME.service
# Reload systemd to pick up the new service file
sudo systemctl daemon-reload

# Enable and start the daemon
sudo systemctl enable $DAEMON_NAME
sudo systemctl start $DAEMON_NAME