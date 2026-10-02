import os
import json
import datetime

db_client = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db_client = firestore.client()
        print("[Firestore] Firebase Admin SDK initialized successfully with serviceAccountKey.json")
    else:
        print("[Firestore] No serviceAccountKey.json found. Firestore operating in simulated multi-tenant mode.")
except Exception as e:
    print(f"[Firestore] Initialization notice: {e}")

# In-memory per-user storage fallback when serviceAccountKey is pending
_IN_MEMORY_TENANT_DB = {}

def _get_tenant_store(user_id: str):
    if user_id not in _IN_MEMORY_TENANT_DB:
        _IN_MEMORY_TENANT_DB[user_id] = {
            "settings": {
                "tau_bot": 0.25,
                "tau_human": 1.80,
                "delta_var": 0.08,
                "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
                "webhook_url": "",
                "alert_email": "",
                "groq_model": "llama-3.1-8b-instant"
            },
            "sessions": {}
        }
    return _IN_MEMORY_TENANT_DB[user_id]

def get_user_settings(user_id: str = "default_user") -> dict:
    if db_client:
        try:
            doc_ref = db_client.collection("users").document(user_id).collection("settings").document("config")
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"[Firestore] Error reading user settings: {e}")
            
    return _get_tenant_store(user_id)["settings"]

def save_user_settings(user_id: str, new_settings: dict) -> dict:
    current = get_user_settings(user_id)
    current.update(new_settings)
    
    if db_client:
        try:
            doc_ref = db_client.collection("users").document(user_id).collection("settings").document("config")
            doc_ref.set(current, merge=True)
            print(f"[Firestore] Saved settings for user: {user_id}")
        except Exception as e:
            print(f"[Firestore] Error saving user settings: {e}")
            
    _get_tenant_store(user_id)["settings"] = current
    return current

def save_session_event(user_id: str, session_id: str, session_data: dict):
    if db_client:
        try:
            doc_ref = db_client.collection("users").document(user_id).collection("sessions").document(session_id)
            doc_ref.set(session_data, merge=True)
        except Exception as e:
            print(f"[Firestore] Error saving session event: {e}")
            
    tenant = _get_tenant_store(user_id)
    if session_id not in tenant["sessions"]:
        tenant["sessions"][session_id] = session_data
    else:
        tenant["sessions"][session_id].update(session_data)

def add_command_event(user_id: str, session_id: str, command_data: dict):
    if db_client:
        try:
            doc_ref = db_client.collection("users").document(user_id).collection("sessions").document(session_id).collection("commands").document()
            doc_ref.set(command_data)
        except Exception as e:
            print(f"[Firestore] Error adding command event: {e}")
            
    tenant = _get_tenant_store(user_id)
    if session_id in tenant["sessions"]:
        cmds = tenant["sessions"][session_id].setdefault("commands", [])
        cmds.append(command_data)

def get_all_user_sessions(user_id: str = "default_user") -> list:
    if db_client:
        try:
            sessions_ref = db_client.collection("users").document(user_id).collection("sessions")
            docs = sessions_ref.stream()
            result = []
            for doc in docs:
                data = doc.to_dict()
                data["session_id"] = doc.id
                result.append(data)
            if result:
                return result
        except Exception as e:
            print(f"[Firestore] Error reading user sessions: {e}")
            
    tenant = _get_tenant_store(user_id)
    res = []
    for sid, sdata in tenant["sessions"].items():
        item = sdata.copy()
        item["session_id"] = sid
        res.append(item)
    return res
