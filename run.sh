#!/bin/bash

source config.env
rfkill unblock bluetooth
bluetoothctl -- power on
source $WORK_DIR/obd-env/bin/activate
rfcomm connect /dev/rfcomm0 $OBD_MAC_ID $OBD_CANNEL_ID &
sleep 2
python $WORK_DIR/OBD-Pi/app.py