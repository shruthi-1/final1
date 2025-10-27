#!/usr/bin/env python3
"""
Train ML Models Script
Initial training on synthetic or real data
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from pymongo import MongoClient
    from app.core.config_1 import settings
    from app.ml.model_manager import ModelManager
    import logging
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nMake sure you:")
    print("  1. Are running from project root: cd C:\\Users\\Shruthi\\Desktop\\final1")
    print("  2. Have installed requirements: pip install -r requirements.txt")
    print("  3. Have activated virtual environment: venv\\Scripts\\activate")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_all_models():
    """Train all ML models on available data."""
    
    print("="*60)
    print("  TRAINING ML MODELS")
    print("="*60)
    print()
    
    # Connect to database
    print("📡 Connecting to MongoDB...")
    try:
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[settings.DATABASE_NAME]
        client.server_info()
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\nMake sure MongoDB is running and config is correct.")
        return
    
    # Initialize model manager
    try:
        model_manager = ModelManager(db)
    except Exception as e:
        print(f"❌ Failed to initialize ModelManager: {e}")
        return
    
    # Get all users
    users = list(db.users.find({}))
    
    if not users:
        print("❌ No users found in database")
        print("\nCreate users and log workouts before training models.")
        return
    
    print(f"📊 Found {len(users)} users\n")
    
    # Train models for each user
    for user in users:
        user_id = user['user_id']
        
        print(f"Training models for user: {user_id}")
        print("-" * 40)
        
        # Check if user has enough data
        sessions = list(db.session_logs.find({"user_id": user_id}))
        
        if len(sessions) < 5:
            print(f"⚠️  User has only {len(sessions)} sessions - need at least 5")
            print(f"✅ Skipping {user_id}\n")
            continue
        
        # Build and train exercise recommender
        print("  🔨 Building exercise recommender...")
        try:
            if model_manager.exercise_recommender.build_interaction_matrix():
                print("  ✅ Exercise recommender built")
            else:
                print("  ⚠️  Not enough data for recommender")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Test other components
        print("  🔨 Testing injury predictor...")
        try:
            risk = model_manager.get_injury_risk_analysis(user_id)
            print(f"  ✅ Injury risk: {risk['overall_risk']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print("  🔨 Testing plateau detector...")
        try:
            plateau = model_manager.detect_plateau(user_id)
            print(f"  ✅ Plateau: {plateau['has_plateau']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Save models
        print("  💾 Saving models...")
        try:
            if model_manager.save_all_models(user_id):
                print("  ✅ Models saved")
            else:
                print("  ⚠️  Some models could not be saved")
        except Exception as e:
            print(f"  ❌ Error saving: {e}")
        
        print()
    
    print("="*60)
    print("✅ MODEL TRAINING COMPLETE!")
    print("="*60)
    print()
    print("Models are now ready for use in the CLI.")
    print("Run: python fitgen_cli_ml.py")
    print()


def main():
    """Main entry point."""
    try:
        train_all_models()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
