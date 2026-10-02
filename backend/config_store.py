import os
import json
import firestore_db

DEFAULT_CONFIG = {
    "tau_bot": 0.25,
    "tau_human": 1.80,
    "delta_var": 0.08,
    "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
    "webhook_url": "",
    "alert_email": "",
    "groq_model": "llama-3.1-8b-instant",
    "offline_fallback_enabled": True
}

def load_settings(user_id: str = "default_user") -> dict:
    user_settings = firestore_db.get_user_settings(user_id)
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_settings)
    return merged

def save_settings(new_settings: dict, user_id: str = "default_user") -> dict:
    saved = firestore_db.save_user_settings(user_id, new_settings)
    merged = DEFAULT_CONFIG.copy()
    merged.update(saved)
    return merged
