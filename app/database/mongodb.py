"""
MongoDB Connection Management
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.database.schemas import User, Workout, ModelWeight
from config import settings

logger = logging.getLogger(__name__)

mongodb_client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Connect to MongoDB and initialize Beanie ODM"""
    global mongodb_client
    
    try:
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Initialize Beanie with document models
        await init_beanie(
            database=mongodb_client[settings.MONGODB_DB_NAME],
            document_models=[User, Workout, ModelWeight]
        )
        
        logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")
