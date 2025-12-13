from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from app.db.database import users_collection
from app.auth.auth_handler import sign_jwt

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Using pbkdf2_sha256 to avoid bcrypt length issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # "admin" or "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register_user(user: UserRegister):
    if user.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")

    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = pwd_context.hash(user.password)
    new_user = {
        "email": user.email,
        "password": hashed_pw,
        "full_name": user.full_name,
        "role": user.role,
    }
    await users_collection.insert_one(new_user)
    return {"message": "User registered successfully", "role": user.role}


@router.post("/login")
async def login_user(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = sign_jwt(db_user["email"], db_user["role"])
    return {
        "access_token": token["access_token"],
        "token_type": "bearer",
        "role": db_user["role"],
        "full_name": db_user.get("full_name"),
    }
