from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("❌ MongoDB connection closed")
    
    @classmethod
    def get_database(cls):
        """Get database instance"""
        return cls.client[settings.MONGODB_DB_NAME]
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get collection instance"""
        db = cls.get_database()
        return db[collection_name]


# Database instance
mongodb = MongoDB()

# Collections
def get_salesperson_collection():
    return mongodb.get_collection("salespeople")

def get_company_collection():
    return mongodb.get_collection("companies")

def get_meeting_collection():
    return mongodb.get_collection("meetings")

def get_conversation_collection():
    return mongodb.get_collection("conversations")

def get_representative_collection():
    return mongodb.get_collection("representatives")