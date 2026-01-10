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
