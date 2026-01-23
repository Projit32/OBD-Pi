#!/bin/bash
rfkill unblock bluetooth
bluetoothctl -- power on
rfcomm connect /dev/rfcomm0 $OBD_MAC_ID $OBD_CANNEL_ID & sleep(2) & python $WORK_DIR/OBD-Pi/app.py