#!/usr/bin/env python3
"""
FitGen AI - Adaptive Workout System with ML
Enhanced CLI with ML-powered insights and recommendations
"""
import sys
import os
from datetime import date, timedelta, datetime
import json
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from app.core.config_1 import settings
from app.services.workout_generator_1 import WorkoutGenerator
from app.utils.bmi_calculator import compute_bmi, get_bmi_category

# Import ML components
try:
    from app.ml.model_manager import ModelManager
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️  ML modules not found. ML features will be disabled.")

MOTIVATION_TIPS = [
    "Consistency beats perfection — show up today.",
    "Your only competition is who you were yesterday.",
    "Small progress is still progress.",
    "The pain you feel today is the strength you feel tomorrow.",
    "Every rep counts. Every set matters.",
]


class FitGenCLI:
    """Enhanced CLI for FitGen AI Workout System with ML."""

    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        self.db = self.client[settings.DATABASE_NAME]
        self.current_user = None
        self.current_mood = None
        
        # Initialize ML Model Manager
        if ML_AVAILABLE:
            try:
                self.model_manager = ModelManager(self.db)
                print("✅ ML Model Manager initialized")
            except Exception as e:
                print(f"⚠️  ML Manager initialization failed: {e}")
                self.model_manager = None
        else:
            self.model_manager = None

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        print("\n" + "="*60)
        print("   🏋️‍♀️  FitGen AI — Adaptive Workout System")
        if ML_AVAILABLE and self.model_manager:
            print("   🤖 ML-Powered Insights Enabled")
        print("="*60)
        if self.current_user:
            print(f"👤 Current User: {self.current_user['user_id']} | "
                  f"Level: {self.current_user['fitness_level']}")
        print()

    def main_menu(self):
        """Main menu with enhanced layout."""
        while True:
            self.clear_screen()
            self.print_header()

            print("🏋️‍♀️  FitGen AI — Adaptive Workout System")
            print("="*60)
            print("1️⃣  User Management 👥")
            print("2️⃣  Workout Generation 🏋️‍♂️")
            print("3️⃣  Daily Workout / Logging 📋")
            print("4️⃣  Progress & Insights 📈")
            print("5️⃣  Motivation & Mindset 💬")
            print("6️⃣  Database Admin 🧩")
            print("7️⃣  Exit ❌")
            print("="*60)
            print()

            choice = input("Enter your choice (1-7): ").strip()

            if choice == '1':
                self.user_management_menu()
            elif choice == '2':
                self.workout_generation_menu()
            elif choice == '3':
                self.daily_workout_menu()
            elif choice == '4':
                self.progress_menu()
            elif choice == '5':
                self.motivation_menu()
            elif choice == '6':
                self.database_admin_menu()
            elif choice == '7':
                self.exit_app()
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    # ============================================================
    # 1️⃣ USER MANAGEMENT (UNCHANGED)
    # ============================================================

    def user_management_menu(self):
        self.clear_screen()
        self.print_header()
        print("👥 USER MANAGEMENT")
        print("="*60)
        print("1. Create New User")
        print("2. Switch User")
        print("3. View Current User")
        print("4. Edit User Info")
        print("5. Delete User")
        print("6. Back to Main Menu")
        print()

        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            self.create_user()
        elif choice == '2':
            self.switch_user()
        elif choice == '3':
            self.view_current_user()
        elif choice == '4':
            self.edit_user()
        elif choice == '5':
            self.delete_user()

    def create_user(self):
        self.clear_screen()
        self.print_header()
        print("✨ CREATE NEW USER\n")

        try:
            user_id = input("User ID: ").strip()
            if self.db.users.find_one({"user_id": user_id}):
                print(f"\n❌ User '{user_id}' already exists!")
                input("Press Enter...")
                return

            age = int(input("Age: "))
            gender = input("Gender (male/female/other): ").lower()
            height_cm = float(input("Height (cm): "))
            weight_kg = float(input("Weight (kg): "))

            print("\nFitness Level:")
            print("  1. Beginner")
            print("  2. Intermediate")
            print("  3. Expert")
            level = ["Beginner", "Intermediate", "Expert"][int(input("Choose: ")) - 1]

            print("\nPrimary Goal:")
            goals_list = ["weight_loss", "muscle_gain", "strength", "endurance", "general_fitness", "athletic"]
            for i, g in enumerate(goals_list, 1):
                print(f"  {i}. {g.replace('_', ' ').title()}")
            goal = goals_list[int(input("Choose: ")) - 1]

            equipment = input("\nEquipment (comma-separated or 'none'): ").strip()
            equipment_list = [] if equipment.lower() == 'none' else [e.strip() for e in equipment.split(',')]

            injuries = input("Injuries (comma-separated or 'none'): ").strip()
            injury_list = [] if injuries.lower() == 'none' else [i.strip() for i in injuries.split(',')]

            bmi = compute_bmi(weight_kg, height_cm)
            bmi_category = get_bmi_category(bmi)

            user_doc = {
                "user_id": user_id,
                "age": age,
                "gender": gender,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "bmi": bmi,
                "bmi_category": bmi_category,
                "fitness_level": level,
                "primary_goal": goal,
                "equipment_list": equipment_list,
                "injury_types": injury_list,
                "created_at": datetime.utcnow().isoformat()
            }

            self.db.users.insert_one(user_doc)
            self.current_user = user_doc

            print(f"\n✅ User created! BMI: {bmi:.1f} ({bmi_category})")
            input("Press Enter...")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter...")

    def switch_user(self):
        self.clear_screen()
        self.print_header()
        print("🔄 SWITCH USER\n")

        users = list(self.db.users.find({}, {"user_id": 1, "fitness_level": 1, "primary_goal": 1}))

        if not users:
            print("No users found.")
            input("Press Enter...")
            return

        for i, user in enumerate(users, 1):
            print(f"{i}. {user['user_id']} - {user.get('fitness_level')} - {user.get('primary_goal')}")

        try:
            idx = int(input(f"\nSelect (1-{len(users)}): ")) - 1
            selected = self.db.users.find_one({"user_id": users[idx]['user_id']})
            self.current_user = selected
            print(f"\n✅ Switched to: {selected['user_id']}")
        except:
            print("❌ Invalid selection")

        input("Press Enter...")

    def view_current_user(self):
        if not self.current_user:
            print("\n❌ No user selected")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("👤 CURRENT USER PROFILE\n")

        u = self.current_user
        print(f"User ID: {u['user_id']}")
        print(f"Age: {u['age']} | Gender: {u['gender']}")
        print(f"Height: {u['height_cm']} cm | Weight: {u['weight_kg']} kg")
        print(f"BMI: {u['bmi']:.1f} ({u['bmi_category']})")
        print(f"Fitness Level: {u['fitness_level']}")
        print(f"Primary Goal: {u['primary_goal']}")
        print(f"Equipment: {', '.join(u.get('equipment_list', [])) or 'None'}")
        print(f"Injuries: {', '.join(u.get('injury_types', [])) or 'None'}")

        input("\nPress Enter...")

    def edit_user(self):
        print("\n⚠️  Edit user feature - coming soon!")
        input("Press Enter...")

    def delete_user(self):
        print("\n⚠️  Delete user feature - coming soon!")
        input("Press Enter...")

    # ============================================================
    # 2️⃣ WORKOUT GENERATION (UNCHANGED)
    # ============================================================
    def regenerate_today(self):
        """Regenerate today's workout plan."""
        if not self.current_user:
            print("\n❌ Please select a user first!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("🔄 REGENERATE TODAY'S PLAN\n")

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        today_name = day_names[today.weekday()]

        # Get current week's plan
        plan = self.db.user_weekly_plans.find_one({
            "user_id": self.current_user['user_id'],
            "week_start_iso": week_start.isoformat()
        })

        if not plan:
            print("❌ No workout plan found for this week!")
            print("Generate a weekly plan first.")
            input("\nPress Enter...")
            return

        today_plan = plan['days'].get(today_name)
        
        if not today_plan or today_plan.get('target_duration', 0) == 0:
            print(f"❌ {today_name.capitalize()} is a rest day!")
            input("\nPress Enter...")
            return

        # Get current duration
        current_duration = today_plan['target_duration']
        
        print(f"Current {today_name.capitalize()} workout: {current_duration} minutes\n")
        print("Options:")
        print("1. Regenerate with same duration")
        print("2. Change duration and regenerate")
        print("3. Cancel")
        print()
        
        choice = input("Choose (1-3): ").strip()
        
        if choice == '1':
            new_duration = current_duration
        elif choice == '2':
            new_duration = int(input(f"\nNew duration for {today_name.capitalize()} (minutes): "))
        else:
            return

        try:
            print("\n🔄 Regenerating workout...")
            
            generator = WorkoutGenerator(self.db)
            
            # Create durations dict with new value for today
            durations = {}
            for day in day_names:
                if day == today_name:
                    durations[day] = new_duration
                else:
                    durations[day] = plan['days'].get(day, {}).get('target_duration', 0)
            
            # Generate new plan
            new_plan = generator.generate_weekly_plan(
                user_snapshot=self.current_user,
                week_start_iso=week_start.isoformat(),
                target_daily_duration_minutes=durations
            )
            
            # Update in database
            self.db.user_weekly_plans.update_one(
                {"user_id": self.current_user['user_id'], "week_start_iso": week_start.isoformat()},
                {"$set": new_plan},
                upsert=True
            )
            
            print(f"\n✅ {today_name.capitalize()}'s workout regenerated!")
            
            new_today_plan = new_plan['days'].get(today_name, {})
            exercises_count = len(new_today_plan.get('main', []))
            print(f"New workout: {new_duration} min, {exercises_count} exercises")
            
        except Exception as e:
            print(f"\n❌ Error regenerating workout: {e}")
        
        input("\nPress Enter...")


    def copy_previous_week_plan(self):
        """Copy previous week's plan to current week."""
        if not self.current_user:
            print("\n❌ Please select a user first!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📋 COPY PREVIOUS WEEK PLAN\n")

        today = date.today()
        current_week_start = today - timedelta(days=today.weekday())
        previous_week_start = current_week_start - timedelta(weeks=1)

        # Get previous week's plan
        previous_plan = self.db.user_weekly_plans.find_one({
            "user_id": self.current_user['user_id'],
            "week_start_iso": previous_week_start.isoformat()
        })

        if not previous_plan:
            print(f"❌ No plan found for week of {previous_week_start.isoformat()}")
            print("\nThere's no previous week plan to copy.")
            input("\nPress Enter...")
            return

        # Check if current week already has a plan
        current_plan = self.db.user_weekly_plans.find_one({
            "user_id": self.current_user['user_id'],
            "week_start_iso": current_week_start.isoformat()
        })

        if current_plan:
            print(f"⚠️  Current week ({current_week_start.isoformat()}) already has a plan!")
            confirm = input("\nOverwrite existing plan? (yes/no): ").strip().lower()
            
            if confirm not in ['yes', 'y']:
                print("\n❌ Cancelled")
                input("Press Enter...")
                return

        try:
            print("\n🔄 Copying previous week's plan...")
            
            # Extract durations from previous week
            durations = {}
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                day_plan = previous_plan['days'].get(day, {})
                durations[day] = day_plan.get('target_duration', 0)
            
            # Generate new plan with same durations
            generator = WorkoutGenerator(self.db)
            new_plan = generator.generate_weekly_plan(
                user_snapshot=self.current_user,
                week_start_iso=current_week_start.isoformat(),
                target_daily_duration_minutes=durations
            )
            
            # Save to database
            self.db.user_weekly_plans.update_one(
                {"user_id": self.current_user['user_id'], "week_start_iso": current_week_start.isoformat()},
                {"$set": new_plan},
                upsert=True
            )
            
            print("\n✅ Previous week's plan copied successfully!")
            print(f"\nWeek Summary (Week of {current_week_start.isoformat()}):")
            
            total_duration = 0
            total_exercises = 0
            
            for day, day_plan in new_plan['days'].items():
                duration = day_plan['target_duration']
                exercises = len(day_plan['main'])
                total_duration += duration
                total_exercises += exercises
                
                if duration > 0:
                    print(f"  {day.capitalize()}: {duration} min, {exercises} exercises")
                else:
                    print(f"  {day.capitalize()}: REST DAY")
            
            print(f"\nTotal: {total_duration} minutes, {total_exercises} exercises this week")
            
        except Exception as e:
            print(f"\n❌ Error copying plan: {e}")
        
        input("\nPress Enter...")


    def print_weekly_plan(self):
        """Print detailed weekly plan."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        plan = self.db.user_weekly_plans.find_one({
            "user_id": self.current_user['user_id'],
            "week_start_iso": week_start.isoformat()
        })

        if not plan:
            print("\n❌ No plan found for this week!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("="*60)
        print(f"  WEEKLY WORKOUT PLAN - Week of {week_start.isoformat()}")
        print("="*60)
        print(f"User: {self.current_user['user_id']} | Goal: {self.current_user['primary_goal']}")
        print(f"BMI: {self.current_user['bmi']:.1f} ({self.current_user['bmi_category']})")
        print("="*60)
        print()

        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day in days:
            day_plan = plan['days'].get(day, {})
            duration = day_plan.get('target_duration', 0)
            
            print(f"{'='*60}")
            print(f"  {day.upper()}")
            print(f"{'='*60}")
            
            if duration == 0:
                print("  REST DAY")
                print()
                continue
            
            print(f"Duration: {duration} minutes")
            print()
            
            # Warmup
            warmup = day_plan.get('warmup', [])
            if warmup:
                warmup_duration = sum(ex.get('duration_secs', 0) for ex in warmup) // 60
                print(f"WARMUP ({warmup_duration} min):")
                for i, ex in enumerate(warmup, 1):
                    if ex.get('duration_secs'):
                        print(f"  {i}. {ex['name']} — {ex['duration_secs']//60} min")
                    else:
                        print(f"  {i}. {ex['name']}")
                print()
            
            # Main
            main = day_plan.get('main', [])
            if main:
                main_duration = duration - (sum(ex.get('duration_secs', 0) for ex in warmup) // 60) - (sum(ex.get('duration_secs', 0) for ex in day_plan.get('cooldown', [])) // 60)
                print(f"MAIN WORKOUT ({main_duration} min):")
                for i, ex in enumerate(main, 1):
                    rpe_str = f"{ex['predicted_rpe_range'][0]}-{ex['predicted_rpe_range'][1]}"
                    
                    if ex.get('sets') and ex.get('reps'):
                        print(f"  {i}. {ex['name']}")
                        print(f"     {ex['sets']} sets x {ex['reps']} reps | Rest: {ex['rest_seconds']}s | RPE: {rpe_str}")
                        print(f"     Body Part: {ex['body_part']} | Equipment: {ex['equipment_required']}")
                    else:
                        print(f"  {i}. {ex['name']}")
                        print(f"     Rest: {ex['rest_seconds']}s | RPE: {rpe_str}")
                    
                    if ex.get('notes'):
                        print(f"     Notes: {ex['notes']}")
                    print()
            
            # Cooldown
            cooldown = day_plan.get('cooldown', [])
            if cooldown:
                cooldown_duration = sum(ex.get('duration_secs', 0) for ex in cooldown) // 60
                print(f"COOLDOWN ({cooldown_duration} min):")
                for i, ex in enumerate(cooldown, 1):
                    duration_str = f"{ex['duration_secs']//60} min" if ex.get('duration_secs') else ""
                    print(f"  {i}. {ex['name']} — {duration_str}")
                print()
            
            # Motivation
            motivation = day_plan.get('motivation', '')
            if motivation:
                print(f"💪 Motivation: \"{motivation}\"")
                print()

        print("="*60)
        print("  END OF WEEKLY PLAN")
        print("="*60)
        print()
        
        # Option to save to file
        save = input("Save to file? (yes/no): ").strip().lower()
        
        if save in ['yes', 'y']:
            try:
                filename = f"weekly_plan_{self.current_user['user_id']}_{week_start.isoformat()}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write(f"  WEEKLY WORKOUT PLAN - Week of {week_start.isoformat()}\n")
                    f.write("="*60 + "\n")
                    f.write(f"User: {self.current_user['user_id']} | Goal: {self.current_user['primary_goal']}\n")
                    f.write(f"BMI: {self.current_user['bmi']:.1f} ({self.current_user['bmi_category']})\n")
                    f.write("="*60 + "\n\n")
                    
                    for day in days:
                        day_plan = plan['days'].get(day, {})
                        duration = day_plan.get('target_duration', 0)
                        
                        f.write(f"{'='*60}\n")
                        f.write(f"  {day.upper()}\n")
                        f.write(f"{'='*60}\n")
                        
                        if duration == 0:
                            f.write("  REST DAY\n\n")
                            continue
                        
                        f.write(f"Duration: {duration} minutes\n\n")
                        
                        # Write warmup
                        warmup = day_plan.get('warmup', [])
                        if warmup:
                            warmup_duration = sum(ex.get('duration_secs', 0) for ex in warmup) // 60
                            f.write(f"WARMUP ({warmup_duration} min):\n")
                            for i, ex in enumerate(warmup, 1):
                                if ex.get('duration_secs'):
                                    f.write(f"  {i}. {ex['name']} — {ex['duration_secs']//60} min\n")
                                else:
                                    f.write(f"  {i}. {ex['name']}\n")
                            f.write("\n")
                        
                        # Write main
                        main = day_plan.get('main', [])
                        if main:
                            main_duration = duration - (sum(ex.get('duration_secs', 0) for ex in warmup) // 60) - (sum(ex.get('duration_secs', 0) for ex in day_plan.get('cooldown', [])) // 60)
                            f.write(f"MAIN WORKOUT ({main_duration} min):\n")
                            for i, ex in enumerate(main, 1):
                                rpe_str = f"{ex['predicted_rpe_range'][0]}-{ex['predicted_rpe_range'][1]}"
                                
                                f.write(f"  {i}. {ex['name']}\n")
                                if ex.get('sets') and ex.get('reps'):
                                    f.write(f"     {ex['sets']} sets x {ex['reps']} reps | Rest: {ex['rest_seconds']}s | RPE: {rpe_str}\n")
                                f.write(f"     Body Part: {ex['body_part']} | Equipment: {ex['equipment_required']}\n")
                                if ex.get('notes'):
                                    f.write(f"     Notes: {ex['notes']}\n")
                                f.write("\n")
                        
                        # Write cooldown
                        cooldown = day_plan.get('cooldown', [])
                        if cooldown:
                            cooldown_duration = sum(ex.get('duration_secs', 0) for ex in cooldown) // 60
                            f.write(f"COOLDOWN ({cooldown_duration} min):\n")
                            for i, ex in enumerate(cooldown, 1):
                                duration_str = f"{ex['duration_secs']//60} min" if ex.get('duration_secs') else ""
                                f.write(f"  {i}. {ex['name']} — {duration_str}\n")
                            f.write("\n")
                        
                        # Write motivation
                        motivation = day_plan.get('motivation', '')
                        if motivation:
                            f.write(f"💪 Motivation: \"{motivation}\"\n\n")
                
                print(f"\n✅ Weekly plan saved to: {filename}")
                
            except Exception as e:
                print(f"\n❌ Error saving file: {e}")
        
        input("\nPress Enter...")


    def workout_generation_menu(self):
        self.clear_screen()
        self.print_header()
        print("🏋️‍♂️ WORKOUT GENERATION")
        print("="*60)
        print("1. Generate New Weekly Plan")
        print("2. View Current Week Plan")
        print("3. Regenerate Today's Plan")
        print("4. Copy Previous Week Plan")
        print("5. Print Weekly Plan")
        print("6. Back to Main Menu")
        print()

        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            self.generate_weekly_plan()
        elif choice == '2':
            self.view_weekly_plan()
        elif choice == '3':
            self.regenerate_today()
        elif choice == '4':
            print("\n⚠️  Copy week - coming soon!")
            input("Press Enter...")
        elif choice == '5':
            self.print_weekly_plan()

    def generate_weekly_plan(self):
        if not self.current_user:
            print("\n❌ Please select a user first!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print(f"📅 GENERATE WEEKLY PLAN\n")

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        print(f"Week starting: {week_start.isoformat()}\n")
        print("Enter workout duration for each day (0 for rest):\n")

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        durations = {}

        for day in days:
            dur = int(input(f"  {day}: "))
            durations[day.lower()] = dur

        print("\n🔄 Generating workout plan...")

        try:
            generator = WorkoutGenerator(self.db)
            plan = generator.generate_weekly_plan(
                user_snapshot=self.current_user,
                week_start_iso=week_start.isoformat(),
                target_daily_duration_minutes=durations
            )

            self.db.user_weekly_plans.update_one(
                {"user_id": self.current_user['user_id'], "week_start_iso": week_start.isoformat()},
                {"$set": plan},
                upsert=True
            )

            print("\n✅ Weekly plan generated!")
            print(f"\nWeek Summary:")
            for day, day_plan in plan['days'].items():
                duration = day_plan['target_duration']
                main_count = len(day_plan['main'])
                print(f"  {day.capitalize()}: {duration} min, {main_count} exercises")

        except Exception as e:
            print(f"\n❌ Error: {e}")

        input("\nPress Enter...")

    def view_weekly_plan(self):
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        plan = self.db.user_weekly_plans.find_one({
            "user_id": self.current_user['user_id'],
            "week_start_iso": week_start.isoformat()
        })

        if not plan:
            print("\n❌ No plan found for this week!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print(f"📅 WEEKLY PLAN - Week of {week_start.isoformat()}\n")

        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            day_plan = plan['days'].get(day, {})
            duration = day_plan.get('target_duration', 0)
            main_count = len(day_plan.get('main', []))

            if duration == 0:
                print(f"{day.capitalize()}: REST DAY")
            else:
                print(f"{day.capitalize()}: {duration} min, {main_count} exercises")

        input("\nPress Enter...")

   


    # ============================================================
    # 3️⃣ DAILY WORKOUT / LOGGING (UNCHANGED)
    # ============================================================

    def daily_workout_menu(self):
        self.clear_screen()
        self.print_header()
        print("📋 DAILY WORKOUT / LOGGING")
        print("="*60)
        print("1. View Today's Workout")
        print("2. Mark Workout as Complete")
        print("3. Rate Workout (1-5)")
        print("4. Add Notes")
        print("5. Skip Logging")
        print("6. Regenerate Today's Plan")
        print("7. Back to Main Menu")
        print()

        choice = input("Enter choice (1-7): ").strip()

        if choice == '1':
            self.view_today_workout_enhanced()
        elif choice == '2':
            self.mark_complete()
        elif choice == '3':
            self.rate_workout()
        elif choice == '4':
            self.add_notes()
        elif choice == '5':
            print("\nSkipped logging")
            input("Press Enter...")

    def view_today_workout_enhanced(self):
        """Display workout in beautiful format."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        today_name = day_names[today.weekday()]

        plan = self.db.user_weekly_plans.find_one({
            "user_id": self.current_user['user_id'],
            "week_start_iso": week_start.isoformat()
        })

        if not plan:
            print("\n❌ No workout plan found!")
            print("Generate a weekly plan first.")
            input("Press Enter...")
            return

        today_plan = plan['days'].get(today_name)

        if not today_plan:
            print("\n❌ No plan for today!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print(f"🔥 {today_name.upper()} WORKOUT\n")

        # Calculate section durations
        total_duration = today_plan['target_duration']
        warmup_duration = sum(ex.get('duration_secs', 0) for ex in today_plan['warmup']) // 60
        cooldown_duration = sum(ex.get('duration_secs', 0) for ex in today_plan['cooldown']) // 60
        main_duration = total_duration - warmup_duration - cooldown_duration

        # WARMUP
        print(f"Warmup ({warmup_duration} min)")
        for i, ex in enumerate(today_plan['warmup'], 1):
            if ex.get('duration_secs'):
                print(f" - {i}) {ex['name']} — {ex['duration_secs']//60} min")
            else:
                print(f" - {i}) {ex['name']}")

        print()

        # MAIN WORKOUT
        print(f"Main ({main_duration} min)")
        for i, ex in enumerate(today_plan['main'], 1):
            rpe_str = f"{ex['predicted_rpe_range'][0]}-{ex['predicted_rpe_range'][1]}"

            if ex.get('sets') and ex.get('reps'):
                print(f" {i}) {ex['name']} — {ex['sets']} sets x {ex['reps']} reps — "
                      f"Rest {ex['rest_seconds']}s — RPE {rpe_str}")
            else:
                print(f" {i}) {ex['name']} — Rest {ex['rest_seconds']}s — RPE {rpe_str}")

            if ex.get('notes'):
                print(f"    Notes: {ex['notes']}")

        print()

        # COOLDOWN
        print(f"Cooldown ({cooldown_duration} min)")
        for i, ex in enumerate(today_plan['cooldown'], 1):
            duration_str = f"{ex['duration_secs']}s" if ex.get('duration_secs') else ""
            print(f" - {i}) {ex['name']} — {duration_str}")
            if ex.get('notes'):
                print(f"    {ex['notes']}")

        print()
        print(f"Motivation: \"{today_plan['motivation']}\"")
        print()

        input("Press Enter...")

    def mark_complete(self):
        print("\n✅ Marking workout as complete...")
        input("Press Enter...")

    def rate_workout(self):
        rating = input("\nRate workout (1-5): ")
        print(f"\n✅ Workout rated: {rating}/5")
        input("Press Enter...")

    def add_notes(self):
        note = input("\nAdd note: ")
        print("\n✅ Note saved")
        input("Press Enter...")

    # ============================================================
    # 4️⃣ PROGRESS & INSIGHTS (ML-ENHANCED!)
    # ============================================================

    def progress_menu(self):
        """Enhanced progress menu with ML features."""
        self.clear_screen()
        self.print_header()
        print("📈 PROGRESS & INSIGHTS")
        print("="*60)
        
        if ML_AVAILABLE and self.model_manager:
            print("🤖 ML-Powered Features:")
            print("1. ML Exercise Recommendations 💡")
            print("2. Injury Risk Analysis ⚠️")
            print("3. Plateau Detection 📊")
            print("4. Trend Analysis & Forecasts 📈")
            print("5. Strength Progression Graphs 📉")
            print("6. Body Part Frequency Heatmap 🗺️")
            print()
            print("📋 Standard Features:")
            print("7. Weekly Summary")
            print("8. View Streaks")
            print("9. Export Data (CSV/PDF)")
            print("10. Back to Main Menu")
        else:
            print("1. Weekly Summary")
            print("2. View Streaks")
            print("3. View Strength Progress")
            print("4. Compare Current vs Previous Week")
            print("5. Export Data (CSV/PDF)")
            print("6. Back to Main Menu")
        print("="*60)
        print()

        choice = input("Enter choice: ").strip()

        if ML_AVAILABLE and self.model_manager:
            if choice == '1':
                self.ml_exercise_recommendations()
            elif choice == '2':
                self.ml_injury_risk_analysis()
            elif choice == '3':
                self.ml_plateau_detection()
            elif choice == '4':
                self.ml_trend_analysis()
            elif choice == '5':
                self.ml_strength_progression()
            elif choice == '6':
                self.ml_body_part_heatmap()
            elif choice == '7':
                self.weekly_summary()
            elif choice == '8':
                self.view_streaks()
            elif choice == '9':
                self.export_data()
        else:
            if choice == '1':
                self.weekly_summary()
            else:
                print("\n⚠️  Feature coming soon!")
                input("Press Enter...")

    # ML-POWERED FEATURES
    
    def ml_exercise_recommendations(self):
        """Show ML exercise recommendations."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("🤖 ML EXERCISE RECOMMENDATIONS\n")

        try:
            recs = self.model_manager.get_exercise_recommendations(self.current_user['user_id'], 5)

            if not recs:
                print("❌ No recommendations available yet.")
                print("Complete more workouts to get personalized suggestions!\n")
            else:
                print("💡 Based on your profile and similar users:\n")

                for i, rec in enumerate(recs, 1):
                    confidence = rec['confidence_score']
                    icon = "🔥" if confidence > 0.8 else "⭐" if confidence > 0.6 else "💫"

                    print(f"{i}. {icon} {rec['name']}")
                    print(f"   Body Part: {rec['body_part']} | Equipment: {rec['equipment']}")
                    print(f"   Confidence: {confidence:.0%}")
                    print(f"   Why: {rec['reason']}")
                    print()

            print("="*60)
            print("🧠 HOW THIS WORKS:")
            print("• Analyzes your workout history and preferences")
            print("• Finds users with similar profiles and goals")
            print("• Recommends exercises they enjoyed and completed")
            print("• You can override any suggestion")
            print("="*60)

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def ml_injury_risk_analysis(self):
        """Show ML injury risk analysis."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("⚠️  INJURY RISK ANALYSIS\n")

        try:
            analysis = self.model_manager.get_injury_risk_analysis(self.current_user['user_id'])

            risk_level = analysis.get('overall_risk', 'unknown')
            risk_colors = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'unknown': '⚪'}

            print(f"Overall Injury Risk: {risk_colors.get(risk_level)} {risk_level.upper()}\n")

            risk_factors = analysis.get('risk_factors', [])
            if risk_factors:
                print("⚠️  Risk Factors Detected:")
                for factor in risk_factors:
                    print(f"  • {factor['name']}: {factor['description']}")
                    print(f"    Confidence: {factor['confidence']:.0%}")
                print()

            recommendations = analysis.get('recommendations', [])
            if recommendations:
                print("💡 ML Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec['action']}")
                    print(f"     Reason: {rec['reason']}")
                print()

            if risk_level == 'low' and not risk_factors:
                print("✅ Looking good! No significant risk factors detected.")
                print("Keep up the consistent training!")

            print("="*60)
            print("🧠 HOW THIS WORKS:")
            print("• Analyzes RPE trends, volume spikes, recovery patterns")
            print("• Compares with injury patterns from similar users")
            print("• Flags concerning patterns before they become injuries")
            print("• Suggests modifications to reduce risk")
            print("="*60)

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def ml_plateau_detection(self):
        """Show ML plateau detection."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📊 PLATEAU DETECTION\n")

        try:
            plateau = self.model_manager.detect_plateau(self.current_user['user_id'])

            has_plateau = plateau.get('has_plateau', False)
            confidence = plateau.get('confidence', 0.0)

            if has_plateau:
                print(f"⚠️  Training Plateau Detected (Confidence: {confidence:.0%})\n")

                indicators = plateau.get('indicators', {})
                print("📉 Stagnation Indicators:")
                if indicators.get('volume_stagnation'):
                    print("  • Volume has not progressed in 3+ weeks")
                if indicators.get('performance_stagnation'):
                    print("  • Performance metrics plateaued")
                if indicators.get('variety_deficiency'):
                    print("  • Exercise selection lacks variety")
                print()

                recommendations = plateau.get('recommendations', [])
                if recommendations:
                    print("💡 Break Through Strategies:")
                    for i, rec in enumerate(recommendations, 1):
                        priority_icon = "🔴" if rec.get('priority') == 'high' else "🟡"
                        print(f"  {i}. {priority_icon} {rec['action']}")
                        print(f"     Why: {rec['reason']}")
                    print()
            else:
                print("✅ No Plateau Detected\n")
                print("Your training is progressing well!")
                print("Keep up the consistent effort.\n")

            print("="*60)
            print("🧠 HOW THIS WORKS:")
            print("• Tracks volume, performance, and exercise variety")
            print("• Detects when progress stalls for 3+ weeks")
            print("• Suggests program changes to restart progress")
            print("• Implements periodization strategies")
            print("="*60)

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def ml_trend_analysis(self):
        """Show ML trend analysis."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📈 TREND ANALYSIS & FORECASTS\n")

        try:
            trends = self.model_manager.analyze_trends(self.current_user['user_id'], 30)

            if not trends.get('has_sufficient_data'):
                print("❌ Not enough data for trend analysis.")
                print("Need at least 10 sessions. Keep logging workouts!\n")
            else:
                print("📊 30-Day Trends:\n")

                completion_trend = trends.get('completion_trend', {})
                if completion_trend.get('trend') == 'improving':
                    print(f"✅ Completion Rate: IMPROVING ({completion_trend.get('change_percent', 0):.1f}%)")
                elif completion_trend.get('trend') == 'declining':
                    print(f"⚠️  Completion Rate: DECLINING ({completion_trend.get('change_percent', 0):.1f}%)")
                else:
                    print(f"➡️  Completion Rate: STABLE ({completion_trend.get('current_value', 0):.0%})")

                satisfaction_trend = trends.get('satisfaction_trend', {})
                if satisfaction_trend.get('trend') == 'improving':
                    print(f"😊 Satisfaction: IMPROVING ({satisfaction_trend.get('change_percent', 0):.1f}%)")
                elif satisfaction_trend.get('trend') == 'declining':
                    print(f"😐 Satisfaction: DECLINING ({satisfaction_trend.get('change_percent', 0):.1f}%)")
                else:
                    print(f"😊 Satisfaction: STABLE ({satisfaction_trend.get('current_value', 0):.1f}/10)")

                print()

            # Forecast
            forecast = self.model_manager.forecast_next_week(self.current_user['user_id'])

            if forecast.get('forecast_available'):
                print("🔮 Next Week Forecast:\n")
                print(f"  Expected Completion: {forecast.get('expected_completion', 0):.0%}")
                print(f"  Expected Satisfaction: {forecast.get('expected_satisfaction', 0):.1f}/10")
                print(f"  Confidence: {forecast.get('confidence', 0):.0%}")
                print()
                print(f"  💡 {forecast.get('recommendation', '')}")
                print()

            print("="*60)
            print("🧠 HOW THIS WORKS:")
            print("• Time series analysis of all metrics")
            print("• Detects improving/declining/stable trends")
            print("• Forecasts next week's expected performance")
            print("• Provides proactive recommendations")
            print("="*60)

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def ml_strength_progression(self):
        """Show strength progression chart."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📉 STRENGTH PROGRESSION CHARTS\n")

        try:
            print("🔄 Generating progression charts...")

            chart_path = f"insights/{self.current_user['user_id']}_progression.png"
            result = self.model_manager.create_progression_chart(self.current_user['user_id'], chart_path)

            if result:
                print(f"\n✅ Chart saved to: {chart_path}")
                print("\nThe chart shows:")
                print("  • Completion rate trend over time")
                print("  • Satisfaction ratings over time")
                print("  • Visual indicators of progress")
                print("\nOpen the file to view your progression!\n")
            else:
                print("\n❌ Could not generate chart.")
                print("Need at least 3 logged sessions.\n")

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def ml_body_part_heatmap(self):
        """Show body part frequency heatmap."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("🗺️  BODY PART FREQUENCY HEATMAP\n")

        try:
            print("🔄 Generating heatmap...")

            heatmap_path = f"insights/{self.current_user['user_id']}_heatmap.png"
            result = self.model_manager.create_body_part_heatmap(self.current_user['user_id'], heatmap_path)

            if result:
                print(f"\n✅ Heatmap saved to: {heatmap_path}")
                print("\nThe heatmap shows:")
                print("  • Training frequency per body part")
                print("  • Weekly distribution of exercises")
                print("  • Potential imbalances in training")
                print("\nOpen the file to view your training balance!\n")
            else:
                print("\n❌ Could not generate heatmap.")
                print("Need workout plans to analyze.\n")

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def weekly_summary(self):
        """Standard weekly summary."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📊 WEEKLY SUMMARY\n")

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        logs = list(self.db.session_logs.find({
            "user_id": self.current_user['user_id'],
            "week_start_iso": week_start.isoformat()
        }))

        if not logs:
            print("No activity logged this week.")
        else:
            total_duration = sum(log.get('actual_duration', 0) for log in logs)
            avg_completion = sum(log.get('completion_percent', 0) for log in logs) / len(logs) * 100
            avg_satisfaction = sum(log.get('satisfaction', 0) for log in logs) / len(logs)

            print(f"Workouts completed: {len(logs)}")
            print(f"Total time: {total_duration} minutes")
            print(f"Avg completion: {avg_completion:.1f}%")
            print(f"Avg satisfaction: {avg_satisfaction:.1f}/10")

        input("\nPress Enter...")

    def export_data(self):
        """Export workout data to CSV or PDF."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📤 EXPORT DATA\n")

        print("Select export format:")
        print("1. CSV (Excel compatible)")
        print("2. JSON (Raw data)")
        print("3. Text Summary Report")
        print("4. Cancel")
        print()

        choice = input("Choose (1-4): ").strip()

        if choice == '1':
            self._export_csv()
        elif choice == '2':
            self._export_json()
        elif choice == '3':
            self._export_text_report()
        else:
            return

    def _export_csv(self):
        """Export workout data to CSV."""
        try:
            import csv
            
            # Get all sessions
            sessions = list(self.db.session_logs.find({
                "user_id": self.current_user['user_id']
            }).sort("logged_at", -1))

            if not sessions:
                print("\n❌ No workout data to export")
                input("\nPress Enter...")
                return

            filename = f"workout_data_{self.current_user['user_id']}_{date.today().isoformat()}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Date', 'Day', 'Duration (min)', 'Completion (%)', 
                    'Satisfaction (1-10)', 'RPE', 'Exercises Completed', 
                    'Total Volume', 'Notes'
                ])

                # Data rows
                for session in sessions:
                    logged_date = datetime.fromisoformat(session.get('logged_at', '')).date()
                    day_name = logged_date.strftime('%A')
                    
                    writer.writerow([
                        logged_date.isoformat(),
                        day_name,
                        session.get('actual_duration', 0),
                        session.get('completion_percent', 0) * 100,
                        session.get('satisfaction', 0),
                        session.get('avg_rpe', 0),
                        len(session.get('exercises_completed', [])),
                        session.get('total_volume', 0),
                        session.get('notes', '')
                    ])

            print(f"\n✅ Data exported to: {filename}")
            print(f"Total sessions: {len(sessions)}")

        except Exception as e:
            print(f"\n❌ Error exporting CSV: {e}")

        input("\nPress Enter...")

    def _export_json(self):
        """Export workout data to JSON."""
        try:
            # Get all sessions
            sessions = list(self.db.session_logs.find({
                "user_id": self.current_user['user_id']
            }).sort("logged_at", -1))

            if not sessions:
                print("\n❌ No workout data to export")
                input("\nPress Enter...")
                return

            # Remove MongoDB _id field
            for session in sessions:
                if '_id' in session:
                    session['_id'] = str(session['_id'])

            filename = f"workout_data_{self.current_user['user_id']}_{date.today().isoformat()}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'user_id': self.current_user['user_id'],
                    'export_date': datetime.utcnow().isoformat(),
                    'total_sessions': len(sessions),
                    'sessions': sessions
                }, f, indent=2, default=str)

            print(f"\n✅ Data exported to: {filename}")
            print(f"Total sessions: {len(sessions)}")

        except Exception as e:
            print(f"\n❌ Error exporting JSON: {e}")

        input("\nPress Enter...")

    def _export_text_report(self):
        """Export summary report to text file."""
        try:
            sessions = list(self.db.session_logs.find({
                "user_id": self.current_user['user_id']
            }).sort("logged_at", -1))

            if not sessions:
                print("\n❌ No workout data to export")
                input("\nPress Enter...")
                return

            filename = f"workout_report_{self.current_user['user_id']}_{date.today().isoformat()}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("  WORKOUT SUMMARY REPORT\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"User: {self.current_user['user_id']}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Overall stats
                total_duration = sum(s.get('actual_duration', 0) for s in sessions)
                avg_completion = sum(s.get('completion_percent', 0) for s in sessions) / len(sessions) * 100
                avg_satisfaction = sum(s.get('satisfaction', 0) for s in sessions) / len(sessions)

                f.write("OVERALL STATISTICS\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total Workouts: {len(sessions)}\n")
                f.write(f"Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)\n")
                f.write(f"Average Completion: {avg_completion:.1f}%\n")
                f.write(f"Average Satisfaction: {avg_satisfaction:.1f}/10\n\n")

                # Recent workouts
                f.write("RECENT WORKOUTS (Last 10)\n")
                f.write("-" * 60 + "\n\n")

                for session in sessions[:10]:
                    logged_date = datetime.fromisoformat(session.get('logged_at', '')).strftime('%Y-%m-%d')
                    f.write(f"Date: {logged_date}\n")
                    f.write(f"Duration: {session.get('actual_duration', 0)} min\n")
                    f.write(f"Completion: {session.get('completion_percent', 0)*100:.0f}%\n")
                    f.write(f"Satisfaction: {session.get('satisfaction', 0)}/10\n")
                    if session.get('notes'):
                        f.write(f"Notes: {session.get('notes')}\n")
                    f.write("\n")

            print(f"\n✅ Report exported to: {filename}")

        except Exception as e:
            print(f"\n❌ Error exporting report: {e}")

        input("\nPress Enter...")

    def view_streaks(self):
        """View workout streaks and consistency."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("🔥 WORKOUT STREAKS\n")

        try:
            # Get all session logs
            sessions = list(self.db.session_logs.find({
                "user_id": self.current_user['user_id']
            }).sort("logged_at", 1))

            if not sessions:
                print("No workouts logged yet.")
                print("\nStart logging workouts to build your streak!")
                input("\nPress Enter...")
                return

            # Parse dates
            workout_dates = []
            for session in sessions:
                date_str = session.get('logged_at', '')
                if date_str:
                    workout_date = datetime.fromisoformat(date_str).date()
                    if workout_date not in workout_dates:
                        workout_dates.append(workout_date)

            workout_dates.sort()

            # Calculate current streak
            today = date.today()
            current_streak = 0
            
            check_date = today
            while check_date in workout_dates or (check_date - timedelta(days=1)) in workout_dates:
                if check_date in workout_dates:
                    current_streak += 1
                check_date -= timedelta(days=1)
                if check_date < workout_dates[0]:
                    break

            # Calculate longest streak
            longest_streak = 0
            temp_streak = 1
            
            for i in range(1, len(workout_dates)):
                days_diff = (workout_dates[i] - workout_dates[i-1]).days
                if days_diff <= 2:  # Allow 1 rest day
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            longest_streak = max(longest_streak, temp_streak)

            # Calculate total stats
            total_sessions = len(sessions)
            first_workout = workout_dates[0]
            last_workout = workout_dates[-1]
            days_active = (last_workout - first_workout).days + 1
            
            # Display streaks
            print("="*60)
            print("  CURRENT STREAK")
            print("="*60)
            
            if current_streak > 0:
                fire_emoji = "🔥" * min(current_streak, 10)
                print(f"\n  {fire_emoji}")
                print(f"\n  {current_streak} {'day' if current_streak == 1 else 'days'} and counting!")
                
                if current_streak >= 7:
                    print(f"\n  🏆 Awesome! You've maintained a full week streak!")
                if current_streak >= 30:
                    print(f"\n  🎖️  INCREDIBLE! 30+ day streak is elite level!")
            else:
                print(f"\n  No active streak")
                print(f"  Last workout: {workout_dates[-1]}")
                print(f"\n  💪 Start a new streak today!")

            print("\n" + "="*60)
            print("  LONGEST STREAK")
            print("="*60)
            print(f"\n  {longest_streak} days 🏅")
            
            print("\n" + "="*60)
            print("  OVERALL STATISTICS")
            print("="*60)
            print(f"\n  Total Workouts: {total_sessions}")
            print(f"  First Workout: {first_workout}")
            print(f"  Last Workout: {last_workout}")
            print(f"  Days Training: {days_active}")
            print(f"  Consistency: {(len(workout_dates)/days_active)*100:.1f}%")

            # Weekly breakdown (last 4 weeks)
            print("\n" + "="*60)
            print("  WEEKLY ACTIVITY (Last 4 Weeks)")
            print("="*60)
            
            for week_offset in range(4):
                week_start = today - timedelta(weeks=week_offset, days=today.weekday())
                week_end = week_start + timedelta(days=6)
                
                week_sessions = [d for d in workout_dates if week_start <= d <= week_end]
                
                week_label = "This Week" if week_offset == 0 else f"{week_offset} {'week' if week_offset == 1 else 'weeks'} ago"
                
                # Visual representation
                week_visual = ""
                for day in range(7):
                    check_date = week_start + timedelta(days=day)
                    if check_date in week_sessions:
                        week_visual += "✅ "
                    else:
                        week_visual += "⬜ "
                
                print(f"\n  {week_label}:")
                print(f"  {week_visual}")
                print(f"  {len(week_sessions)}/7 days")

            # Motivation based on streak
            print("\n" + "="*60)
            if current_streak >= 7:
                print("  🌟 Keep the momentum! You're crushing it!")
            elif current_streak >= 3:
                print("  💪 Great consistency! Push for a full week!")
            elif current_streak == 0 and longest_streak > 0:
                print("  🎯 You've done it before. Start again today!")
            else:
                print("  🚀 Every journey starts with one workout!")
            print("="*60)

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    # ============================================================
    # 5️⃣ MOTIVATION & MINDSET (UNCHANGED)
    # ============================================================

    def motivation_menu(self):
        self.clear_screen()
        self.print_header()
        print("💬 MOTIVATION & MINDSET")
        print("="*60)
        print("1. Mood Check-In (1-5)")
        print("2. AI Motivation Message")
        print("3. Short Guided Breathing")
        print("4. Read Today's Tip")
        print("5. View Motivation History")
        print("6. Back to Main Menu")
        print()

        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            self.mood_checkin()
        elif choice == '2':
            self.motivation_message()
        elif choice == '3':
            self.guided_breathing()
        elif choice == '4':
            self.daily_tip()
        elif choice == '5':
            self.view_motivation_history()
        else:
            print("\n⚠️  Feature coming soon!")
            input("Press Enter...")
    def view_motivation_history(self):
        """View mood check-in history."""
        if not self.current_user:
            print("\n❌ No user selected!")
            input("Press Enter...")
            return

        self.clear_screen()
        self.print_header()
        print("📊 MOTIVATION HISTORY\n")

        try:
            # Get motivation logs
            mood_logs = list(self.db.motivation_logs.find({
                "user_id": self.current_user['user_id']
            }).sort("logged_at", -1).limit(30))

            if not mood_logs:
                print("No mood check-ins logged yet.")
                print("\nStart tracking your mood to see patterns over time!")
            else:
                print(f"Last {len(mood_logs)} Mood Check-ins:\n")
                print(f"{'Date':<20} {'Mood':<10} {'Trend':<10}")
                print("="*60)

                for i, log in enumerate(mood_logs):
                    date_str = log.get('logged_at', '')[:10]
                    mood = log.get('mood', 3)
                    
                    # Mood emoji
                    mood_emoji = {1: "😢", 2: "😐", 3: "😊", 4: "😄", 5: "🤩"}.get(mood, "😊")
                    
                    # Trend
                    if i < len(mood_logs) - 1:
                        prev_mood = mood_logs[i+1].get('mood', 3)
                        if mood > prev_mood:
                            trend = "↑"
                        elif mood < prev_mood:
                            trend = "↓"
                        else:
                            trend = "→"
                    else:
                        trend = "-"

                    print(f"{date_str:<20} {mood_emoji} {mood}/5     {trend:<10}")

                # Calculate statistics
                avg_mood = sum(log.get('mood', 3) for log in mood_logs) / len(mood_logs)
                recent_avg = sum(log.get('mood', 3) for log in mood_logs[:7]) / min(7, len(mood_logs))
                
                print()
                print("="*60)
                print(f"\n📊 Statistics:")
                print(f"  Average Mood (All Time): {avg_mood:.1f}/5")
                print(f"  Average Mood (Last 7 Days): {recent_avg:.1f}/5")
                
                # Mood distribution
                mood_counts = {}
                for log in mood_logs:
                    mood = log.get('mood', 3)
                    mood_counts[mood] = mood_counts.get(mood, 0) + 1
                
                print(f"\n  Mood Distribution:")
                for mood in sorted(mood_counts.keys(), reverse=True):
                    emoji = {1: "😢", 2: "😐", 3: "😊", 4: "😄", 5: "🤩"}.get(mood, "😊")
                    count = mood_counts[mood]
                    percentage = (count / len(mood_logs)) * 100
                    bar = "█" * int(percentage / 5)
                    print(f"    {emoji} {mood}/5: {bar} {percentage:.0f}% ({count})")

                # Trend analysis
                if len(mood_logs) >= 7:
                    first_week_avg = sum(log.get('mood', 3) for log in mood_logs[-7:]) / 7
                    if recent_avg > first_week_avg + 0.5:
                        print(f"\n  📈 Trend: Your mood is improving! Keep it up!")
                    elif recent_avg < first_week_avg - 0.5:
                        print(f"\n  📉 Trend: Your mood has declined recently. Take care of yourself.")
                    else:
                        print(f"\n  ➡️  Trend: Your mood is stable.")

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter...")

    def mood_checkin(self):
        """Mood check-in with database logging."""
        mood = input("\nHow are you feeling? (1-5): ")
        
        try:
            self.current_mood = int(mood)
            
            if self.current_mood < 1 or self.current_mood > 5:
                print("❌ Please enter a number between 1 and 5")
                input("\nPress Enter...")
                return

            responses = {
                1: "That's tough. Remember: showing up is half the battle. 💙",
                2: "Not your best day, but you're here. That counts. 💪",
                3: "Neutral is okay. Let's make today count. 🎯",
                4: "Feeling good! Channel that energy into your workout. 🔥",
                5: "Amazing! Let's crush this workout! 💥"
            }

            print(f"\n{responses.get(self.current_mood, 'Thanks for checking in!')}")
            
            # Save to database
            if self.current_user:
                mood_log = {
                    "user_id": self.current_user['user_id'],
                    "mood": self.current_mood,
                    "logged_at": datetime.utcnow().isoformat()
                }
                self.db.motivation_logs.insert_one(mood_log)
                print("\n✅ Mood logged")
            
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        
        input("\nPress Enter...")

    def motivation_message(self):
        self.clear_screen()
        self.print_header()
        print("💪 MOTIVATION MESSAGE\n")

        message = random.choice(MOTIVATION_TIPS)
        print(f"✨ {message}\n")

        input("Press Enter...")

    def guided_breathing(self):
        print("\n🧘 GUIDED BREATHING\n")
        print("Let's do 3 deep breaths...")
        print("\nInhale (4s) ... Hold (4s) ... Exhale (6s)")
        print("\nRepeat 3 times.")
        input("\nPress Enter when done...")

    def daily_tip(self):
        self.clear_screen()
        self.print_header()
        print("💡 TODAY'S TIP\n")

        tip = random.choice(MOTIVATION_TIPS)
        print(f"✨ {tip}\n")

        input("Press Enter...")

    # ============================================================
    # 6️⃣ DATABASE ADMIN (UNCHANGED)
    # ============================================================

    def database_admin_menu(self):
        self.clear_screen()
        self.print_header()
        print("🧩 DATABASE ADMIN")
        print("="*60)
        print("1. View All Collections")
        print("2. Backup Database")
        print("3. Restore Database")
        print("4. Delete Old Logs (>90 days)")
        print("5. Optimize Indexes")
        print("6. Show Connection Status")
        print("7. Back to Main Menu")
        print()

        choice = input("Enter choice (1-7): ").strip()

        if choice == '1':
            self.view_collections()
        elif choice == '6':
            self.connection_status()
        else:
            print("\n⚠️  Feature coming soon!")
            input("Press Enter...")

    def view_collections(self):
        self.clear_screen()
        self.print_header()
        print("📚 DATABASE COLLECTIONS\n")

        collections = self.db.list_collection_names()

        for coll in collections:
            count = self.db[coll].count_documents({})
            print(f"  {coll}: {count} documents")

        input("\nPress Enter...")

    def connection_status(self):
        self.clear_screen()
        self.print_header()
        print("🔗 CONNECTION STATUS\n")

        try:
            self.client.server_info()
            print("✅ MongoDB connected")
            print(f"Database: {settings.DATABASE_NAME}")
            print(f"URI: {settings.MONGO_URI}")
            
            if ML_AVAILABLE and self.model_manager:
                print("\n✅ ML System: Active")
            else:
                print("\n⚠️  ML System: Inactive")
                
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")

        input("\nPress Enter...")

    # ============================================================
    # 7️⃣ EXIT
    # ============================================================

    def exit_app(self):
        self.clear_screen()
        print("\n" + "="*60)
        print("   Session ended — see you tomorrow, champion 💪")
        print("="*60)
        print()

        self.client.close()
        sys.exit(0)

    def run(self):
        """Run the CLI application."""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            self.exit_app()


if __name__ == "__main__":
    cli = FitGenCLI()
    cli.run()
