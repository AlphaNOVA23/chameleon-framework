import asyncio
import json
import os
import glob
from datetime import datetime
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from orchestrator.log_tailer import parse_tty_chunk, read_new_bytes
from orchestrator.biometric import calculate_metrics, classify
from orchestrator.semantic_engine import analyze_command
from orchestrator.deception_engine import generate_deception_action

app = FastAPI(title="Chameleon Orchestrator API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_LOG = os.path.join(BASE_DIR, "honeypot", "logs2", "cowrie.json")
TTY_DIR = os.path.join(BASE_DIR, "honeypot", "tty")

active_connections = []
sessions = {}

def get_json_metrics(s):
    if len(s["cmd_timestamps"]) < 2:
        return 0.0, 0.0, []
    iats = []
    for i in range(1, len(s["cmd_timestamps"])):
        iat = (s["cmd_timestamps"][i] - s["cmd_timestamps"][i-1]).total_seconds()
        if 0 < iat < 60:
            iats.append(iat)
    if not iats:
        return 0.0, 0.0, []
    return float(np.mean(iats)), float(np.var(iats)), iats

async def broadcast(payload):
    for ws in active_connections:
        try:
            await ws.send_json(payload)
        except:
            pass

async def tail_logs():
    json_pos = 0
    # Removed getsize check so we read the entire file on startup
    # This prevents us from missing sessions that started before the backend.
        
    while True:
        # JSON Polling (Fallback / Command level)
        try:
            if os.path.exists(JSON_LOG):
                with open(JSON_LOG, 'r') as f:
                    f.seek(json_pos)
                    lines = f.readlines()
                    json_pos = f.tell()
                    
                for line in lines:
                    try:
                        event = json.loads(line.strip())
                    except:
                        continue
                        
                    sid = event.get("session", "")
                    eid = event.get("eventid", "")
                    
                    if sid not in sessions:
                        sessions[sid] = {"src_ip": event.get("src_ip", "?"), "tty_log": None, "tty_pos": 0, 
                                         "timestamps": [], "keys": [], "cmds": [], "tier": "UNKNOWN", "cmd_timestamps": [],
                                         "connected_at": event.get("timestamp", ""), "closed": False, "duration_ms": 0}
                        
                    s = sessions[sid]
                    
                    if eid == "cowrie.session.connect":
                        s["src_ip"] = event.get("src_ip", "?")
                        s["connected_at"] = event.get("timestamp", "")
                        await broadcast({"type": "SESSION_NEW", "session_id": sid, "src_ip": s["src_ip"], "timestamp": s["connected_at"]})
                        
                    elif eid == "cowrie.command.input":
                        cmd = event.get("input", "")
                        ts_str = event.get("timestamp", "")
                        try:
                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            s["cmd_timestamps"].append(ts)
                        except:
                            pass
                            
                        s["cmds"].append(cmd)
                        # ALWAYS calculate metrics and analyze command
                        mean_iat, var_iat, iats = get_json_metrics(s)
                        if mean_iat > 0:
                            # Bots are basically 0. Agents are ~1-3s. Humans are anything > 0.3s
                            s["tier"] = "TIER_3_HUMAN" if mean_iat > 0.3 else "TIER_1_BOT"
                        
                        intent = analyze_command(cmd)
                        deception = generate_deception_action(s["tier"], intent)
                        
                        await broadcast({
                            "type": "COMMAND",
                            "session_id": sid,
                            "command": cmd,
                            "classification": s["tier"],
                            "intent": intent,
                            "deception": deception,
                            "metrics": {
                                "mean_iat": round(mean_iat, 4),
                                "variance_iat": round(var_iat, 4),
                                "num_commands": len(s["cmds"]),
                                "recent_iats": [round(x, 4) for x in iats[-10:]]
                            }
                        })
                        
                        if deception:
                            await broadcast({
                                "type": "DECEPTION_DEPLOYED",
                                "session_id": sid,
                                "action": deception["action"],
                                "payload": deception["payload"]
                            })
                            
                    elif eid == "cowrie.session.closed":
                        duration = event.get("duration", 0)
                        s["closed"] = True
                        s["duration_ms"] = round(duration * 1000)
                        await broadcast({"type": "SESSION_CLOSED", "session_id": sid, "duration_ms": s["duration_ms"]})
        except Exception:
            pass
        
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup():
    asyncio.create_task(tail_logs())

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)
    
    for sid, s in sessions.items():
        if s["timestamps"]:
            mean_iat, var_iat, iats = calculate_metrics(s["timestamps"])
            num = len(s["keys"])
        else:
            mean_iat, var_iat, iats = get_json_metrics(s)
            num = len(s["cmds"])
            
        await ws.send_json({
            "type": "SESSION_HISTORY",
            "session_id": sid,
            "src_ip": s["src_ip"],
            "commands": s["cmds"],
            "classification": s["tier"],
            "closed": s.get("closed", False),
            "duration_ms": s.get("duration_ms", 0),
            "connected_at": s.get("connected_at", ""),
            "metrics": {
                "mean_iat": round(mean_iat, 4),
                "variance_iat": round(var_iat, 4),
                "num_commands": num,
                "recent_iats": [round(x, 4) for x in iats[-10:]]
            },
        })
        
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
