#!/usr/bin/env python3
"""
Chameleon Framework — Real SSH Protocol Bot Simulator
Connects over SSH (Port 2222 or Port 22) to the Cowrie Honeypot Docker Container
and executes rapid automated commands over the network socket.
"""
import sys
import time
import subprocess

def run_ssh_bot(host="127.0.0.1", port=2222):
    print(f"\n[+] Launching Real SSH Protocol Bot Attack against SSH Honeypot at {host}:{port}...")
    
    # Try paramiko SSH client first
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"[+] Establishing SSH TCP connection to {host}:{port}...")
        ssh.connect(host, port=port, username="root", password="password123", timeout=5)
        
        commands = ["uname -a", "cat /etc/passwd", "whoami", "id", "uptime", "exit"]
        print("[+] Executing automated bot command sequence over SSH socket (rapid 50ms delay)...")
        for cmd in commands:
            print(f"  [SSH Bot -> Honeypot] {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()
            time.sleep(0.05) # 50ms rapid bot execution
            
        ssh.close()
        print("[✓] Real SSH Bot Attack complete! Telemetry streamed via Cowrie agent to Chameleon Dashboard.")
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"[!] Paramiko SSH connection attempt: {e}")

    # Fallback using system SSH client
    print("[+] Using system SSH client to stream bot commands over SSH socket...")
    ssh_cmd = f'ssh -o StrictHostKeyChecking=no -p {port} root@{host} "uname -a; cat /etc/passwd; whoami; id; uptime"'
    try:
        subprocess.run(ssh_cmd, shell=True)
        print("[✓] SSH Bot Attack complete!")
    except Exception as e:
        print(f"[!] System SSH command failed: {e}")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 2222
    run_ssh_bot(port=port)
