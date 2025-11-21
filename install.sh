#!/bin/bash

echo "Installing Ubuntu DNS Manager Pro..."

# 1. Install Dependencies
echo "Updating & Installing system dependencies..."
sudo apt-get update
# python3-pip added for font fixing libraries
sudo apt-get install -y python3-tk bind9-dnsutils iputils-ping curl python3-pip

# 2. Install Python Libraries (for Persian Text Support)
echo "Installing Python libraries..."
# Break-system-packages flag might be needed on newer Ubuntu versions (23.04+),
# otherwise standard pip install works.
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt

# 3. Setup Directory
INSTALL_DIR="/opt/UbuntuDNSManager"
echo "Setting up $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r src data docs requirements.txt "$INSTALL_DIR"

# 4. Create Launcher
DESKTOP_FILE="/usr/share/applications/ubuntu-dns-manager.desktop"
echo "Creating shortcut..."

sudo bash -c "cat > $DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=2.0
Name=Ubuntu DNS Manager
Comment=Advanced DNS Management & Benchmark
Exec=sudo python3 $INSTALL_DIR/src/main.py
Icon=preferences-system-network
Terminal=true
Type=Application
Categories=Network;Settings;
EOF

# 5. Permissions
sudo chmod +x $DESKTOP_FILE
sudo chmod -R 755 "$INSTALL_DIR"

echo "Done! Search for 'Ubuntu DNS Manager' in your apps."