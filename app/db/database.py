from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGO_URL, MONGO_DB_NAME

# Create a single shared MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[MONGO_DB_NAME]

# Collections
products_collection = db["products"]
orders_collection = db["orders"]
audit_collection = db["audit_logs"]
reservations_collection = db["reservations"]
stock_history_collection = db["stock_history"]
users_collection = db["users"]
