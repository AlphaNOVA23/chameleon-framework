import asyncio
import json
import os
import io
import csv
from datetime import datetime
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, Response, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from orchestrator.log_tailer import parse_tty_chunk, read_new_bytes
from orchestrator.biometric import calculate_metrics, classify
from orchestrator.semantic_engine import analyze_command
from orchestrator.deception_engine import generate_deception_action
from orchestrator.llm_engine import test_groq_connection
from orchestrator.ip_intel import enrich_ip
from email_alerts import send_threat_email_alert
from database import SessionLocal
import db_sync
import auth
import config_store

app = FastAPI(title="Chameleon Enterprise Deception API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_LOG = os.path.join(BASE_DIR, "honeypot", "logs2", "cowrie.json")
TTY_DIR = os.path.join(BASE_DIR, "honeypot", "tty")

active_connections = []
sessions = {}

# In-Memory Users for Demo Commercial Auth
USERS_DB = {
    "admin": auth.hash_password("admin123")
}

# Registered Sensor Nodes
SENSOR_NODES = [
    {"id": "sensor-01", "name": "AWS-US-East-Sensor", "ip": "54.210.12.99", "status": "ACTIVE", "region": "us-east-1", "token": "CHAM_SENS_01_KEY"},
    {"id": "sensor-02", "name": "Azure-EU-West-Canary", "ip": "52.174.90.14", "status": "ACTIVE", "region": "eu-west-1", "token": "CHAM_SENS_02_KEY"},
    {"id": "sensor-03", "name": "Internal-DMZ-Trap", "ip": "10.0.1.55", "status": "ACTIVE", "region": "on-premise", "token": "CHAM_SENS_03_KEY"}
]

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
        except Exception:
            pass

# ============================================================
# REST API ENDPOINTS FOR COMMERCIAL DASHBOARD
# ============================================================

@app.post("/api/auth/register")
def register(user_data: dict = Body(...)):
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    if username in USERS_DB:
        raise HTTPException(status_code=400, detail="User already exists")
    USERS_DB[username] = auth.hash_password(password)
    token = auth.create_jwt_token({"sub": username, "role": "analyst"})
    return {"token": token, "username": username, "role": "analyst"}

@app.post("/api/auth/login")
def login(credentials: dict = Body(...)):
    username = credentials.get("username", "").strip()
    password = credentials.get("password", "").strip()
    hashed = USERS_DB.get(username)
    if not hashed or not auth.verify_password(password, hashed):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_jwt_token({"sub": username, "role": "admin"})
    return {"token": token, "username": username, "role": "admin"}

@app.get("/api/auth/me")
def get_me(user: dict = Depends(auth.get_current_user)):
    return {"username": user.get("sub"), "role": user.get("role", "analyst")}

@app.get("/api/settings")
def get_settings(user_id: str = "default_user"):
    return config_store.load_settings(user_id=user_id)

@app.post("/api/settings")
def update_settings(new_settings: dict = Body(...), user_id: str = "default_user"):
    saved = config_store.save_settings(new_settings, user_id=user_id)
    # If Groq API key is updated, set in env
    if "groq_api_key" in new_settings:
        os.environ["GROQ_API_KEY"] = new_settings["groq_api_key"]
    return {"status": "success", "settings": saved}

@app.post("/api/groq/test")
def test_groq_endpoint(data: dict = Body(default={})):
    api_key = data.get("groq_api_key")
    model = data.get("groq_model")
    return test_groq_connection(api_key, model)

@app.get("/api/sensors")
def get_sensors():
    return {"sensors": SENSOR_NODES}

@app.post("/api/sensors/register")
def register_sensor(sensor_data: dict = Body(...)):
    user_id = sensor_data.get("user_id") or sensor_data.get("user") or "admin"
    name = sensor_data.get("name", "New-Sensor-Node")
    ip = sensor_data.get("ip", "127.0.0.1")
    region = sensor_data.get("region", "custom-vpc")
    new_id = f"sensor-0{len(SENSOR_NODES) + 1}"
    token = f"CHAM_SENS_{len(SENSOR_NODES) + 1:02d}_KEY"
    TOKEN_USER_MAP[token] = user_id
    install_cmd = f"curl -sSL https://chameleon-backend-fm38.onrender.com/sensor/install.sh | sudo bash -s -- --token {token} --server https://chameleon-backend-fm38.onrender.com"
    new_sensor = {"id": new_id, "name": name, "ip": ip, "status": "ACTIVE", "region": region, "token": token, "user_id": user_id, "install_command": install_cmd}
    SENSOR_NODES.append(new_sensor)
    return {"status": "registered", "sensor": new_sensor}

@app.delete("/api/sessions/{session_id}")
def delete_single_session(session_id: str):
    db = SessionLocal()
    try:
        if session_id in sessions:
            del sessions[session_id]
        db_sync.delete_session(db, session_id)
        return {"status": "deleted", "session_id": session_id}
    finally:
        db.close()

@app.post("/api/sessions/clear")
def clear_sessions_history():
    db = SessionLocal()
    try:
        sessions.clear()
        db_sync.clear_all_sessions(db)
        return {"status": "cleared"}
    finally:
        db.close()

from report_generator import generate_pdf_report

@app.get("/api/reports/pdf")
def export_pdf_report():
    db = SessionLocal()
    try:
        all_sessions = db_sync.get_all_sessions(db)
        settings = config_store.load_settings()
        pdf_bytes = generate_pdf_report(all_sessions, settings)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=chameleon_security_report.pdf"}
        )
    finally:
        db.close()

