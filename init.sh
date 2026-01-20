#!/bin/bash

apt-get -y update
apt-get -y upgrade
apt-get -y pwdinstall bluetooth bluez
WORK_DIR=$(pwd)
echo $WORK_DIR
mkdir -p $WORK_DIR/obd
cd $WORK_DIR/obd
pwd
python -m venv obd-env
source obd-env/bin/activate
git clone https://github.com/Projit32/OBD-Pi.git
pip install -r ./OBD-Pi/requirements.txt

cd OBD-Pi
touch runtime.env
echo "WORK_DIR=$WORK_DIR/OBD-Pi" >> runtime.env
