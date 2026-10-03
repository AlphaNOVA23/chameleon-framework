#!/usr/bin/env python3
"""
Chameleon Lightweight Sensor Agent
Tails honeypot events from Cowrie JSON log and streams them to Chameleon Cloud API.
"""
import os
import sys
import time
import json
import argparse
import urllib.request
import urllib.parse

def find_logfile(user_path=None):
    if user_path and os.path.exists(user_path):
        return os.path.abspath(user_path)
    
    candidates = [
        r"C:\Users\tanma\cowrie_logs\cowrie.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "honeypot", "logs2", "cowrie.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "honeypot", "logs2", "cowrie.json"),
        os.path.join(os.getcwd(), "honeypot", "logs2", "cowrie.json"),
        "/var/log/cowrie/cowrie.json"
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return user_path or "/var/log/cowrie/cowrie.json"

def parse_args():
    parser = argparse.ArgumentParser(description="Chameleon Remote Sensor Agent")
    parser.add_argument("--token", required=True, help="Sensor authentication token")
    parser.add_argument("--user_id", default="admin", help="Tenant user account ID / email")
    parser.add_argument("--server", default="http://localhost:8000", help="Chameleon backend server URL")
    parser.add_argument("--logfile", default=None, help="Path to cowrie.json log")
    return parser.parse_args()

def send_event(server, token, event, user_id="admin"):
    url = f"{server.rstrip('/')}/api/ingest"
    payload = json.dumps({"token": token, "user_id": user_id, "event": event}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"[Chameleon-Agent] Failed to post event: {e}")
        return False

def tail_file(filename):
    if not os.path.exists(filename):
        print(f"[Chameleon-Agent] Waiting for logfile {filename} to exist...")
        while not os.path.exists(filename):
            time.sleep(2)

    f = open(filename, "r", encoding="utf-8", errors="ignore")
    f.seek(0, os.SEEK_END)
    print(f"[Chameleon-Agent] Tailing new events from end of {filename}...")
    file_stat = os.fstat(f.fileno())

    while True:
        try:
            path_stat = os.stat(filename)
        except FileNotFoundError:
            time.sleep(0.5)
            continue

        if not os.path.samestat(file_stat, path_stat):
            f.close()
            f = open(filename, "r", encoding="utf-8", errors="ignore")
            file_stat = os.fstat(f.fileno())
            print(f"[Chameleon-Agent] Reopened replaced logfile {filename} from start")
            continue

        if path_stat.st_size < f.tell():
            f.seek(0)
            print(f"[Chameleon-Agent] Detected truncated logfile {filename}; resuming from start")

        line = f.readline()
        if not line:
            time.sleep(0.5)
            continue
        try:
            event = json.loads(line.strip())
            if isinstance(event, dict):
                yield event
        except Exception:
            continue

def main():
    args = parse_args()
    logfile = find_logfile(args.logfile)
    print(f"[Chameleon-Agent] Starting sensor agent...")
    print(f"[Chameleon-Agent] Server: {args.server}")
    print(f"[Chameleon-Agent] Logfile: {logfile}")
    
    for event in tail_file(logfile):
        if send_event(args.server, args.token, event, user_id=args.user_id):
            event_id = event.get("eventid", "")
            if event_id in ("cowrie.session.connect", "cowrie.command.input", "cowrie.session.closed"):
                print(f"[Chameleon-Agent] Ingested {event_id} for session {event.get('session', '?')}")

if __name__ == "__main__":
    main()
