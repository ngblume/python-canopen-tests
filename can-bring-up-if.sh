#!/bin/bash

# Script to bring up the USBtin as SocketCAN

sudo /home/ngblume/git-repos/can-utils/slcan_attach -f -s5 -o /dev/ttyACM0
sudo /home/ngblume/git-repos/can-utils/slcand ttyACM0 can0
sudo ifconfig can0 up
