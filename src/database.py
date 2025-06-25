from datetime import datetime
from typing import Dict, List, Any

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from src import config

# Initialize MongoDB client and collections
mongodb_client = AsyncIOMotorClient(config.MONGODB_URL)
db = mongodb_client.whatsapp_ai
users_collection = db.get_collection("users")
messages_collection = db.get_collection("messages")

# Ensure index on timestamp for efficient sorting (create once during setup)
# await messages_collection.create_index("timestamp", expireAfterSeconds=60*60*24*30)  # Optional TTL index

class User(BaseModel):
    phone_number: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    user_id: str
    phone_number: str
    content: str
    role: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

async def get_or_create_user(from_number: str, sender_name: str) -> str:
    """Get existing user or create a new one if not exists."""
    user = await users_collection.find_one({"phone_number": from_number})
    if not user:
        new_user = User(phone_number=from_number, name=sender_name)
        result = await users_collection.insert_one(new_user.model_dump())
        return str(result.inserted_id)
    return str(user.get("_id"))

async def save_message(
    user_id: str, phone_number: str, content: str, role: str
) -> None:
    """Save a message to the database."""
    message = Message(
        user_id=user_id,
        phone_number=phone_number,
        content=content,
        role=role,
    )
    await messages_collection.insert_one(message.model_dump())

async def get_recent_messages(
    phone_number: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve and return recent messages for a specific user, sorted oldest first."""
    cursor = (
        messages_collection
        .find({"phone_number": phone_number})
        .sort("timestamp", -1)
        .limit(limit)
    )
    # Fetch and reverse so oldest messages come first
    messages = await cursor.to_list(length=limit)
    messages.reverse()
    return [ {"role": msg.get("role"), "content": msg.get("content")} for msg in messages ]
