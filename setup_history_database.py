from pymongo import MongoClient
from app.core.config_1 import settings

def setup_history_database():
    """Initialize workout history database with collections and indexes."""

    client = MongoClient(settings.WORKOUT_HISTORY_DB_URI)
    db = client[settings.WORKOUT_HISTORY_DB_NAME]

    print("Setting up workout history database...")

    # Collection 1: generated_workouts
    print("Creating 'generated_workouts' collection...")
    workouts_coll = db.generated_workouts

    workouts_coll.create_index([
        ("user_id", 1),
        ("generated_at", -1)
    ], name="user_date_idx")

    workouts_coll.create_index([
        ("workout_hash", 1)
    ], name="hash_idx")

    workouts_coll.create_index([
        ("user_id", 1),
        ("week_start_iso", -1)
    ], name="user_week_idx")

    # Collection 2: exercise_history
    print("Creating 'exercise_history' collection...")
    history_coll = db.exercise_history

    history_coll.create_index([
        ("user_id", 1),
        ("exercise_id", 1),
        ("last_used", -1)
    ], name="user_exercise_idx")

    print("✅ Workout history database setup complete!")
    print(f"   Database: {settings.WORKOUT_HISTORY_DB_NAME}")
    print(f"   Collections: generated_workouts, exercise_history")

if __name__ == "__main__":
    setup_history_database()
