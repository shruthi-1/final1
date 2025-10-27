#!/usr/bin/env python3
"""
Generate ML Insights Script
Generate and save insights for all users
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
    from datetime import datetime
    import json
    import logging
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nMake sure you:")
    print("  1. Are running from project root")
    print("  2. Have installed all requirements: pip install -r requirements.txt")
    print("  3. Have activated your virtual environment")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_insights_for_all_users():
    """Generate ML insights for all users."""
    
    print("="*60)
    print("  GENERATING ML INSIGHTS")
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
        print("\nMake sure MongoDB is running:")
        print("  - Check if MongoDB service is started")
        print("  - Verify MONGO_URI in your config")
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
        print("\nCreate users first using the CLI menu:")
        print("  python fitgen_cli_ml.py")
        return
    
    print(f"📊 Found {len(users)} users\n")
    
    # Create insights directory
    os.makedirs('insights', exist_ok=True)
    
    # Generate insights for each user
    for user in users:
        user_id = user['user_id']
        
        print(f"Generating insights for: {user_id}")
        print("-" * 40)
        
        # Check if user has enough data
        sessions = list(db.session_logs.find({"user_id": user_id}))
        
        if len(sessions) < 3:
            print(f"⚠️  User has only {len(sessions)} sessions - need at least 3")
            print(f"✅ Skipping {user_id}\n")
            continue
        
        # Generate comprehensive dashboard
        try:
            dashboard = model_manager.generate_ml_dashboard(user_id)
            
            if dashboard:
                # Save to file
                filename = f"insights/{user_id}_insights_{datetime.now().strftime('%Y%m%d')}.json"
                with open(filename, 'w') as f:
                    json.dump(dashboard, f, indent=2, default=str)
                
                print(f"  ✅ Insights saved to: {filename}")
                
                # Print summary
                if dashboard.get('exercise_recommendations'):
                    print(f"  📋 {len(dashboard['exercise_recommendations'])} exercise recommendations")
                
                if dashboard.get('injury_risk'):
                    risk = dashboard['injury_risk']['overall_risk']
                    print(f"  ⚠️  Injury risk: {risk}")
                
                if dashboard.get('plateau_detection'):
                    plateau = dashboard['plateau_detection']['has_plateau']
                    print(f"  📊 Plateau detected: {plateau}")
            else:
                print("  ⚠️  Could not generate insights")
        
        except Exception as e:
            print(f"  ❌ Error generating insights: {e}")
            logger.error(f"Error generating insights for {user_id}: {e}")
        
        # Generate visualizations
        print("  📊 Generating visualizations...")
        
        # Progression chart
        try:
            prog_chart = model_manager.create_progression_chart(
                user_id, 
                f"insights/{user_id}_progression.png"
            )
            if prog_chart:
                print(f"  ✅ Progression chart saved")
        except Exception as e:
            print(f"  ⚠️  Could not create progression chart: {str(e)[:50]}")
        
        # Heatmap
        try:
            heatmap = model_manager.create_body_part_heatmap(
                user_id, 
                f"insights/{user_id}_heatmap.png"
            )
            if heatmap:
                print(f"  ✅ Body part heatmap saved")
        except Exception as e:
            print(f"  ⚠️  Could not create heatmap: {str(e)[:50]}")
        
        # Weekly summary
        try:
            summary = model_manager.create_weekly_summary_chart(
                user_id, 
                f"insights/{user_id}_weekly.png"
            )
            if summary:
                print(f"  ✅ Weekly summary chart saved")
        except Exception as e:
            print(f"  ⚠️  Could not create weekly summary: {str(e)[:50]}")
        
        print()
    
    print("="*60)
    print("✅ INSIGHTS GENERATION COMPLETE!")
    print("="*60)
    print()
    print(f"Check the 'insights/' directory for all generated files.")
    print()


def main():
    """Main entry point."""
    try:
        generate_insights_for_all_users()
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
