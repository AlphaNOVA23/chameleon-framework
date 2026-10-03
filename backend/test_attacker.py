#!/usr/bin/env python3
"""
Chameleon Framework — Attack Simulator & Test Suite
Simulates Bot (Tier 1), AI Agent (Tier 2), and Human (Tier 3) SSH attacks to verify live biometric classification & Groq LLM deception.
"""
import time
import json
import random
import sys
import urllib.request

SERVER_URL = "http://localhost:8000" if len(sys.argv) < 2 else sys.argv[1]
TOKEN = "CHAM_SENS_01_KEY"

def send_simulated_event(session_id, eventid, src_ip, username=None, password=None, command=None):
    event = {
        "session": session_id,
        "eventid": eventid,
        "src_ip": src_ip,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    }
    if username: event["username"] = username
    if password: event["password"] = password
    if command: event["input"] = command

    url = f"{SERVER_URL.rstrip('/')}/api/ingest"
    payload = json.dumps({"token": TOKEN, "event": event}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status == 200
    except Exception as e:
        print(f"[Test Attacker] Ingest failed: {e}")
        return False

def run_bot_attack():
    """Tier 1 Bot: <0.25s command delay"""
    sid = f"bot_{random.randint(1000, 9999)}"
    ip = f"185.220.{random.randint(10,250)}.{random.randint(1,250)}"
    print(f"\n[+] Starting Tier 1 Bot Attack (Fast Script) | Session: {sid} | IP: {ip}")
    send_simulated_event(sid, "cowrie.session.connect", ip)
    send_simulated_event(sid, "cowrie.login.success", ip, "root", "admin123")
    
    commands = ["uname -a", "cat /etc/passwd", "uptime", "whoami", "id", "exit"]
    for cmd in commands:
        print(f"  -> Executing: {cmd} (delay: 0.08s)")
        send_simulated_event(sid, "cowrie.command.input", ip, command=cmd)
        time.sleep(0.08) # 80ms delay = Bot
        
    send_simulated_event(sid, "cowrie.session.closed", ip)
    print(f"[✓] Tier 1 Bot Attack completed. Expected classification: TIER_1_BOT")

def run_ai_agent_attack():
    """Tier 2 AI Agent: 0.5s - 1.2s command delay"""
    sid = f"agent_{random.randint(1000, 9999)}"
    ip = f"194.26.{random.randint(10,250)}.{random.randint(1,250)}"
    print(f"\n[+] Starting Tier 2 AI Agent Attack (LLM Recon Tool) | Session: {sid} | IP: {ip}")
    send_simulated_event(sid, "cowrie.session.connect", ip)
    send_simulated_event(sid, "cowrie.login.success", ip, "admin", "password123")
    
    commands = ["env", "cat aws_credentials.ini", "cat /etc/app_config.json", "ps aux", "ls -la"]
    for cmd in commands:
        print(f"  -> Executing: {cmd} (delay: 0.75s)")
        send_simulated_event(sid, "cowrie.command.input", ip, command=cmd)
        time.sleep(0.75) # 750ms delay = AI Agent
        
    send_simulated_event(sid, "cowrie.session.closed", ip)
    print(f"[✓] Tier 2 AI Agent Attack completed. Expected classification: TIER_2_AGENT (Triggers Groq Honeytoken)")

def run_human_attack():
    """Tier 3 Human: >2.0s command delay"""
    sid = f"human_{random.randint(1000, 9999)}"
    ip = f"45.142.{random.randint(10,250)}.{random.randint(1,250)}"
    print(f"\n[+] Starting Tier 3 Human Attack (Manual Keyboard) | Session: {sid} | IP: {ip}")
    send_simulated_event(sid, "cowrie.session.connect", ip)
    send_simulated_event(sid, "cowrie.login.success", ip, "operator", "secpassword")
    
    commands = ["ls -l /home/admin", "cat /etc/shadow", "history", "netstat -tulpn"]
    for cmd in commands:
        delay = round(random.uniform(2.1, 3.5), 2)
        print(f"  -> Executing: {cmd} (delay: {delay}s)")
        send_simulated_event(sid, "cowrie.command.input", ip, command=cmd)
        time.sleep(delay) # 2.1-3.5s delay = Human
        
    send_simulated_event(sid, "cowrie.session.closed", ip)
    print(f"[✓] Tier 3 Human Attack completed. Expected classification: TIER_3_HUMAN (Triggers SOC Alert)")

if __name__ == "__main__":
    print(f"Target Chameleon Backend: {SERVER_URL}")
    run_bot_attack()
    time.sleep(2)
    run_ai_agent_attack()
    time.sleep(2)
    run_human_attack()
