#!/bin/bash
rfkill unblock bluetooth
rfcomm connect /dev/rfcomm0 $OBD_MAC_ID $OBD_CANNEL_ID
python $WORK_DIR/OBD-Pi/app.py