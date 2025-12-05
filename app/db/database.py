from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017/"
DB_NAME = "inventory_reservation_db"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

products_collection = db["products"]
orders_collection = db["orders"]
audit_collection = db["audit_logs"]
reservations_collection = db["reservations"]
stock_history_collection = db["stock_history"]
