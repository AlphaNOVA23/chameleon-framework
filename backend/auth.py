import os
import time
import hashlib
import hmac
import json
import base64
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "chameleon_commercial_secret_key_2026_fypproject")
security = HTTPBearer()

def hash_password(password: str) -> str:
    salt = "chameleon_salt_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

def create_jwt_token(payload: dict, expires_in_seconds: int = 86400) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expires_in_seconds
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input.encode('utf-8'), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_jwt_token(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
            
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        signature_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input.encode('utf-8'), hashlib.sha256).digest()
        
        # Add padding back if necessary
        rem = len(signature_b64) % 4
        if rem > 0:
            signature_b64 += '=' * (4 - rem)
        actual_sig = base64.urlsafe_b64decode(signature_b64.encode('utf-8'))
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")
            
        # Decode payload
        rem_payload = len(payload_b64) % 4
        if rem_payload > 0:
            payload_b64 += '=' * (4 - rem_payload)
        payload_data = json.loads(base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8'))
        
        if payload_data.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token has expired")
            
        return payload_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    return decode_jwt_token(token)
