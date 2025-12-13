import time
import jwt

JWT_SECRET = "supersecretkey"   # ⚠️ use env var in real apps
JWT_ALGORITHM = "HS256"


def sign_jwt(user_id: str, role: str) -> dict:
    payload = {
        "user_id": user_id,
        "role": role,
        "expires": time.time() + 60 * 60 * 24,  # 24 hours
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token}


def decode_jwt(token: str) -> dict | None:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except Exception:
        return None
