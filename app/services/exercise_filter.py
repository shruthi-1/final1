"""
Exercise filtering service with safety rules and cascade fallback.
"""
from typing import List, Dict, Any, Tuple
from app.core.constants import (
    BMI_SAFETY_BLACKLIST, INJURY_CONTRAINDICATIONS, 
    EQUIPMENT_HIERARCHY, GOAL_TAGS, RELATED_GOALS
)
import logging

logger = logging.getLogger(__name__)


class ExerciseFilter:
    """Handles exercise filtering with safety rules and fallback cascade."""

    def __init__(self, exercises_collection):
        self.exercises = exercises_collection

    def query_candidate_exercises(
        self, 
        equipment_list: List[str], 
        goal: str,
        body_part: str = None
    ) -> List[Dict[str, Any]]:
        """
        Query exercises from database matching equipment and goal.

        Args:
            equipment_list: List of available equipment
            goal: Primary fitness goal
            body_part: Optional body part filter

        Returns:
            List of candidate exercises
        """
        query = {"is_active": True}

        # Equipment filter: match provided equipment OR bodyweight
        if equipment_list:
            query["$or"] = [
                {"Equipment": {"$in": equipment_list}},
                {"is_bodyweight": True}
            ]
        else:
            query["is_bodyweight"] = True

        # Body part filter
        if body_part:
            query["BodyPart"] = body_part

        candidates = list(self.exercises.find(query).limit(1000))
        logger.info(f"Found {len(candidates)} candidate exercises")
        return candidates

    def filter_for_safety(
        self,
        candidates: List[Dict[str, Any]],
        bmi_category: str,
        injury_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter exercises for safety based on BMI and injuries.

        Args:
            candidates: List of candidate exercises
            bmi_category: User's BMI category
            injury_types: List of user injuries

        Returns:
            Filtered safe exercises
        """
        safe_exercises = []

        # Get blacklist for BMI category
        bmi_blacklist = BMI_SAFETY_BLACKLIST.get(bmi_category, [])

        for exercise in candidates:
            is_safe = True

            # Check BMI safety keywords
            title_lower = exercise.get("Title", "").lower()
            desc_lower = exercise.get("Desc", "").lower()

            for keyword in bmi_blacklist:
                if keyword in title_lower or keyword in desc_lower:
                    is_safe = False
                    break

            if not is_safe:
                continue

            # Check injury contraindications
            for injury in injury_types:
                injury_keywords = INJURY_CONTRAINDICATIONS.get(injury, [])
                for keyword in injury_keywords:
                    if keyword in title_lower or keyword in desc_lower:
                        is_safe = False
                        break
                if not is_safe:
                    break

            if is_safe:
                safe_exercises.append(exercise)

        logger.info(f"Filtered to {len(safe_exercises)} safe exercises")
        return safe_exercises

    def score_exercises(
        self,
        exercises: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        recent_exercises: List[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Score exercises based on goal relevance, difficulty match, and novelty.

        Args:
            exercises: List of exercises to score
            user_profile: User profile with goal, level, etc.
            recent_exercises: List of recently performed exercise IDs

        Returns:
            List of (exercise, score) tuples sorted by score descending
        """
        if recent_exercises is None:
            recent_exercises = []

        goal = user_profile.get("primary_goal", "general_fitness")
        fitness_level = user_profile.get("fitness_level", "Intermediate")
        equipment_list = user_profile.get("equipment_list", [])

        goal_keywords = GOAL_TAGS.get(goal, [])
        scored = []

        for exercise in exercises:
            score = 0.0

            # 1. Goal relevance (40%)
            title_lower = exercise.get("Title", "").lower()
            desc_lower = exercise.get("Desc", "").lower()
            type_lower = exercise.get("Type", "").lower()

            for keyword in goal_keywords:
                if keyword in title_lower or keyword in desc_lower or keyword in type_lower:
                    score += 0.4
                    break

            # 2. Difficulty match (20%)
            ex_level = exercise.get("Level", "Intermediate")
            if ex_level == fitness_level:
                score += 0.2
            elif abs(self._level_to_int(ex_level) - self._level_to_int(fitness_level)) == 1:
                score += 0.1

            # 3. Novelty (15%)
            ex_id = exercise.get("exercise_id_clean", "")
            if ex_id not in recent_exercises:
                score += 0.15

            # 4. Equipment fit (25%)
            ex_equipment = exercise.get("Equipment", "")
            if ex_equipment in equipment_list or ex_equipment == "Bodyweight":
                score += 0.25
            elif equipment_list and ex_equipment in EQUIPMENT_HIERARCHY.get(equipment_list[0], []):
                score += 0.1

            scored.append((exercise, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _level_to_int(self, level: str) -> int:
        """Convert fitness level string to integer."""
        mapping = {"Beginner": 1, "Intermediate": 3, "Expert": 5}
        return mapping.get(level, 3)

    def apply_cascade_fallback(
        self,
        user_profile: Dict[str, Any],
        body_part: str = None,
        min_exercises: int = 5
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Apply cascade fallback to find sufficient exercises.

        Level 1: Exact match (goal + equipment + level + safety)
        Level 2: Relax equipment
        Level 3: Relax difficulty ±1 level
        Level 4: Relax goal to related goals
        Level 5: Expand BMI safety slightly (if allowed)
        Level 6: Default to safe bodyweight exercises

        Args:
            user_profile: User profile dictionary
            body_part: Optional body part filter
            min_exercises: Minimum number of exercises needed

        Returns:
            Tuple of (exercises, fallback_level_used)
        """
        equipment_list = user_profile.get("equipment_list", [])
        goal = user_profile.get("primary_goal", "general_fitness")
        bmi_category = user_profile.get("bmi_category", "normal")
        injury_types = user_profile.get("injury_types", [])
        allow_relaxation = user_profile.get("allow_auto_relaxation", True)

        # Level 1: Exact match
        candidates = self.query_candidate_exercises(equipment_list, goal, body_part)
        safe = self.filter_for_safety(candidates, bmi_category, injury_types)

        if len(safe) >= min_exercises:
            return safe, "perfect_match"

        # Level 2: Relax equipment (add alternative equipment)
        logger.info("Fallback Level 2: Relaxing equipment constraints")
        expanded_equipment = equipment_list.copy()
        for eq in equipment_list:
            expanded_equipment.extend(EQUIPMENT_HIERARCHY.get(eq, []))

        candidates = self.query_candidate_exercises(list(set(expanded_equipment)), goal, body_part)
        safe = self.filter_for_safety(candidates, bmi_category, injury_types)

        if len(safe) >= min_exercises:
            return safe, "relax_equipment"

        # Level 3: Relax difficulty
        logger.info("Fallback Level 3: Relaxing difficulty constraints")
        candidates = self.query_candidate_exercises(list(set(expanded_equipment)), goal, body_part)
        safe = self.filter_for_safety(candidates, bmi_category, injury_types)

        if len(safe) >= min_exercises:
            return safe, "relax_difficulty"

        # Level 4: Relax goal to related goals
        logger.info("Fallback Level 4: Expanding to related goals")
        related_goals = RELATED_GOALS.get(goal, ["general_fitness"])
        all_goal_candidates = []

        for related_goal in related_goals:
            candidates = self.query_candidate_exercises(list(set(expanded_equipment)), related_goal, body_part)
            all_goal_candidates.extend(candidates)

        safe = self.filter_for_safety(all_goal_candidates, bmi_category, injury_types)

        if len(safe) >= min_exercises:
            return safe, "relax_goal"

        # Level 5: Expand BMI bounds slightly (if allowed)
        if allow_relaxation and bmi_category in BMI_SAFETY_BLACKLIST:
            logger.info("Fallback Level 5: Relaxing BMI safety bounds")
            # Use lighter BMI restrictions
            safe = all_goal_candidates[:min_exercises * 3]
            if len(safe) >= min_exercises:
                return safe, "relax_bmi_safety"

        # Level 6: Default to safe bodyweight exercises
        logger.warning("Fallback Level 6: Using default safe bodyweight exercises")
        query = {"is_bodyweight": True, "is_active": True}
        if body_part:
            query["BodyPart"] = body_part

        fallback_exercises = list(self.exercises.find(query).limit(min_exercises * 2))
        return fallback_exercises, "fallback_default"
