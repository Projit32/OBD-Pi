#!/bin/bash

apt-get -y update
apt-get -y upgrade
apt-get -y pwdinstall bluetooth bluez

git clone https://github.com/Projit32/OBD-Pi.git obd-pi
cd obd-pi
WORK_DIR=$(pwd)
echo $WORK_DIR
python -m venv $WORK_DIR/obd-env
source $WORK_DIR/obd-env/bin/activate
pip install -r ./requirements.txt
#touch config.env
#echo "WORK_DIR=$WORK_DIR" >> config.env
