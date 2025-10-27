"""
MongoDB connection and database management.
bassed on id create new workout??
have user table and serive?
app:sign up 
mongodb cloud - organisational lvl 
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from app.core.config_1 import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB database manager."""

    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(settings.MONGO_URI)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
            self._create_indexes()
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def _create_indexes(self):
        """Create necessary indexes for optimal query performance."""
        try:
            # User weekly plans indexes
            self.db.user_weekly_plans.create_index(
                [("user_id", ASCENDING), ("week_start_iso", DESCENDING)],
                unique=True
            )

            # Exercises indexes
            self.db.exercises.create_index([
                ("Equipment", ASCENDING),
                ("BodyPart", ASCENDING),
                ("difficulty", ASCENDING)
            ])

            self.db.exercises.create_index([("is_active", ASCENDING)])

            # Users index
            self.db.users.create_index([("user_id", ASCENDING)], unique=True)

            # Learning vectors index
            self.db.user_learning_vectors.create_index([("user_id", ASCENDING)], unique=True)

            # Session logs index
            self.db.session_logs.create_index([
                ("user_id", ASCENDING),
                ("logged_at", DESCENDING)
            ])

            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def get_collection(self, name: str):
        """Get a collection by name."""
        return self.db[name]


# Global database instance
db_manager = MongoDB()


def get_database():
    """Dependency for getting database instance."""
    return db_manager.db
