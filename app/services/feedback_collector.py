"""
Interactive Feedback Collection Flow
User interface for collecting workout and exercise feedback
"""

from typing import Dict, List, Any
from app.services.exercise_feedback_system import (
    PreWorkoutFeeling, PostWorkoutFeeling, ExerciseDifficulty,
    ExerciseFeedback, WorkoutSession, FeedbackManager
)

class FeedbackCollector:
    """Interactive feedback collector for CLI/API."""

    def __init__(self, feedback_manager: FeedbackManager):
        self.manager = feedback_manager

    def start_workout(
        self,
        user_id: str,
        workout_id: str,
        day_name: str
    ) -> WorkoutSession:
        """
        Start workout and collect pre-workout feedback.

        Interactive prompts:
        1. How do you feel right now?
        2. Energy level (1-10)
        3. Any notes?
        """
        print("\n" + "="*60)
        print(" 🏋️  STARTING WORKOUT")
        print("="*60)

        # Collect pre-workout feeling
        print("\n1. How do you feel RIGHT NOW (before workout)?")
        feelings = {
            "1": PreWorkoutFeeling.ENERGIZED,
            "2": PreWorkoutFeeling.NORMAL,
            "3": PreWorkoutFeeling.TIRED,
            "4": PreWorkoutFeeling.SORE,
            "5": PreWorkoutFeeling.UNMOTIVATED,
            "6": PreWorkoutFeeling.STRESSED,
            "7": PreWorkoutFeeling.EXCELLENT
        }

        for key, feeling in feelings.items():
            print(f"   {key}. {feeling.value.replace('_', ' ').title()}")

        feeling_choice = input("   Your choice (1-7): ").strip()
        pre_feeling = feelings.get(feeling_choice, PreWorkoutFeeling.NORMAL)

        # Collect energy level
        print("\n2. Energy level RIGHT NOW?")
        print("   1 = Exhausted ... 10 = Fully Energized")
        pre_energy = int(input("   Your level (1-10): ").strip() or "5")
        pre_energy = max(1, min(10, pre_energy))

        # Optional notes
        print("\n3. Any notes before starting? (optional)")
        pre_notes = input("   Notes: ").strip()

        # Create session
        session = WorkoutSession(
            user_id=user_id,
            workout_id=workout_id,
            day_name=day_name,
            pre_workout_feeling=pre_feeling,
            pre_workout_energy=pre_energy,
            pre_workout_notes=pre_notes
        )

        print("\n✅ Pre-workout feedback recorded!")
        print(f"   Feeling: {pre_feeling.value.title()}")
        print(f"   Energy: {pre_energy}/10")
        print("\n🎯 Let's crush this workout!\n")

        return session

    def collect_exercise_feedback(
        self,
        session: WorkoutSession,
        exercise: Dict[str, Any],
        planned_sets: int,
        planned_reps: int
    ) -> ExerciseFeedback:
        """
        Collect feedback for individual exercise AFTER completing it.

        Interactive prompts:
        1. Star rating (1-5)
        2. Difficulty level
        3. Sets/reps completed
        4. Weight used (if applicable)
        5. Form quality (optional)
        6. Enjoyment (optional)
        7. Would you do this again?
        8. Notes
        """
        print("\n" + "-"*60)
        print(f" 📋 FEEDBACK: {exercise['name']}")
        print("-"*60)

        # 1. Star rating
        print("\n⭐ Overall rating for this exercise?")
        print("   1 = Hated it ... 5 = Loved it")
        rating = int(input("   Rating (1-5): ").strip() or "3")
        rating = max(1, min(5, rating))

        # 2. Difficulty
        print("\n💪 How difficult was it?")
        difficulties = {
            "1": ExerciseDifficulty.TOO_EASY,
            "2": ExerciseDifficulty.EASY,
            "3": ExerciseDifficulty.PERFECT,
            "4": ExerciseDifficulty.CHALLENGING,
            "5": ExerciseDifficulty.TOO_HARD
        }
        for key, diff in difficulties.items():
            print(f"   {key}. {diff.value.replace('_', ' ').title()}")

        diff_choice = input("   Your choice (1-5): ").strip()
        difficulty = difficulties.get(diff_choice, ExerciseDifficulty.PERFECT)

        # 3. Sets/reps completed
        print(f"\n📊 Sets/Reps (planned: {planned_sets}×{planned_reps})")
        sets_done = int(input(f"   Sets completed: ").strip() or str(planned_sets))
        reps_done = int(input(f"   Reps per set: ").strip() or str(planned_reps))

        # 4. Weight (optional)
        weight = None
        if exercise.get('equipment') not in ['Bodyweight', 'Body Only']:
            weight_input = input("   Weight used (kg/lbs, optional): ").strip()
            if weight_input:
                weight = float(weight_input)

        # 5. Form quality (optional)
        print("\n🎯 Form quality? (optional, press Enter to skip)")
        print("   1 = Poor ... 5 = Perfect")
        form_input = input("   Form (1-5): ").strip()
        form_quality = int(form_input) if form_input else None
        if form_quality:
            form_quality = max(1, min(5, form_quality))

        # 6. Enjoyment (optional)
        print("\n😊 Enjoyment level? (optional, press Enter to skip)")
        print("   1 = Boring ... 5 = Super fun")
        enjoy_input = input("   Enjoyment (1-5): ").strip()
        enjoyment = int(enjoy_input) if enjoy_input else None
        if enjoyment:
            enjoyment = max(1, min(5, enjoyment))

        # 7. Would repeat
        print("\n🔄 Would you like to do this exercise again?")
        repeat_input = input("   (yes/no, default yes): ").strip().lower()
        would_repeat = repeat_input != "no"

        # 8. Notes
        notes = input("\n📝 Any notes? (optional): ").strip()

        # Create feedback object
        feedback = ExerciseFeedback(
            exercise_id=exercise.get('id', exercise['name']),
            exercise_name=exercise['name'],
            rating=rating,
            difficulty=difficulty,
            sets_completed=sets_done,
            reps_completed=reps_done,
            weight_used=weight,
            form_quality=form_quality,
            enjoyment=enjoyment,
            would_repeat=would_repeat,
            notes=notes
        )

        # Add to session
        session.add_exercise_feedback(feedback)

        print(f"\n✅ Feedback recorded for {exercise['name']}")
        print(f"   Rating: {'⭐' * rating}")
        print(f"   Difficulty: {difficulty.value.title()}")

        return feedback

    def complete_workout(
        self,
        session: WorkoutSession
    ) -> str:
        """
        Complete workout and collect post-workout feedback.

        Interactive prompts:
        1. How do you feel NOW (after workout)?
        2. Energy level NOW (1-10)
        3. Overall satisfaction (1-5)
        4. Overall difficulty
        5. Post-workout notes
        """
        print("\n" + "="*60)
        print(" 🎉 WORKOUT COMPLETE - FINAL FEEDBACK")
        print("="*60)

        # 1. Post-workout feeling
        print("\n1. How do you feel NOW (after workout)?")
        feelings = {
            "1": PostWorkoutFeeling.ACCOMPLISHED,
            "2": PostWorkoutFeeling.ENERGIZED,
            "3": PostWorkoutFeeling.EXHAUSTED,
            "4": PostWorkoutFeeling.GREAT,
            "5": PostWorkoutFeeling.SATISFIED,
            "6": PostWorkoutFeeling.DISAPPOINTED,
            "7": PostWorkoutFeeling.SORE,
            "8": PostWorkoutFeeling.PUMPED
        }

        for key, feeling in feelings.items():
            print(f"   {key}. {feeling.value.replace('_', ' ').title()}")

        feeling_choice = input("   Your choice (1-8): ").strip()
        post_feeling = feelings.get(feeling_choice, PostWorkoutFeeling.SATISFIED)

        # 2. Post-workout energy
        print("\n2. Energy level NOW?")
        print("   1 = Exhausted ... 10 = Fully Energized")
        post_energy = int(input("   Your level (1-10): ").strip() or "5")
        post_energy = max(1, min(10, post_energy))

        # 3. Overall satisfaction
        print("\n3. Overall workout satisfaction?")
        print("   1 = Terrible ... 5 = Amazing")
        satisfaction = int(input("   Rating (1-5): ").strip() or "3")
        satisfaction = max(1, min(5, satisfaction))

        # 4. Overall difficulty
        print("\n4. Overall workout difficulty?")
        difficulties = {
            "1": ExerciseDifficulty.TOO_EASY,
            "2": ExerciseDifficulty.EASY,
            "3": ExerciseDifficulty.PERFECT,
            "4": ExerciseDifficulty.CHALLENGING,
            "5": ExerciseDifficulty.TOO_HARD
        }
        for key, diff in difficulties.items():
            print(f"   {key}. {diff.value.replace('_', ' ').title()}")

        diff_choice = input("   Your choice (1-5): ").strip()
        overall_difficulty = difficulties.get(diff_choice, ExerciseDifficulty.PERFECT)

        # 5. Post-workout notes
        print("\n5. Any final thoughts? (optional)")
        post_notes = input("   Notes: ").strip()

        # Complete session
        session.complete_workout(
            post_workout_feeling=post_feeling,
            post_workout_energy=post_energy,
            overall_satisfaction=satisfaction,
            overall_difficulty=overall_difficulty,
            post_workout_notes=post_notes
        )

        # Save to database
        session_id = self.manager.save_session(session)

        # Display summary
        print("\n" + "="*60)
        print(" 📊 WORKOUT SUMMARY")
        print("="*60)
        print(f"\n⏱️  Duration: {session.duration_minutes} minutes")
        print(f"⚡ Energy Change: {session.pre_workout_energy}/10 → {post_energy}/10")
        print(f"   (Delta: {post_energy - session.pre_workout_energy:+d})")
        print(f"\n⭐ Overall Satisfaction: {'⭐' * satisfaction}")
        print(f"💪 Difficulty: {overall_difficulty.value.title()}")
        print(f"🏋️  Exercises Logged: {len(session.exercise_feedback)}")

        # Show analytics
        analytics = session._compute_analytics()
        if analytics:
            print(f"\n📈 Session Analytics:")
            print(f"   • Avg Exercise Rating: {analytics['avg_exercise_rating']:.1f}⭐")

            if analytics.get('favorite_exercises'):
                print(f"   • Favorite Exercises: {', '.join(analytics['favorite_exercises'][:3])}")

            if analytics.get('difficult_exercises'):
                print(f"   • Challenging: {', '.join(analytics['difficult_exercises'][:3])}")

        print(f"\n✅ Session saved! ID: {session_id}")
        print("="*60)

        return session_id
