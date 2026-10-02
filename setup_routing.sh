#!/bin/bash
# chameleon-framework: Production Network Routing Setup
# This script configures iptables to silently redirect inbound traffic on Port 22
# to the Cowrie honeypot running on Port 2222.
# 
# PREREQUISITES:
# 1. Change your real SSH daemon (sshd_config) to listen on a non-standard port (e.g. 49152).
# 2. Restart your sshd service.
# 3. Ensure Cowrie is running on 127.0.0.1:2222 or 0.0.0.0:2222.
# 4. Run this script as root.

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

REAL_SSH_PORT=49152
HONEYPOT_PORT=2222

echo "Configuring iptables for Chameleon Honeypot..."

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# Redirect inbound external traffic on port 22 to the honeypot port 2222
iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port $HONEYPOT_PORT

# (Optional) Drop connections to the real SSH port from the outside world, 
# forcing admin access only from VPN or specific trusted IPs.
# iptables -A INPUT -p tcp --dport $REAL_SSH_PORT -s 10.0.0.0/8 -j ACCEPT
# iptables -A INPUT -p tcp --dport $REAL_SSH_PORT -j DROP

echo "Routing successful."
echo "Traffic to Port 22 is now being captured by the honeypot on Port $HONEYPOT_PORT."
echo "Ensure your actual SSH server is safely running on Port $REAL_SSH_PORT."
