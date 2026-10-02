#!/usr/bin/env python3
"""
Chameleon Framework — Single-Session Interactive SSH Bot Simulator
Connects over SSH to the Cowrie Honeypot, authenticates automatically,
and streams multiple commands down a SINGLE active SSH shell session.
"""
import sys
import time
import paramiko

def run_ssh_bot(host="127.0.0.1", port=22):
    print(f"\n[+] Launching Single-Session SSH Bot Attack against {host}:{port}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"[+] Connecting & Authenticating to SSH Honeypot on port {port}...")
        ssh.connect(host, port=port, username="root", password="admin123", timeout=10)
        
        # Open single interactive shell channel
        channel = ssh.invoke_shell()
        time.sleep(1) # wait for shell prompt
        
        commands = [
            "uname -a",
            "whoami",
            "id",
            "cat /etc/passwd",
            "uptime",
            "cat /etc/shadow",
            "exit"
        ]
        
        print(f"[+] Streaming {len(commands)} bot commands down SINGLE SSH channel (120ms delay)...")
        for cmd in commands:
            print(f"  [SSH Bot -> Channel] {cmd}")
            channel.send(cmd + "\n")
            time.sleep(0.12) # 120ms inter-arrival timing = TIER 1 BOT
            
            # Read output available
            if channel.recv_ready():
                channel.recv(2048)
                
        time.sleep(0.5)
        ssh.close()
        print("\n[✓] Single-Session SSH Bot Attack Completed Successfully!")
        print("    -> 1 Single Session ID created")
        print("    -> 0 Password prompts required")
        print("    -> Inter-Arrival Time ~0.12s -> Classified as TIER_1_BOT")
        
    except Exception as e:
        print(f"[!] SSH Bot Error: {e}")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    run_ssh_bot(port=port)
