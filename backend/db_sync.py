import datetime
from database import SessionLocal, SessionData, CommandData, DeceptionData
import firestore_db

def get_or_create_session(db, session_id, src_ip, connected_at_str, user_id: str = "default_user"):
    session = db.query(SessionData).filter(SessionData.id == session_id).first()
    if not session:
        try:
            connected_at = datetime.datetime.fromisoformat(connected_at_str.replace("Z", "+00:00")) if connected_at_str else datetime.datetime.utcnow()
        except:
            connected_at = datetime.datetime.utcnow()
            
        session = SessionData(
            id=session_id,
            src_ip=src_ip,
            connected_at=connected_at
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Sync to Firestore
    try:
        firestore_db.save_session_event(user_id, session_id, {
            "src_ip": src_ip,
            "connected_at": connected_at_str,
            "classification": session.classification or "UNKNOWN",
            "closed": session.closed_at is not None
        })
    except Exception as fe:
        print(f"[Firestore Sync Error]: {fe}")

    return session

def update_session_metrics(db, session_id, classification, mean_iat, variance_iat, user_id: str = "default_user"):
    session = db.query(SessionData).filter(SessionData.id == session_id).first()
    if session:
        session.classification = classification
        session.mean_iat = mean_iat
        session.variance_iat = variance_iat
        db.commit()

        try:
            firestore_db.save_session_event(user_id, session_id, {
                "classification": classification,
                "mean_iat": mean_iat,
                "variance_iat": variance_iat
            })
        except Exception as fe:
            print(f"[Firestore Metrics Sync Error]: {fe}")

def add_command(db, session_id, text, timestamp_str, intent_tactic, intent_severity, user_id: str = "default_user"):
    try:
        ts = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")) if timestamp_str else datetime.datetime.utcnow()
    except:
        ts = datetime.datetime.utcnow()
        
    # Prevent duplicate commands on restart
    existing = db.query(CommandData).filter(
        CommandData.session_id == session_id,
        CommandData.text == text,
        CommandData.timestamp == ts
    ).first()
    
    if not existing:
        cmd = CommandData(
            session_id=session_id,
            text=text,
            timestamp=ts,
            intent_tactic=intent_tactic,
            intent_severity=intent_severity
        )
        db.add(cmd)
        db.commit()

        try:
            firestore_db.add_command_event(user_id, session_id, {
                "text": text,
                "timestamp": timestamp_str,
                "intent_tactic": intent_tactic,
                "intent_severity": intent_severity
            })
        except Exception as fe:
            print(f"[Firestore Command Sync Error]: {fe}")

def add_deception(db, session_id, action, payload):
    dec = DeceptionData(
        session_id=session_id,
        action=action,
        payload=payload
    )
    db.add(dec)
    db.commit()

def close_session(db, session_id, duration_ms):
    session = db.query(SessionData).filter(SessionData.id == session_id).first()
    if session:
        session.closed_at = datetime.datetime.utcnow()
        session.duration_ms = duration_ms
        db.commit()

        try:
            firestore_db.save_session_event("default_user", session_id, {
                "closed": True,
                "duration_ms": duration_ms
            })
        except Exception as fe:
            print(f"[Firestore Close Sync Error]: {fe}")

def get_all_sessions(db):
    sessions = db.query(SessionData).all()
    result = []
    for s in sessions:
        sorted_cmds = sorted(s.commands, key=lambda c: c.timestamp or datetime.datetime.min)
        cmds = [{"text": c.text, "intent": {"tactic": c.intent_tactic, "severity": c.intent_severity} if c.intent_tactic else None} for c in sorted_cmds]
        
        recent_iats = []
        for i in range(1, len(sorted_cmds)):
            if sorted_cmds[i].timestamp and sorted_cmds[i-1].timestamp:
                delta = (sorted_cmds[i].timestamp - sorted_cmds[i-1].timestamp).total_seconds()
                recent_iats.append(round(max(0.001, delta), 3))
            else:
                recent_iats.append(round(s.mean_iat or 0.1, 3))
                
        result.append({
            "session_id": s.id,
            "src_ip": s.src_ip,
            "connected_at": s.connected_at.isoformat() + "Z" if s.connected_at else "",
            "closed": s.closed_at is not None,
            "classification": s.classification,
            "commands": cmds,
            "duration_ms": s.duration_ms or 0,
            "metrics": {
                "mean_iat": s.mean_iat or 0,
                "variance_iat": s.variance_iat or 0,
                "num_commands": len(cmds),
                "recent_iats": recent_iats
            }
        })
    return result
