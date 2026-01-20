#!/bin/bash
# Select bluetooth device

# set it in env

# remove desktop and make cli only

# setup service

SERVICE_NAME="obd"
SCRIPT_PATH="$WORK_DIR/run.sh"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

touch $SERVICE_FILE
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=OBD Scanner Python App
After=network.target

[Service]
Type=oneshot
ExecStart=$SCRIPT_PATH
User=root
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Make the target script executable
sudo chmod +x $SCRIPT_PATH

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable ${SERVICE_NAME}.service

# Start the service
sudo systemctl start ${SERVICE_NAME}.service

# Show status
sudo systemctl status ${SERVICE_NAME}.service

echo "Service ${SERVICE_NAME}.service has been created and enabled!"