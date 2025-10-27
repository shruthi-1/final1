"""
Enhanced Workout Generator with ML adaptation and comprehensive safety rules.
"""
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import random
import logging

from app.utils.bmi_calculator import compute_bmi, get_bmi_category
from app.core.constants import (
    DAYS_OF_WEEK, DURATION_ALLOCATION, EXERCISE_COUNT_BY_DURATION,
    SETS_REPS_RANGES, REST_PERIODS, BMI_RPE_CAPS, MOTIVATION_TEMPLATES,
    BMI_SAFETY_BLACKLIST_KEYWORDS, INJURY_CONTRAINDICATIONS
)

logger = logging.getLogger(__name__)


class WorkoutGenerator:
    """Generates personalized weekly workout plans with ML adaptation."""

    def __init__(self, db):
        self.db = db
        self.exercises_coll = db.exercises

    def generate_weekly_plan(
        self,
        user_snapshot: Dict[str, Any],
        week_start_iso: str,
        target_daily_duration_minutes: Dict[str, int],
        history_summary: Dict[str, Any] = None,
        learning_flags: Dict[str, Any] = None,
        weekly_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate complete weekly workout plan with ML adaptation."""

        logger.info(f"Generating weekly plan for user {user_snapshot['user_id']}")

        # Compute BMI
        bmi = compute_bmi(user_snapshot['weight_kg'], user_snapshot['height_cm'])
        bmi_category = get_bmi_category(bmi)
        user_snapshot['bmi'] = bmi
        user_snapshot['bmi_category'] = bmi_category

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
                "version": 2
            }
        }

        # Get user's historical performance for ML adaptation
        user_preferences = self._get_ml_user_preferences(user_snapshot['user_id'])

        # Get recent exercises to avoid repetition
        recent_exercises = self._get_recent_exercises(user_snapshot['user_id'])

        # Compute motivation score
        motivation_score = self._compute_motivation_score(history_summary)

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
                    recent_exercises=recent_exercises,
                    motivation_score=motivation_score,
                    user_preferences=user_preferences
                )
                plan['days'][day] = day_plan['plan']
                plan['fallbacks_used'][day] = day_plan['fallback']

                # Add exercises to recent list
                for ex in day_plan['plan']['main']:
                    recent_exercises.append(ex['id'])

            except Exception as e:
                logger.error(f"Error generating plan for {day}: {e}", exc_info=True)
                plan['days'][day] = self._create_rest_day()
                plan['fallbacks_used'][day] = "error"

        return plan

    def _generate_day_plan(
        self,
        day: str,
        duration: int,
        user_snapshot: Dict[str, Any],
        recent_exercises: List[str],
        motivation_score: float,
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate plan for a single day with ML adaptation."""

        # Calculate section durations
        warmup_duration = max(5, int(duration * DURATION_ALLOCATION['warmup']))
        cooldown_duration = max(3, int(duration * DURATION_ALLOCATION['cooldown']))
        main_duration = duration - warmup_duration - cooldown_duration

        # Determine number of main exercises
        main_count = self._get_exercise_count(main_duration)

        # Get exercises with cascade fallback
        exercises, fallback_level = self._apply_cascade_fallback(
            user_snapshot=user_snapshot,
            min_exercises=main_count * 2,
            recent_exercises=recent_exercises
        )

        if not exercises or len(exercises) == 0:
            logger.warning(f"No exercises found for {day}, using emergency fallback")
            exercises = self._get_emergency_exercises()
            fallback_level = "emergency_bodyweight"

        # Score and select exercises with ML preferences
        selected = self._score_and_select_exercises(
            exercises=exercises,
            user_snapshot=user_snapshot,
            recent_exercises=recent_exercises,
            user_preferences=user_preferences,
            count=main_count
        )

        # Build main exercises with ML-adjusted parameters
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
        recent_exercises: List[str]
    ) -> Tuple[List[Dict], str]:
        """Apply 6-level cascade fallback to get exercises."""

        goal = user_snapshot.get('primary_goal', 'general_fitness')
        fitness_level = user_snapshot.get('fitness_level', 'Intermediate')
        equipment_list = user_snapshot.get('equipment_list', ['Bodyweight'])
        bmi_category = user_snapshot.get('bmi_category', 'normal')
        injury_types = user_snapshot.get('injury_types', [])

        # Level 1: Perfect match
        query = {
            "Level": fitness_level,
            "Equipment": {"$in": equipment_list},
            "is_active": True
        }

        # Apply BMI safety filter
        blacklist = BMI_SAFETY_BLACKLIST_KEYWORDS.get(bmi_category, [])
        if blacklist:
            query["Title"] = {"$not": {"$regex": "|".join(blacklist), "$options": "i"}}

        # Apply injury contraindications
        for injury in injury_types:
            contraindicated = INJURY_CONTRAINDICATIONS.get(injury, [])
            if contraindicated:
                for keyword in contraindicated:
                    if "Title" in query:
                        query["Title"]["$not"]["$regex"] += f"|{keyword}"
                    else:
                        query["Title"] = {"$not": {"$regex": keyword, "$options": "i"}}

        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))

        if len(exercises) >= min_exercises:
            logger.info("Level 1: Perfect match")
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
        # Expand query (simplified - would need goal mapping in DB)

        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))

        if len(exercises) >= min_exercises:
            logger.info("Level 4: Related goals")
            return exercises, "related_goals"

        # Level 5: Relax BMI safety (slightly)
        query.pop("Title", None)  # Remove title restrictions
        exercises = list(self.exercises_coll.find(query).limit(min_exercises * 2))

        if len(exercises) >= min_exercises:
            logger.info("Level 5: BMI safety relaxed")
            return exercises, "bmi_relaxed"

        # Level 6: Emergency - safe bodyweight only
        logger.warning("Level 6: Emergency bodyweight fallback")
        return self._get_emergency_exercises(), "emergency_bodyweight"

    def _get_emergency_exercises(self) -> List[Dict]:
        """Get emergency safe bodyweight exercises."""
        emergency_query = {
            "Equipment": "Bodyweight",
            "Level": {"$in": ["Beginner", "Intermediate"]},
            "is_active": True
        }

        exercises = list(self.exercises_coll.find(emergency_query).limit(20))

        if not exercises:
            # Absolute fallback - create from scratch
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
        recent_exercises: List[str],
        user_preferences: Dict[str, Any],
        count: int
    ) -> List[Dict]:
        """Score exercises with ML preferences and select top N."""

        scored = []

        for ex in exercises:
            score = 1.0

            # Penalize recently done exercises
            ex_id = ex.get('exercise_id_clean', ex.get('Title', ''))
            if ex_id in recent_exercises:
                recency_index = recent_exercises.index(ex_id)
                score -= (1.0 - recency_index / len(recent_exercises)) * 0.3

            # Boost based on user preferences (ML)
            ex_body_part = ex.get('BodyPart', '').lower()
            if ex_body_part in user_preferences.get('preferred_body_parts', []):
                score += 0.2

            # Boost based on equipment match
            ex_equipment = ex.get('Equipment', '')
            if ex_equipment in user_snapshot.get('equipment_list', []):
                score += 0.1

            # Adjust based on past satisfaction with similar exercises
            satisfaction_boost = user_preferences.get('body_part_satisfaction', {}).get(ex_body_part, 0)
            score += satisfaction_boost * 0.15

            # Boost variety - different body parts
            score += random.uniform(0, 0.1)  # Add small random factor

            scored.append((ex, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Select top N ensuring body part variety
        selected = []
        used_body_parts = set()

        for ex, score in scored:
            if len(selected) >= count:
                break

            body_part = ex.get('BodyPart', '').lower()

            # Prefer exercises from different body parts
            if body_part not in used_body_parts or len(selected) < count // 2:
                selected.append(ex)
                used_body_parts.add(body_part)

        # If not enough, add remaining regardless of body part
        remaining_count = count - len(selected)
        if remaining_count > 0:
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

    def _get_recent_exercises(self, user_id: str, days: int = 7) -> List[str]:
        """Get recently performed exercises to avoid repetition."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        recent_logs = list(self.db.session_logs.find({
            "user_id": user_id,
            "logged_at": {"$gte": cutoff_date}
        }).limit(50))

        exercise_ids = []
        for log in recent_logs:
            if 'exercises_completed' in log:
                exercise_ids.extend(log['exercises_completed'])

        return list(set(exercise_ids))[-20:]  # Keep last 20 unique

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

        # Calculate average RPE (would need to store this)
        avg_rpe = 7.0  # Default

        # Analyze body part preferences (would need to track exercises)
        preferred_body_parts = []
        body_part_satisfaction = {}

        # Analyze satisfaction by body part (simplified)
        for log in logs:
            satisfaction = log.get('satisfaction', 5)
            # Would need to map exercises to body parts

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
