import os
import json
import random
import config_store

SYNTHETIC_HONEYTOKENS = {
    "Credential Access": [
        "# Production Environment Config\n[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE\naws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\nregion = us-east-1\noutput = json",
        "DATABASE_URL=postgres://admin:P%40ssw0rd2026!@10.0.12.44:5432/prod_db\nREDIS_AUTH=eYJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\nJWT_SECRET=super_secret_chameleon_key_99",
        "root:$6$v7kXm9$Q4T8Z3xL0e1W2y3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0:19823:0:99999:7:::"
    ],
    "Discovery": [
        "{\n  \"internal_subnets\": [\"10.0.1.0/24\", \"10.0.2.0/24\", \"10.0.100.0/20\"],\n  \"gateway\": \"10.0.1.1\",\n  \"domain_controller\": \"10.0.1.10 (dc01.corp.internal)\",\n  \"backup_server\": \"10.0.2.55 (s3-vault.corp.internal)\"\n}",
        "127.0.0.1       localhost\n10.0.1.10       dc01.corp.internal\n10.0.2.55       backup-node.internal\n10.0.12.44      db-primary.corp.internal"
    ],
    "Command and Control": [
        "#!/bin/bash\n# Scheduled Heartbeat Script\ncurl -X POST https://telemetry.corp-monitoring.net/api/v1/ping -d '{\"node_id\": \"srv-prod-ssh-01\", \"status\": \"active\"}'"
    ]
}

def generate_honeytoken(intent_tactic, command=""):
    """
    Generates a honeytoken payload. Uses Groq LLM if API key is provided;
    otherwise seamlessly uses high-fidelity synthetic generative engine.
    """
    settings = config_store.load_settings()
    groq_key = settings.get("groq_api_key") or os.environ.get("GROQ_API_KEY", "")
    groq_model = settings.get("groq_model", "llama-3.1-8b-instant")

    if groq_key and not groq_key.startswith("gsk_placeholder"):
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            prompt = f"Attacker command: '{command}'. Tactic: '{intent_tactic}'. Generate raw enticing file payload."
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a cyber deception engine. Output only raw file payload."},
                    {"role": "user", "content": prompt}
                ],
                model=groq_model,
                temperature=0.7,
                max_tokens=256
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LLM Engine] Groq API call failed: {e}")

    # High-Fidelity Synthetic Engine Fallback
    templates = SYNTHETIC_HONEYTOKENS.get(intent_tactic, SYNTHETIC_HONEYTOKENS["Credential Access"])
    return random.choice(templates)

def test_groq_connection(api_key: str = None, model: str = None):
    settings = config_store.load_settings()
    key = api_key or settings.get("groq_api_key") or os.environ.get("GROQ_API_KEY", "")
    mdl = model or settings.get("groq_model", "llama-3.1-8b-instant")
    
    if not key or key.startswith("gsk_placeholder"):
        return {"success": False, "error": "No valid Groq API key configured"}
    try:
        from groq import Groq
        client = Groq(api_key=key)
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello! Reply with 'OK' if working."}],
            model=mdl,
            max_tokens=10
        )
        msg = res.choices[0].message.content.strip()
        return {"success": True, "message": f"Connected successfully! Model response: '{msg}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def inject_to_honeyfs(filename, content):
    """
    Writes the generated deception content into the shared honeyfs volume.
    """
    honeyfs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'honeypot', 'honeyfs')
    os.makedirs(honeyfs_dir, exist_ok=True)
    
    filepath = os.path.join(honeyfs_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return filepath