@app.get("/api/reports/export")
def export_reports(format: str = "json"):
    db = SessionLocal()
    try:
        all_sessions = db_sync.get_all_sessions(db)
        enriched_data = []
        for s in all_sessions:
            ip_meta = enrich_ip(s["src_ip"])
            enriched_data.append({
                "session_id": s["session_id"],
                "src_ip": s["src_ip"],
                "country": ip_meta["country"],
                "isp": ip_meta["isp"],
                "threat_score": ip_meta["threat_score"],
                "risk": ip_meta["risk"],
                "connected_at": s["connected_at"],
                "closed": s["closed"],
                "classification": s["classification"],
                "mean_iat_sec": round(s["metrics"].get("mean_iat", 0), 4),
                "variance_iat": round(s["metrics"].get("variance_iat", 0), 5),
                "command_count": len(s["commands"]),
                "commands": [c.get("text", "") for c in s["commands"]]
            })
            
        if format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Session ID", "Source IP", "Country", "ISP", "Risk Level", "Threat Score", "Classification", "Mean IAT (s)", "Variance", "Command Count", "Commands"])
            for row in enriched_data:
                writer.writerow([
                    row["session_id"], row["src_ip"], row["country"], row["isp"], row["risk"], row["threat_score"],
                    row["classification"], row["mean_iat_sec"], row["variance_iat"], row["command_count"],
                    " | ".join(row["commands"])
                ])
            return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=chameleon_forensics_report.csv"})
        
        return {"total_sessions": len(enriched_data), "report": enriched_data}
    finally:
        db.close()


# ============================================================
# LOG TAILING & INGESTION LOOP
# ============================================================

async def process_log_event(event: dict, db, user_id: str = "admin"):
    sid = event.get("session", "")
    eid = event.get("eventid", "")
    if not sid or not eid:
        return

    if sid not in sessions:
        src_ip = event.get("src_ip", "?")
        ip_intel = enrich_ip(src_ip)
        conn_ts = event.get("timestamp", "")
        sessions[sid] = {
            "src_ip": src_ip,
            "ip_intel": ip_intel,
            "tty_log": None,
            "tty_pos": 0, 
            "timestamps": [],
            "keys": [],
            "cmds": [],
            "tier": "UNKNOWN",
            "cmd_timestamps": [],
            "connected_at": conn_ts,
            "closed": False,
            "duration_ms": 0
        }
        try:
            db_sync.get_or_create_session(db, sid, src_ip, conn_ts, user_id=user_id)
        except Exception as dbe:
            print(f"DB error (session auto-create): {dbe}")
        
    s = sessions[sid]
    
    if eid == "cowrie.session.connect":
        s["src_ip"] = event.get("src_ip", "?")
        s["ip_intel"] = enrich_ip(s["src_ip"])
        s["connected_at"] = event.get("timestamp", "")
        try:
            db_sync.get_or_create_session(db, sid, s["src_ip"], s["connected_at"], user_id=user_id)
        except Exception as dbe:
            print(f"DB error (session create): {dbe}")
        await broadcast({
            "type": "SESSION_NEW",
            "session_id": sid,
            "src_ip": s["src_ip"],
            "ip_intel": s["ip_intel"],
            "timestamp": s["connected_at"]
        })
        
    elif eid in ("cowrie.login.success", "cowrie.login.failed"):
        await broadcast({
            "type": "LOGIN_ATTEMPT",
            "session_id": sid,
            "username": event.get("username", ""),
            "password": event.get("password", ""),
            "success": eid == "cowrie.login.success"
        })
        
    elif eid == "cowrie.command.input":
        cmd = event.get("input", "")
        ts_str = event.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            s["cmd_timestamps"].append(ts)
        except Exception:
            pass
            
        s["cmds"].append(cmd)
        mean_iat, var_iat, iats = get_json_metrics(s)
        if len(s["cmd_timestamps"]) >= 2:
            s["tier"] = classify(mean_iat, var_iat, len(s["cmd_timestamps"]))
        
        try:
            db_sync.update_session_metrics(db, sid, s["tier"], mean_iat, var_iat, user_id=user_id)
        except Exception as dbe:
            print(f"DB error (metrics): {dbe}")
        
        intent = analyze_command(cmd)
        try:
            db_sync.add_command(db, sid, cmd, ts_str, intent["tactic"] if intent else None, intent["severity"] if intent else 0, user_id=user_id)
        except Exception as dbe:
            print(f"DB error (command): {dbe}")
        deception = generate_deception_action(s["tier"], intent, cmd)
        
        await broadcast({
            "type": "COMMAND",
            "session_id": sid,
            "command": cmd,
            "classification": s["tier"],
            "intent": intent,
            "deception": deception,
            "ip_intel": s["ip_intel"],
            "metrics": {
                "mean_iat": round(mean_iat, 4),
                "variance_iat": round(var_iat, 4),
                "num_commands": len(s["cmds"]),
                "recent_iats": [round(x, 4) for x in iats[-10:]]
            }
        })
        
        if deception:
            try:
                db_sync.add_deception(db, sid, deception["action"], deception["payload"])
                send_threat_email_alert(sid, s["tier"], s["src_ip"], cmd)
            except Exception as dbe:
                print(f"DB error (deception): {dbe}")
            await broadcast({
                "type": "DECEPTION_DEPLOYED",
                "session_id": sid,
                "action": deception["action"],
                "payload": deception["payload"]
            })
            
    elif eid == "cowrie.session.closed":
        dur_ms = int(event["duration_ms"]) if "duration_ms" in event else int(event.get("duration", 0) * 1000)
        s["closed"] = True
        s["duration_ms"] = dur_ms
        try:
            db_sync.close_session(db, sid, dur_ms, user_id=user_id)
        except Exception as dbe:
            print(f"DB error (close): {dbe}")
        await broadcast({"type": "SESSION_CLOSED", "session_id": sid, "duration_ms": dur_ms})

