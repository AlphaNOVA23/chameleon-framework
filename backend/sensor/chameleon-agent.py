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

def parse_args():
    parser = argparse.ArgumentParser(description="Chameleon Remote Sensor Agent")
    parser.add_argument("--token", required=True, help="Sensor authentication token")
    parser.add_argument("--server", default="http://localhost:8000", help="Chameleon backend server URL")
    parser.add_argument("--logfile", default="/var/log/cowrie/cowrie.json", help="Path to cowrie.json log")
    return parser.parse_args()

def send_event(server, token, event):
    url = f"{server.rstrip('/')}/api/ingest"
    payload = json.dumps({"token": token, "event": event}).encode("utf-8")
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
            
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        print(f"[Chameleon-Agent] Tailing {filename}...")
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            try:
                event = json.loads(line.strip())
                yield event
            except Exception:
                continue

def main():
    args = parse_args()
    print(f"[Chameleon-Agent] Starting sensor agent...")
    print(f"[Chameleon-Agent] Server: {args.server}")
    print(f"[Chameleon-Agent] Logfile: {args.logfile}")
    
    for event in tail_file(args.logfile):
        send_event(args.server, args.token, event)

if __name__ == "__main__":
    main()
