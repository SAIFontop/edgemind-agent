#!/bin/bash
# EdgeMind Agent - Service Installation Script
# Installs EdgeMind as a systemd service

SERVICE_NAME="edgemind"
INSTALL_DIR="/opt/edgemind-agent"
USER="pi"

echo "Installing EdgeMind Agent as systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Create installation directory
echo "Creating installation directory..."
mkdir -p $INSTALL_DIR
cp -r . $INSTALL_DIR/
chown -R $USER:$USER $INSTALL_DIR

# Create service file
echo "Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=EdgeMind Agent - AI System Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/bin
ExecStart=$INSTALL_DIR/venv/bin/python main.py --web
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable $SERVICE_NAME

echo ""
echo "Service installed successfully!"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Web interface will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