async def tail_logs():
    json_pos = 0
    while True:
        try:
            db = SessionLocal()
            if os.path.exists(JSON_LOG):
                with open(JSON_LOG, 'r') as f:
                    f.seek(json_pos)
                    lines = f.readlines()
                    json_pos = f.tell()
                    
                for line in lines:
                    try:
                        event = json.loads(line.strip())
                        await process_log_event(event, db)
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error in tail_logs: {e}")
        finally:
            if 'db' in locals():
                db.close()
        
        await asyncio.sleep(0.1)

TOKEN_USER_MAP = {
    "CHAM_SENS_01_KEY": "admin",
    "CHAM_SENS_02_KEY": "admin",
    "CHAM_SENS_03_KEY": "admin",
    "CHAM_SENS_04_KEY": "admin"
}

@app.post("/api/ingest")
async def ingest_event(payload: dict = Body(...)):
    token = payload.get("token")
    user_id = payload.get("user_id") or payload.get("user")
    if not user_id or user_id in ("admin", "default_user"):
        user_id = TOKEN_USER_MAP.get(token, "admin")
        
    event = payload.get("event")
    if not event or not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid event payload")
        
    db = SessionLocal()
    try:
        await process_log_event(event, db, user_id=user_id)
    finally:
        db.close()
        
    return {"status": "ingested", "event_id": event.get("eventid")}

@app.get("/sensor/install.sh")
def get_installer():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensor", "install.sh")
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript")
    raise HTTPException(status_code=440, detail="Installer script not found")

@app.get("/sensor/chameleon-agent.py")
def get_agent_script():
    agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensor", "chameleon-agent.py")
    if os.path.exists(agent_path):
        return FileResponse(agent_path, media_type="text/x-python")
    raise HTTPException(status_code=404, detail="Agent script not found")

@app.on_event("startup")
async def startup():
    asyncio.create_task(tail_logs())

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    db = SessionLocal()
    try:
        history = db_sync.get_all_sessions(db)
        for h in history:
            ip_intel = enrich_ip(h["src_ip"])
            await websocket.send_json({
                "type": "SESSION_HISTORY",
                "session_id": h["session_id"],
                "src_ip": h["src_ip"],
                "ip_intel": ip_intel,
                "connected_at": h["connected_at"],
                "closed": h["closed"],
                "classification": h["classification"],
                "commands": h["commands"],
                "metrics": h["metrics"],
                "duration_ms": h.get("duration_ms", 0)
            })
    except Exception as e:
        print(f"WS History Error: {e}")
    finally:
        db.close()
        
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
