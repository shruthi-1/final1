#!/usr/bin/env python3
"""
Import Exercise Data into MongoDB
Loads CSV files and creates proper indexes
"""
import pandas as pd
from pymongo import MongoClient, ASCENDING
import os

def import_exercises():
    """Import all exercise data into MongoDB."""

    print("="*60)
    print("  NUTRIX - Exercise Data Import")
    print("="*60)
    print()

    # Connect to MongoDB
    print("📡 Connecting to MongoDB...")
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        db = client['nutrix']
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("Make sure MongoDB is running!")
        return

    # Check if files exist
    csv_files = [
        "C:/Users/Shruthi/Desktop/final1/data/nutrix_exercise_database.csv",
        "C:/Users/Shruthi/Desktop/final1/data/megaGym_enriched_muscles_patterns.csv"
    ]

    for file in csv_files:
        if not os.path.exists(file):
            print(f"❌ File not found: {file}")
            print(f"   Please make sure CSV files are in the same folder!")
            return

    print("📂 Loading CSV files...")

    # Load main exercise database
    try:
        nutrix_db = pd.read_csv('nutrix_exercise_database.csv')
        print(f"✅ Loaded nutrix_exercise_database.csv ({len(nutrix_db)} exercises)")
    except Exception as e:
        print(f"❌ Error loading nutrix_exercise_database.csv: {e}")
        return

    # Load enriched data
    try:
        enriched = pd.read_csv('megaGym_enriched_muscles_patterns.csv')
        print(f"✅ Loaded megaGym_enriched_muscles_patterns.csv ({len(enriched)} records)")
    except Exception as e:
        print(f"❌ Error loading megaGym_enriched_muscles_patterns.csv: {e}")
        return

    print()
    print("🔄 Processing and merging data...")

    # Merge datasets
    merged = pd.merge(
        nutrix_db,
        enriched[['Title', 'primary_muscle', 'secondary_muscles_str', 'movement_pattern']],
        on='Title',
        how='left'
    )

    # Clean and standardize data
    merged['exercise_id_clean'] = merged['Title'].str.lower().str.replace(' ', '-').str.replace('[^a-z0-9-]', '', regex=True)
    merged['is_bodyweight'] = merged['Equipment'] == 'Bodyweight'
    merged['is_active'] = True

    # Map difficulty levels
    difficulty_map = {'Beginner': 1, 'Intermediate': 3, 'Expert': 5}
    merged['difficulty'] = merged['Level'].map(difficulty_map).fillna(3).astype(int)

    # Fill missing values
    merged['Rating'] = merged['Rating'].fillna(0)
    merged['Desc'] = merged['Desc'].fillna('')
    merged['primary_muscle'] = merged['primary_muscle'].fillna('unknown')
    merged['movement_pattern'] = merged['movement_pattern'].fillna('unknown')

    # Convert to list of dictionaries
    exercises = merged.to_dict('records')

    print(f"✅ Processed {len(exercises)} exercises")
    print()

    # Clear existing data (optional - comment out to keep existing)
    print("⚠️  Clearing existing exercises collection...")
    db.exercises.delete_many({})

    # Insert exercises
    print("💾 Inserting exercises into MongoDB...")
    try:
        if exercises:
            result = db.exercises.insert_many(exercises)
            print(f"✅ Inserted {len(result.inserted_ids)} exercises")
    except Exception as e:
        print(f"❌ Error inserting exercises: {e}")
        return

    # Create indexes for fast queries
    print()
    print("🔍 Creating database indexes...")

    try:
        # Equipment + BodyPart + difficulty index
        db.exercises.create_index([
            ("Equipment", ASCENDING),
            ("BodyPart", ASCENDING),
            ("difficulty", ASCENDING)
        ], name="equipment_bodypart_difficulty")

        # Active exercises index
        db.exercises.create_index([("is_active", ASCENDING)], name="is_active")

        # Exercise ID index
        db.exercises.create_index([("exercise_id_clean", ASCENDING)], name="exercise_id")

        # Level index
        db.exercises.create_index([("Level", ASCENDING)], name="level")

        print("✅ Created all indexes")
    except Exception as e:
        print(f"⚠️  Warning: Some indexes may already exist")

    # Print summary statistics
    print()
    print("="*60)
    print("📊 IMPORT SUMMARY")
    print("="*60)
    print(f"Total exercises in database: {db.exercises.count_documents({})}")
    print()

    print("Equipment breakdown:")
    for equipment in db.exercises.distinct('Equipment'):
        count = db.exercises.count_documents({'Equipment': equipment})
        print(f"  {equipment}: {count}")

    print()
    print("Body part breakdown:")
    for body_part in db.exercises.distinct('BodyPart'):
        count = db.exercises.count_documents({'BodyPart': body_part})
        print(f"  {body_part}: {count}")

    print()
    print("Fitness level breakdown:")
    for level in db.exercises.distinct('Level'):
        count = db.exercises.count_documents({'Level': level})
        print(f"  {level}: {count}")

    print()
    print("="*60)
    print("✅ IMPORT COMPLETE!")
    print("="*60)
    print()
    print("You can now run: python cli_menu.py")
    print()

    client.close()


if __name__ == "__main__":
    import_exercises()
