from fastapi import Depends, HTTPException
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_jwt
from app.db.database import users_collection


async def get_current_user(token: str = Depends(JWTBearer())):
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    user = await users_collection.find_one({"email": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user  # this is a MongoDB document dict


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "user":
        raise HTTPException(status_code=403, detail="User access required")
    return current_user
