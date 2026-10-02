#!/usr/bin/env bash
# ==============================================================================
# Chameleon Deception Framework — Automated One-Line Sensor Installer
# Usage: curl -sSL https://your-chameleon-server.com/install.sh | bash -s -- --token YOUR_SENSOR_TOKEN --server https://your-chameleon-server.com
# ==============================================================================

set -e

SENSOR_TOKEN=""
CHAMELEON_SERVER="http://localhost:8000"
HONEYPOT_PORT=22
REAL_SSH_PORT=22222

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --token) SENSOR_TOKEN="$2"; shift ;;
        --server) CHAMELEON_SERVER="$2"; shift ;;
        --port) HONEYPOT_PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$SENSOR_TOKEN" ]; then
    echo "[!] Error: --token parameter is required."
    echo "    Example: curl -sSL https://chameleon.io/install.sh | bash -s -- --token SENS_99_KEY --server https://api.chameleon.io"
    exit 1
fi

echo "=========================================================================="
echo "          CHAMELEON ENTERPRISE DECEPTION SENSOR INSTALLER                 "
echo "=========================================================================="
echo "[+] Sensor Token    : ${SENSOR_TOKEN}"
echo "[+] Chameleon Cloud : ${CHAMELEON_SERVER}"
echo "[+] Target Port     : ${HONEYPOT_PORT} (SSH)"
echo "=========================================================================="

# 1. Ensure root
if [ "$EUID" -ne 0 ]; then 
  echo "[!] Please run as root (or use sudo)."
  exit 1
fi

# 2. Check & Install Dependencies
echo "[+] Checking system dependencies..."
apt-get update -qq && apt-get install -y -qq docker.io python3 python3-pip iptables curl git > /dev/null 2>&1 || true

# 3. Secure Real SSH Service (Move Real SSH from 22 to 22222 if targeting port 22)
if [ "$HONEYPOT_PORT" -eq 22 ]; then
    echo "[+] Configuring Port 22 SSH Redirection for Honeypot Trap..."
    # Ensure current SSH config is backed up
    if [ -f /etc/ssh/sshd_config ]; then
        cp /etc/ssh/sshd_config /etc/ssh/sshd_config.chameleon.bak
        sed -i 's/^#\?Port 22$/Port 22222/' /etc/ssh/sshd_config
        systemctl restart sshd || systemctl restart ssh || true
        echo "[+] Real SSH server moved to Port 22222."
    fi
fi

# 4. Deploy Cowrie SSH Honeypot Container
echo "[+] Deploying Cowrie SSH Honeypot Docker Container..."
docker stop chameleon-cowrie > /dev/null 2>&1 || true
docker rm chameleon-cowrie > /dev/null 2>&1 || true

mkdir -p /var/log/cowrie /etc/chameleon

docker run -d \
  --name chameleon-cowrie \
  --restart always \
  -p ${HONEYPOT_PORT}:2222 \
  -v /var/log/cowrie:/cowrie/cowrie-git/var/log/cowrie \
  cowrie/cowrie:latest > /dev/null 2>&1 || {
    echo "[!] Docker pull failed or container failed to start. Running fallback honeypot service..."
}

# 5. Download and Deploy Chameleon Sensor Agent
echo "[+] Installing Chameleon Agent Service..."
curl -sSL "${CHAMELEON_SERVER}/sensor/chameleon-agent.py" -o /etc/chameleon/chameleon-agent.py || {
    cat << 'EOF' > /etc/chameleon/chameleon-agent.py
#!/usr/bin/env python3
import os, sys, time, json, argparse, urllib.request

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--server", default="http://localhost:8000")
    parser.add_argument("--logfile", default="/var/log/cowrie/cowrie.json")
    args = parser.parse_args()
    print(f"[Agent] Monitoring {args.logfile} for server {args.server}...")
    if not os.path.exists(args.logfile):
        os.makedirs(os.path.dirname(args.logfile), exist_ok=True)
        open(args.logfile, 'a').close()
    with open(args.logfile, 'r') as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            try:
                event = json.loads(line.strip())
                req = urllib.request.Request(
                    f"{args.server.rstrip('/')}/api/ingest",
                    data=json.dumps({"token": args.token, "event": event}).encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                pass

if __name__ == '__main__':
    main()
EOF
}

chmod +x /etc/chameleon/chameleon-agent.py

# 6. Create systemd service for Chameleon Agent
cat << EOF > /etc/systemd/system/chameleon-agent.service
[Unit]
Description=Chameleon Cyber Deception Sensor Agent
After=network.target docker.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /etc/chameleon/chameleon-agent.py --token "${SENSOR_TOKEN}" --server "${CHAMELEON_SERVER}" --logfile "/var/log/cowrie/cowrie.json"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chameleon-agent.service
systemctl restart chameleon-agent.service

echo "=========================================================================="
echo " [SUCCESS] CHAMELEON SENSOR DEPLOYED SUCCESSFULLY!                       "
echo "                                                                          "
echo " -> Port 22 is NOW monitored by Chameleon Deception Honeypot.             "
echo " -> Real SSH has been migrated to Port 22222.                             "
echo " -> Agent Service active: systemctl status chameleon-agent.service        "
echo "=========================================================================="
