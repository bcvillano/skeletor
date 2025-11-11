#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Script must be run as root"
  exit
fi

echo "Moving Skeletor files to /usr/local/bin..."
cp ./skelctl.py /usr/local/bin/skelctl
chmod 755 /usr/local/bin/skelctl
chown root:root /usr/local/bin/skelctl

cp ./skeletor.py /usr/local/bin/skeletor
chmod 755 /usr/local/bin/skeletor
chown root:root /usr/local/bin/skeletor

echo "Setting Up Skeletor Service..."
cp ./skeletor.service /etc/systemd/system/skeletor.service
systemctl daemon-reload
#systemctl enable skeletor

echo "Skeletor installed successfully"
echo "To run Skeletor as a service, use the command: systemctl start skeletor"