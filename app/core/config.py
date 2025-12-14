# app/core/config.py
import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

# === MongoDB ===
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "inventory_reservation_db")

# === JWT / Auth ===
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# === Reservation config ===
RESERVATION_DEFAULT_TTL_MINUTES = int(os.getenv("RESERVATION_DEFAULT_TTL_MINUTES", "15"))
RESERVATION_CLEANUP_INTERVAL_SECONDS = int(os.getenv("RESERVATION_CLEANUP_INTERVAL_SECONDS", "30"))
