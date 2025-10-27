"""
Enhanced Workout Generator with Anti-Repetition System
Tracks exercise history and stores all generated workouts in separate MongoDB database
Ready for deployment as microservices
Combines WorkoutHistoryManager with complete WorkoutGenerator functionality
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import random
import logging
import hashlib
from app.utils.bmi_calculator import compute_bmi, get_bmi_category
from app.core.constants import (
    DAYS_OF_WEEK, DURATION_ALLOCATION, EXERCISE_COUNT_BY_DURATION,
    SETS_REPS_RANGES, REST_PERIODS, BMI_RPE_CAPS, MOTIVATION_TEMPLATES,
    BMI_SAFETY_BLACKLIST_KEYWORDS, INJURY_CONTRAINDICATIONS
)

logger = logging.getLogger(__name__)

class WorkoutHistoryManager:
    """Manages workout history in separate database to prevent exercise repetition."""

    def __init__(self, workout_history_db):
        """
        Args:
            workout_history_db: MongoDB database instance for workout history
                               (separate from main nutrix database)
        """
        self.db = workout_history_db
        self.workouts_coll = self.db.generated_workouts
        self.exercise_history_coll = self.db.exercise_history
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for workout history collections."""
        try:
            # Compound index for efficient user + date queries
            self.workouts_coll.create_index([
                ("user_id", 1),
                ("generated_at", -1)
            ])

            # Index for workout hash (deduplication)
            self.workouts_coll.create_index([("workout_hash", 1)])

            # Exercise history indexes
            self.exercise_history_coll.create_index([
                ("user_id", 1),
                ("exercise_id", 1),
                ("last_used", -1)
            ])

            logger.info("Workout history indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating workout history indexes: {e}")

    def get_recent_exercise_ids(self, user_id: str, days: int = 14) -> List[Dict]:
        """
        Get exercise IDs used by user in last N days.

        Args:
            user_id: User identifier
            days: Number of days to look back (default 14 for 2 weeks)

        Returns:
            List of exercise data with recency weighting (most recent first)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get exercise history
        history = list(self.exercise_history_coll.find({
            "user_id": user_id,
            "last_used": {"$gte": cutoff_date}
        }).sort("last_used", -1).limit(100))

        # Extract IDs with recency information
        exercise_data = []
        for i, record in enumerate(history):
            exercise_data.append({
                "id": record["exercise_id"],
                "recency_score": 1.0 - (i / len(history)) if history else 0,
                "use_count": record.get("use_count", 1),
                "last_used": record["last_used"]
            })

        return exercise_data

    def save_generated_workout(
        self,
        user_id: str,
        workout_plan: Dict[str, Any],
        week_start_iso: str
    ) -> str:
        """
        Save generated workout to history database.

        Args:
            user_id: User identifier
            workout_plan: Complete workout plan dict
            week_start_iso: Week start date in ISO format

        Returns:
            Workout document ID
        """
        # Extract all exercise IDs from the plan
        exercise_ids = self._extract_exercise_ids(workout_plan)

        # Create workout hash for deduplication
        workout_hash = self._compute_workout_hash(exercise_ids)

        # Create workout record
        workout_record = {
            "user_id": user_id,
            "week_start_iso": week_start_iso,
            "generated_at": datetime.utcnow(),
            "workout_hash": workout_hash,
            "exercise_ids": exercise_ids,
            "workout_plan": workout_plan,
            "plan_metadata": {
                "total_exercises": len(exercise_ids),
                "fallbacks_used": workout_plan.get("fallbacks_used", {}),
                "bmi_category": workout_plan.get("bmi_category"),
                "version": workout_plan.get("weekly_metadata", {}).get("version", 3)
            }
        }

        # Save workout
        result = self.workouts_coll.insert_one(workout_record)

        # Update exercise history for each exercise
        self._update_exercise_history(user_id, exercise_ids)

        logger.info(f"Saved workout for user {user_id}, week {week_start_iso}: {result.inserted_id}")
        return str(result.inserted_id)

    def _extract_exercise_ids(self, workout_plan: Dict[str, Any]) -> List[str]:
        """Extract all exercise IDs from workout plan."""
        exercise_ids = []

        for day_name, day_plan in workout_plan.get("days", {}).items():
            # Main exercises
            for exercise in day_plan.get("main", []):
                ex_id = exercise.get("id")
                if ex_id and ex_id not in ["warmup_mobility", "warmup_cardio", "cooldown_stretch"]:
                    exercise_ids.append(ex_id)

        return exercise_ids

    def _compute_workout_hash(self, exercise_ids: List[str]) -> str:
        """Compute hash of workout for deduplication."""
        sorted_ids = sorted(exercise_ids)
        hash_input = "|".join(sorted_ids)
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _update_exercise_history(self, user_id: str, exercise_ids: List[str]):
        """Update exercise usage history."""
        now = datetime.utcnow()

        for exercise_id in exercise_ids:
            self.exercise_history_coll.update_one(
                {
                    "user_id": user_id,
                    "exercise_id": exercise_id
                },
                {
                    "$set": {"last_used": now},
                    "$inc": {"use_count": 1},
                    "$setOnInsert": {"first_used": now}
                },
                upsert=True
            )

    def check_workout_similarity(self, user_id: str, exercise_ids: List[str], threshold: float = 0.7) -> bool:
        """
        Check if proposed workout is too similar to recent workouts.

        Args:
            user_id: User identifier
            exercise_ids: Proposed exercise IDs
            threshold: Similarity threshold (0-1, default 0.7 = 70% overlap)

        Returns:
            True if workout is too similar (should regenerate)
        """
        # Get last 3 workouts
        recent_workouts = list(self.workouts_coll.find({
            "user_id": user_id
        }).sort("generated_at", -1).limit(3))

        if not recent_workouts:
            return False  # No history, not similar

        proposed_set = set(exercise_ids)

        for workout in recent_workouts:
            existing_set = set(workout.get("exercise_ids", []))

            if not existing_set:
                continue

            # Calculate Jaccard similarity
            intersection = len(proposed_set & existing_set)
            union = len(proposed_set | existing_set)

            similarity = intersection / union if union > 0 else 0

            if similarity >= threshold:
                logger.warning(f"Workout too similar ({similarity:.2%}) to recent workout")
                return True

        return False


class WorkoutGenerator:
    """Generates personalized weekly workout plans with anti-repetition system and ML adaptation."""

    def __init__(self, db, workout_history_db):
        """
        Args:
            db: Main nutrix database (users, exercises, etc.)
            workout_history_db: Separate database for workout history
        """
        self.db = db
        self.exercises_coll = db.exercises
        self.history_manager = WorkoutHistoryManager(workout_history_db)

    def generate_weekly_plan(
        self,
        user_snapshot: Dict[str, Any],
        week_start_iso: str,
        target_daily_duration_minutes: Dict[str, int],
        history_summary: Dict[str, Any] = None,
        learning_flags: Dict[str, Any] = None,
        weekly_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate complete weekly workout plan with anti-repetition and ML adaptation."""
        logger.info(f"Generating weekly plan for user {user_snapshot['user_id']}")

        # Compute BMI
        bmi = compute_bmi(user_snapshot['weight_kg'], user_snapshot['height_cm'])
        bmi_category = get_bmi_category(bmi)
        user_snapshot['bmi'] = bmi
        user_snapshot['bmi_category'] = bmi_category

        # Get recent exercise history (14 days) - ANTI-REPETITION
        recent_exercise_data = self.history_manager.get_recent_exercise_ids(
            user_snapshot['user_id'],
            days=14
        )

        # Extract just IDs and recency scores
        recent_exercise_ids = [ex["id"] for ex in recent_exercise_data]
        recency_map = {ex["id"]: ex["recency_score"] for ex in recent_exercise_data}

        logger.info(f"Found {len(recent_exercise_ids)} recent exercises for user {user_snapshot['user_id']}")

        # Initialize plan
        plan = {
            "user_id": user_snapshot['user_id'],
            "week_start_iso": week_start_iso,
            "generated_at_iso": datetime.utcnow().isoformat() + "Z",
            "bmi": bmi,
            "bmi_category": bmi_category,
            "user_snapshot": user_snapshot,
            "fallbacks_used": {},
            "days": {},
            "weekly_metadata": {
                "split_applied": "auto",
                "ml_adjustments_applied": True,
                "anti_repetition_enabled": True,
                "recent_exercises_excluded": len(recent_exercise_ids),
                "version": 3
            }
        }

        # Get user's ML preferences
        user_preferences = self._get_ml_user_preferences(user_snapshot['user_id'])

        # Compute motivation score
        motivation_score = self._compute_motivation_score(history_summary)

        # Track exercises used this week to avoid within-week repetition
        week_exercise_ids = []

        # Generate each day
        for day in DAYS_OF_WEEK:
            duration = target_daily_duration_minutes.get(day, 0)
            if duration == 0:
                plan['days'][day] = self._create_rest_day()
                plan['fallbacks_used'][day] = "rest"
                continue

            try:
                day_plan = self._generate_day_plan(
                    day=day,
                    duration=duration,
                    user_snapshot=user_snapshot,
                    recent_exercise_ids=recent_exercise_ids,
                    week_exercise_ids=week_exercise_ids,
                    recency_map=recency_map,
                    motivation_score=motivation_score,
                    user_preferences=user_preferences
                )

                plan['days'][day] = day_plan['plan']
                plan['fallbacks_used'][day] = day_plan['fallback']

                # Add exercises to week tracking
                for ex in day_plan['plan']['main']:
                    ex_id = ex['id']
                    week_exercise_ids.append(ex_id)

            except Exception as e:
                logger.error(f"Error generating plan for {day}: {e}", exc_info=True)
                plan['days'][day] = self._create_rest_day()
                plan['fallbacks_used'][day] = "error"

        # Save generated workout to history database
        try:
            workout_id = self.history_manager.save_generated_workout(
                user_id=user_snapshot['user_id'],
                workout_plan=plan,
                week_start_iso=week_start_iso
            )
            plan['weekly_metadata']['workout_history_id'] = workout_id
        except Exception as e:
            logger.error(f"Error saving workout to history: {e}")

        return plan

    def _generate_day_plan(
        self,
        day: str,
        duration: int,
        user_snapshot: Dict[str, Any],
        recent_exercise_ids: List[str],
        week_exercise_ids: List[str],
        recency_map: Dict[str, float],
        motivation_score: float,
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate plan for a single day with anti-repetition."""

        # Calculate section durations
        warmup_duration = max(5, int(duration * DURATION_ALLOCATION['warmup']))
        cooldown_duration = max(3, int(duration * DURATION_ALLOCATION['cooldown']))
        main_duration = duration - warmup_duration - cooldown_duration

        # Determine number of main exercises
        main_count = self._get_exercise_count(main_duration)

        # Combine recent and week exercises for exclusion
        all_excluded_ids = recent_exercise_ids + week_exercise_ids

        # Get exercises with cascade fallback
        exercises, fallback_level = self._apply_cascade_fallback(
            user_snapshot=user_snapshot,
            min_exercises=main_count * 3,  # Get more candidates for better selection
            excluded_exercise_ids=all_excluded_ids
        )

        if not exercises or len(exercises) == 0:
            logger.warning(f"No exercises found for {day}, using emergency fallback")
            exercises = self._get_emergency_exercises(all_excluded_ids)
            fallback_level = "emergency_bodyweight"

        # Score and select exercises with heavy anti-repetition penalty
        selected = self._score_and_select_exercises(
            exercises=exercises,
            user_snapshot=user_snapshot,
            excluded_ids=all_excluded_ids,
            recency_map=recency_map,
            user_preferences=user_preferences,
            count=main_count
        )

        # Build main exercises
        main_exercises = []
        for exercise in selected:
            ex_detail = self._build_exercise_detail(
                exercise=exercise,
                user_snapshot=user_snapshot,
                user_preferences=user_preferences
            )
            main_exercises.append(ex_detail)

        # Build warmup and cooldown
        warmup = self._build_warmup(warmup_duration)
        cooldown = self._build_cooldown(cooldown_duration)

        # Generate motivation message
        motivation = self._get_motivation_message(motivation_score)

        return {
            "plan": {
                "target_duration": duration,
                "warmup": warmup,
                "main": main_exercises,
                "cooldown": cooldown,
                "motivation": motivation,
                "placeholders": {
                    "actual_duration": None,
                    "completion_percent": None,
                    "satisfaction": None,
                    "activity_override_type": None
                }
            },
            "fallback": fallback_level
        }

    def _apply_cascade_fallback(
        self,
        user_snapshot: Dict[str, Any],
        min_exercises: int,
        excluded_exercise_ids: List[str]
    ) -> Tuple[List[Dict], str]:
        """Apply 6-level cascade fallback with exercise exclusion."""

        goal = user_snapshot.get('primary_goal', 'general_fitness')
        fitness_level = user_snapshot.get('fitness_level', 'Intermediate')
        equipment_list = user_snapshot.get('equipment_list', ['Bodyweight'])
        bmi_category = user_snapshot.get('bmi_category', 'normal')
        injury_types = user_snapshot.get('injury_types', [])

        # Base exclusion query for anti-repetition
        exclusion_query = {}
        if excluded_exercise_ids:
            exclusion_query = {
                "exercise_id_clean": {"$nin": excluded_exercise_ids},
                "Title": {"$nin": excluded_exercise_ids}
            }

        # Level 1: Perfect match
        query = {
            **exclusion_query,
            "Level": fitness_level,
            "Equipment": {"$in": equipment_list},
            "is_active": True
        }

        # Apply BMI safety filter
        blacklist = BMI_SAFETY_BLACKLIST_KEYWORDS.get(bmi_category, [])
        if blacklist:
            title_regex = "|".join(blacklist)
            if "Title" in query:
                if "$not" in query["Title"]:
                    query["Title"]["$not"]["$regex"] += f"|{title_regex}"
                else:
                    query["Title"]["$not"] = {"$regex": title_regex, "$options": "i"}
            else:
                query["Title"] = {"$not": {"$regex": title_regex, "$options": "i"}}

        # Apply injury contraindications
        for injury in injury_types:
            contraindicated = INJURY_CONTRAINDICATIONS.get(injury, [])
            for keyword in contraindicated:
                if "Title" in query and "$not" in query["Title"]:
                    query["Title"]["$not"]["$regex"] += f"|{keyword}"
                else:
                    query["Title"] = {"$not": {"$regex": keyword, "$options": "i"}}

        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))
        if len(exercises) >= min_exercises:
            logger.info(f"Level 1: Perfect match ({len(exercises)} exercises found)")
            return exercises, "perfect"

        # Level 2: Relax equipment
        query["Equipment"] = {"$in": equipment_list + ["Bodyweight", "Dumbbell"]}
        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))
        if len(exercises) >= min_exercises:
            logger.info("Level 2: Relaxed equipment")
            return exercises, "equipment_relaxed"

        # Level 3: Relax difficulty
        level_map = {"Beginner": 1, "Intermediate": 2, "Expert": 3}
        user_level_num = level_map.get(fitness_level, 2)
        adjacent_levels = []
        for level_name, level_num in level_map.items():
            if abs(level_num - user_level_num) <= 1:
                adjacent_levels.append(level_name)

        query["Level"] = {"$in": adjacent_levels}
        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))
        if len(exercises) >= min_exercises:
            logger.info("Level 3: Relaxed difficulty")
            return exercises, "difficulty_relaxed"

        # Level 4: Related goals
        goal_groups = {
            "weight_loss": ["endurance", "general_fitness"],
            "muscle_gain": ["strength", "athletic"],
            "strength": ["muscle_gain", "athletic"],
            "endurance": ["weight_loss", "general_fitness"],
            "general_fitness": ["weight_loss", "endurance"],
            "athletic": ["strength", "muscle_gain"]
        }

        related_goals = goal_groups.get(goal, [])
        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))
        if len(exercises) >= min_exercises:
            logger.info("Level 4: Related goals")
            return exercises, "related_goals"

        # Level 5: Relax BMI safety (slightly)
        query.pop("Title", None)
        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))
        if len(exercises) >= min_exercises:
            logger.info("Level 5: BMI safety relaxed")
            return exercises, "bmi_relaxed"

        # Level 6: Emergency fallback
        logger.warning("Level 6: Emergency bodyweight fallback")
        return self._get_emergency_exercises(excluded_exercise_ids), "emergency_bodyweight"

    def _get_emergency_exercises(self, excluded_ids: List[str] = None) -> List[Dict]:
        """Get emergency safe bodyweight exercises."""
        query = {
            "Equipment": "Bodyweight",
            "Level": {"$in": ["Beginner", "Intermediate"]},
            "is_active": True
        }

        if excluded_ids:
            query["exercise_id_clean"] = {"$nin": excluded_ids}
            query["Title"] = {"$nin": excluded_ids}

        exercises = list(self.exercises_coll.find(query).limit(20))

        if not exercises:
            logger.error("No exercises in database! Using hardcoded fallback")
            return self._get_hardcoded_fallback()

        return exercises

    def _get_hardcoded_fallback(self) -> List[Dict]:
        """Hardcoded exercises as absolute last resort."""
        return [
            {"Title": "Push-ups", "BodyPart": "Chest", "Equipment": "Bodyweight", "Level": "Beginner", "exercise_id_clean": "pushups"},
            {"Title": "Bodyweight Squats", "BodyPart": "Legs", "Equipment": "Bodyweight", "Level": "Beginner", "exercise_id_clean": "squats"},
            {"Title": "Plank", "BodyPart": "Core", "Equipment": "Bodyweight", "Level": "Beginner", "exercise_id_clean": "plank"},
            {"Title": "Lunges", "BodyPart": "Legs", "Equipment": "Bodyweight", "Level": "Beginner", "exercise_id_clean": "lunges"},
            {"Title": "Mountain Climbers", "BodyPart": "Core", "Equipment": "Bodyweight", "Level": "Intermediate", "exercise_id_clean": "mountain-climbers"},
        ]

    def _score_and_select_exercises(
        self,
        exercises: List[Dict],
        user_snapshot: Dict[str, Any],
        excluded_ids: List[str],
        recency_map: Dict[str, float],
        user_preferences: Dict[str, Any],
        count: int
    ) -> List[Dict]:
        """Score exercises with HEAVY anti-repetition penalty and ML preferences."""
        scored = []

        for ex in exercises:
            score = 1.0
            ex_id = ex.get('exercise_id_clean', ex.get('Title', '').lower().replace(' ', '-'))

            # HEAVY penalty for recent exercises (ANTI-REPETITION)
            if ex_id in recency_map:
                recency_score = recency_map[ex_id]
                # Exponential penalty: recently used exercises get heavy penalty
                penalty = recency_score ** 2  # Square for stronger effect
                score -= penalty * 0.8  # Up to 80% penalty for most recent
                logger.debug(f"Exercise {ex_id}: recency penalty {penalty:.2f}")

            # Boost based on user preferences (ML)
            ex_body_part = ex.get('BodyPart', '').lower()
            if ex_body_part in user_preferences.get('preferred_body_parts', []):
                score += 0.2

            # Equipment match boost
            ex_equipment = ex.get('Equipment', '')
            if ex_equipment in user_snapshot.get('equipment_list', []):
                score += 0.15

            # User satisfaction boost
            satisfaction_boost = user_preferences.get('body_part_satisfaction', {}).get(ex_body_part, 0)
            score += satisfaction_boost * 0.1

            # Small random factor for variety
            score += random.uniform(0, 0.05)

            scored.append((ex, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Select top N ensuring body part variety
        selected = []
        used_body_parts = {}  # Track frequency

        for ex, score in scored:
            if len(selected) >= count:
                break

            body_part = ex.get('BodyPart', '').lower()

            # Limit same body part to max 2 exercises
            bp_count = used_body_parts.get(body_part, 0)
            if bp_count < 2:
                selected.append(ex)
                used_body_parts[body_part] = bp_count + 1

        # If not enough, relax body part constraint
        if len(selected) < count:
            for ex, score in scored:
                if ex not in selected:
                    selected.append(ex)
                    if len(selected) >= count:
                        break

        return selected

    def _build_exercise_detail(
        self,
        exercise: Dict[str, Any],
        user_snapshot: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build detailed exercise with ML-adjusted parameters."""
        fitness_level = user_snapshot.get('fitness_level', 'Intermediate')
        goal = user_snapshot.get('primary_goal', 'general_fitness')
        bmi_category = user_snapshot.get('bmi_category', 'normal')

        # Get base sets/reps range
        ranges = SETS_REPS_RANGES.get(fitness_level, {}).get(goal, {"sets": (3, 4), "reps": (10, 12)})

        # ML Adjustment: Adapt based on user's historical completion rates
        completion_rate = user_preferences.get('avg_completion_rate', 0.8)

        # If user struggles to complete, reduce volume
        if completion_rate < 0.7:
            ranges = {"sets": (ranges['sets'][0], ranges['sets'][1] - 1), "reps": ranges['reps']}
        # If user consistently completes, can increase slightly
        elif completion_rate > 0.95:
            ranges = {"sets": (ranges['sets'][0], min(6, ranges['sets'][1] + 1)), "reps": ranges['reps']}

        sets = random.randint(*ranges['sets'])
        reps = random.randint(*ranges['reps'])

        # Determine rest period
        rest_category = "hypertrophy" if goal == "muscle_gain" else "strength" if goal == "strength" else "endurance"
        rest_seconds = REST_PERIODS.get(fitness_level, {}).get(rest_category, 60)

        # ML Adjustment: Adjust rest based on RPE feedback
        avg_rpe = user_preferences.get('avg_rpe', 7)
        if avg_rpe > 8.5:  # User consistently rates high RPE
            rest_seconds += 15  # Give more rest
        elif avg_rpe < 6:  # User rates low RPE
            rest_seconds = max(30, rest_seconds - 15)  # Can reduce rest

        # Determine RPE range with BMI cap
        base_rpe_min = 6
        base_rpe_max = 9
        rpe_cap = BMI_RPE_CAPS.get(bmi_category, 10)
        rpe_max = min(base_rpe_max, rpe_cap)

        # Extract tags
        tags = []
        if exercise.get('movement_pattern'):
            tags.append(exercise['movement_pattern'])
        if exercise.get('Type'):
            tags.append(exercise['Type'].lower())

        return {
            "id": exercise.get('exercise_id_clean', exercise.get('Title', '').lower().replace(' ', '-')),
            "name": exercise.get('Title', 'Unknown Exercise'),
            "body_part": exercise.get('BodyPart', ''),
            "equipment_required": exercise.get('Equipment', 'Bodyweight'),
            "sets": sets,
            "reps": reps,
            "duration_secs": None,
            "rest_seconds": rest_seconds,
            "predicted_rpe_range": [base_rpe_min, rpe_max],
            "notes": self._generate_exercise_notes(exercise, user_snapshot),
            "tags": tags
        }

    def _generate_exercise_notes(self, exercise: Dict[str, Any], user_snapshot: Dict[str, Any]) -> str:
        """Generate safety/form notes with injury considerations."""
        notes = []
        injury_types = user_snapshot.get('injury_types', [])
        title_lower = exercise.get('Title', '').lower()

        # Injury-specific notes
        if 'knee' in injury_types and any(word in title_lower for word in ['squat', 'lunge', 'jump']):
            notes.append("Keep knees tracking over toes. Stop if pain occurs.")

        if 'lower_back' in injury_types and any(word in title_lower for word in ['deadlift', 'row', 'squat']):
            notes.append("Maintain neutral spine. Engage core. Consider substituting if pain.")

        if 'shoulder' in injury_types and any(word in title_lower for word in ['press', 'overhead', 'raise']):
            notes.append("Reduce range of motion if discomfort. Use lighter weight.")

        if 'wrist' in injury_types and any(word in title_lower for word in ['push', 'plank', 'press']):
            notes.append("Use wrist wraps or modify hand position.")

        # General form cues
        if not notes:
            notes.append("Focus on controlled movement and proper form.")

        return " ".join(notes)

    def _build_warmup(self, duration: int) -> List[Dict[str, Any]]:
        """Build warmup sequence."""
        warmup_duration_mins = duration // 60

        return [
            {
                "id": "warmup_mobility",
                "name": "Joint Mobility Flow",
                "body_part": "Full Body",
                "equipment_required": "Bodyweight",
                "sets": None,
                "reps": None,
                "duration_secs": min(120, duration // 2),
                "rest_seconds": 0,
                "predicted_rpe_range": [2, 3],
                "notes": "Neck rolls, arm circles, hip circles, leg swings",
                "tags": ["warmup", "mobility"]
            },
            {
                "id": "warmup_cardio",
                "name": "Light Cardio",
                "body_part": "Full Body",
                "equipment_required": "Bodyweight",
                "sets": None,
                "reps": None,
                "duration_secs": max(180, duration - 120),
                "rest_seconds": 0,
                "predicted_rpe_range": [3, 4],
                "notes": "Marching in place, jumping jacks, or light jogging",
                "tags": ["warmup", "cardio"]
            }
        ]

    def _build_cooldown(self, duration: int) -> List[Dict[str, Any]]:
        """Build cooldown sequence."""
        return [
            {
                "id": "cooldown_stretch",
                "name": "Full Body Stretch",
                "body_part": "Full Body",
                "equipment_required": "Bodyweight",
                "sets": None,
                "reps": None,
                "duration_secs": duration,
                "rest_seconds": 0,
                "predicted_rpe_range": [1, 2],
                "notes": "Hold each stretch 20-30 seconds. Focus on worked muscle groups.",
                "tags": ["cooldown", "flexibility"]
            }
        ]

    def _create_rest_day(self) -> Dict[str, Any]:
        """Create rest day plan."""
        return {
            "target_duration": 0,
            "warmup": [],
            "main": [],
            "cooldown": [],
            "motivation": "Rest and recovery day. Your body grows stronger during rest.",
            "placeholders": {
                "actual_duration": None,
                "completion_percent": None,
                "satisfaction": None,
                "activity_override_type": None
            }
        }

    def _get_exercise_count(self, duration: int) -> int:
        """Determine number of exercises based on duration."""
        for (min_dur, max_dur), count in EXERCISE_COUNT_BY_DURATION.items():
            if min_dur <= duration < max_dur:
                return count
        return 5

    def _get_ml_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get ML-learned user preferences from historical data."""
        # Get session logs
        logs = list(self.db.session_logs.find({
            "user_id": user_id
        }).sort("logged_at", -1).limit(30))

        if not logs:
            return {
                "avg_completion_rate": 0.8,
                "avg_rpe": 7.0,
                "preferred_body_parts": [],
                "body_part_satisfaction": {}
            }

        # Calculate completion rate
        completions = [log.get('completion_percent', 0.8) for log in logs]
        avg_completion = sum(completions) / len(completions) if completions else 0.8

        # Calculate average RPE
        avg_rpe = 7.0  # Default

        # Analyze body part preferences
        preferred_body_parts = []
        body_part_satisfaction = {}

        return {
            "avg_completion_rate": avg_completion,
            "avg_rpe": avg_rpe,
            "preferred_body_parts": preferred_body_parts,
            "body_part_satisfaction": body_part_satisfaction
        }

    def _compute_motivation_score(self, history_summary: Dict[str, Any] = None) -> float:
        """Compute motivation score from history."""
        if not history_summary:
            return 0.0

        completion = history_summary.get('last_7_completions', 0.5)
        satisfaction = history_summary.get('avg_satisfaction_7d', 5.0)

        # Normalize satisfaction to -1 to 1
        satisfaction_norm = (satisfaction - 5) / 5

        # Combine metrics
        motivation = (completion * 0.6) + (satisfaction_norm * 0.4)
        return max(-1.0, min(1.0, motivation))

    def _get_motivation_message(self, motivation_score: float) -> str:
        """Get motivational message based on score."""
        if motivation_score > 0.3:
            category = "high"
        elif motivation_score < -0.3:
            category = "low"
        else:
            category = "neutral"

        messages = MOTIVATION_TEMPLATES.get(category, MOTIVATION_TEMPLATES.get("neutral", [
            "Solid work — aim for crisp reps; you're one step closer."
        ]))

        return random.choice(messages)
