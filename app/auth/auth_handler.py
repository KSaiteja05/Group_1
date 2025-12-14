import time
import jwt
from typing import Optional

# Load configuration values from .env
from app.core.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def sign_jwt(user_id: str, role: str) -> dict:
    """
    Create a signed JWT token for the given user.
    The expiration time is controlled by ACCESS_TOKEN_EXPIRE_MINUTES in .env.
    """
    expires_at = time.time() + 60 * ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expires_at,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token}


def decode_jwt(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    Returns the decoded payload if valid, otherwise None.
    """
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Invalid signature or malformed token
        return None
