"""
Application-wide constants for BMI safety rules and exercise parameters.
Comprehensive rules for workout generation with ML adaptation.
"""

# ============================================================
# BMI CATEGORIES & SAFETY
# ============================================================

# BMI Category thresholds
BMI_CATEGORIES = {
    "severe_underweight": (0, 16),
    "moderate_underweight": (16, 17),
    "mild_underweight": (17, 18.5),
    "normal": (18.5, 25),
    "overweight": (25, 30),
    "obese": (30, 35),
    "severe_obese": (35, 100)
}

# Safety rules: keywords to exclude per BMI category
BMI_SAFETY_BLACKLIST_KEYWORDS = {
    "severe_obese": [
        "jump", "jumping", "sprint", "sprinting", "burpee", "box jump", 
        "box-jump", "plyometric", "high-impact", "running", "hiit"
    ],
    "obese": [
        "jump", "jumping", "sprint", "sprinting", "burpee", "box jump",
        "box-jump", "plyometric", "high-impact", "running"
    ],
    "severe_underweight": [
        "heavy lifting", "max strength", "powerlifting", "1rm", "one-rep max"
    ],
    "moderate_underweight": [
        "heavy lifting", "max strength", "powerlifting", "1rm"
    ]
}

# Legacy name for compatibility
BMI_SAFETY_BLACKLIST = BMI_SAFETY_BLACKLIST_KEYWORDS

# Max RPE caps per BMI category
BMI_RPE_CAPS = {
    "severe_obese": 7,
    "obese": 8,
    "overweight": 9,
    "normal": 10,
    "mild_underweight": 9,
    "moderate_underweight": 8,
    "severe_underweight": 7
}

# ============================================================
# INJURY CONTRAINDICATIONS
# ============================================================

# Injury contraindication mapping
INJURY_CONTRAINDICATIONS = {
    "lower_back": ["deadlift", "good morning", "goodmorning", "hyperextension", "heavy squat", "back extension"],
    "knee": ["deep squat", "lunge", "leg press", "running", "jump", "pistol", "bulgarian"],
    "shoulder": ["overhead press", "military press", "handstand", "dip", "snatch", "jerk", "upright row"],
    "wrist": ["push-up", "pushup", "plank", "handstand", "front rack", "heavy press"],
    "ankle": ["running", "jump", "calf raise", "box jump", "sprint"],
    "hip": ["deep squat", "sumo", "wide stance", "split"],
    "elbow": ["tricep extension", "overhead", "heavy curl", "close-grip", "dip"],
    "neck": ["overhead", "heavy shrug", "upright row"]
}

# ============================================================
# EXERCISE PARAMETERS
# ============================================================

# Goal-based exercise tags priority
GOAL_TAGS = {
    "weight_loss": ["cardio", "compound", "full_body", "hiit", "metabolic"],
    "muscle_gain": ["compound", "hypertrophy", "isolation", "progressive_overload", "mass"],
    "strength": ["compound", "low_rep", "powerlifting", "heavy", "power"],
    "endurance": ["cardio", "high_rep", "circuit", "functional", "stamina"],
    "general_fitness": ["compound", "functional", "bodyweight", "varied"],
    "athletic": ["explosive", "plyometric", "power", "speed", "dynamic"]
}

# Goal-related mappings for cascade fallback
RELATED_GOALS = {
    "weight_loss": ["endurance", "general_fitness"],
    "muscle_gain": ["strength", "general_fitness"],
    "strength": ["muscle_gain", "athletic"],
    "endurance": ["weight_loss", "general_fitness"],
    "general_fitness": ["weight_loss", "endurance"],
    "athletic": ["strength", "muscle_gain"]
}

# Equipment hierarchy for cascade relaxation
EQUIPMENT_HIERARCHY = {
    "Barbell": ["Dumbbell", "Kettlebells", "Bodyweight"],
    "Dumbbell": ["Kettlebells", "Bodyweight"],
    "Kettlebells": ["Dumbbell", "Bodyweight"],
    "Machine": ["Cable", "Dumbbell", "Bodyweight"],
    "Cable": ["Bands", "Dumbbell", "Bodyweight"],
    "Bands": ["Bodyweight"],
    "Medicine Ball": ["Dumbbell", "Bodyweight"],
    "Exercise Ball": ["Bodyweight"],
    "Other": ["Bodyweight"]
}

# Equipment alternatives for cascade fallback
EQUIPMENT_ALTERNATIVES = {
    "Barbell": ["Dumbbell", "Bodyweight"],
    "Dumbbell": ["Kettlebells", "Bands", "Bodyweight"],
    "Cable": ["Bands", "Dumbbell"],
    "Machine": ["Dumbbell", "Barbell", "Bodyweight"],
    "Kettlebells": ["Dumbbell", "Barbell"],
    "Bands": ["Cable", "Bodyweight"],
    "Medicine Ball": ["Dumbbell", "Bodyweight"],
    "Exercise Ball": ["Bodyweight"]
}

# ============================================================
# WORKOUT STRUCTURE
# ============================================================

# Days of week
DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Duration allocation percentages
DURATION_ALLOCATION = {
    "warmup": 0.15,  # 15% of total duration, min 5 minutes
    "cooldown": 0.10,  # 10% of total duration, min 3 minutes
    "main": 0.75  # 75% of total duration
}

# Exercise count by duration (minutes)
EXERCISE_COUNT_BY_DURATION = {
    (0, 20): 3,
    (20, 30): 4,
    (30, 45): 5,
    (45, 60): 6,
    (60, 90): 8,
    (90, 999): 10
}

# ============================================================
# SETS, REPS, REST PERIODS
# ============================================================

# Sets/reps ranges by fitness level and goal
SETS_REPS_RANGES = {
    "Beginner": {
        "weight_loss": {"sets": (2, 3), "reps": (12, 15)},
        "muscle_gain": {"sets": (3, 4), "reps": (8, 12)},
        "strength": {"sets": (3, 4), "reps": (5, 8)},
        "endurance": {"sets": (2, 3), "reps": (15, 20)},
        "general_fitness": {"sets": (2, 3), "reps": (10, 15)},
        "athletic": {"sets": (3, 4), "reps": (6, 10)}
    },
    "Intermediate": {
        "weight_loss": {"sets": (3, 4), "reps": (12, 15)},
        "muscle_gain": {"sets": (3, 5), "reps": (8, 12)},
        "strength": {"sets": (4, 5), "reps": (4, 6)},
        "endurance": {"sets": (3, 4), "reps": (15, 20)},
        "general_fitness": {"sets": (3, 4), "reps": (10, 12)},
        "athletic": {"sets": (4, 5), "reps": (5, 8)}
    },
    "Expert": {
        "weight_loss": {"sets": (4, 5), "reps": (12, 15)},
        "muscle_gain": {"sets": (4, 6), "reps": (6, 12)},
        "strength": {"sets": (5, 6), "reps": (3, 5)},
        "endurance": {"sets": (4, 5), "reps": (15, 25)},
        "general_fitness": {"sets": (4, 5), "reps": (10, 12)},
        "athletic": {"sets": (5, 6), "reps": (4, 8)}
    }
}

# Rest periods (seconds) by fitness level and goal category
REST_PERIODS = {
    "Beginner": {
        "strength": 120,
        "hypertrophy": 60,
        "endurance": 45
    },
    "Intermediate": {
        "strength": 150,
        "hypertrophy": 90,
        "endurance": 60
    },
    "Expert": {
        "strength": 180,
        "hypertrophy": 90,
        "endurance": 60
    }
}

# ============================================================
# SPLIT PATTERNS
# ============================================================

# Split preference mappings
SPLIT_PATTERNS = {
    "push_pull_legs": {
        "monday": "push",
        "tuesday": "pull", 
        "wednesday": "legs",
        "thursday": "push",
        "friday": "pull",
        "saturday": "legs",
        "sunday": "rest"
    },
    "upper_lower": {
        "monday": "upper",
        "tuesday": "lower",
        "wednesday": "rest",
        "thursday": "upper",
        "friday": "lower",
        "saturday": "full_body",
        "sunday": "rest"
    },
    "full_body": {
        "monday": "full_body",
        "tuesday": "rest",
        "wednesday": "full_body",
        "thursday": "rest",
        "friday": "full_body",
        "saturday": "rest",
        "sunday": "rest"
    }
}

# Body part groups for split programming
BODY_PART_GROUPS = {
    "push": ["Chest", "Shoulders", "Triceps"],
    "pull": ["Back", "Biceps", "Forearms"],
    "legs": ["Quadriceps", "Hamstrings", "Calves", "Glutes"],
    "core": ["Abdominals", "Abductors", "Lower Back"],
    "upper": ["Chest", "Back", "Shoulders", "Arms"],
    "lower": ["Quadriceps", "Hamstrings", "Glutes", "Calves"],
    "full_body": ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"]
}

# Recommended weekly splits by goal
WEEKLY_SPLITS = {
    "muscle_gain": {
        "monday": ["push"],
        "tuesday": ["pull"],
        "wednesday": ["legs"],
        "thursday": [],
        "friday": ["push"],
        "saturday": ["pull", "core"],
        "sunday": []
    },
    "strength": {
        "monday": ["push", "legs"],
        "tuesday": [],
        "wednesday": ["pull"],
        "thursday": [],
        "friday": ["push", "legs"],
        "saturday": [],
        "sunday": []
    },
    "weight_loss": {
        "monday": ["core", "push"],
        "tuesday": ["legs"],
        "wednesday": ["pull", "core"],
        "thursday": [],
        "friday": ["push", "legs"],
        "saturday": ["pull"],
        "sunday": []
    }
}

# ============================================================
# MOTIVATION & MESSAGING
# ============================================================

# Motivation message templates
MOTIVATION_TEMPLATES = {
    "high": [  # motivation_score > 0.3
        "You're crushing it — keep the momentum!",
        "Another week, another PR incoming.",
        "Your consistency is paying off.",
        "Solid work — aim for crisp reps; you're one step closer.",
        "You've got this — push for that extra set.",
        "On fire! Let's build on this streak.",
        "This is what dedication looks like. Proud of you!"
    ],
    "neutral": [  # -0.3 to 0.3
        "Solid work — aim for crisp reps; you're one step closer.",
        "Small wins add up — stay consistent.",
        "Focus on form today.",
        "One step closer to your goals.",
        "Quality over quantity — nail each rep.",
        "Steady progress beats perfection.",
        "Every rep counts. Every set matters.",
        "Show up and do the work. That's all that matters."
    ],
    "low": [  # < -0.3
        "Short session today — just show up.",
        "Any movement is progress.",
        "Start light — consistency beats perfection.",
        "Take it easy today — recovery matters.",
        "Baby steps — you've got this.",
        "Tough week, but you showed up. That's what counts.",
        "Every journey has ups and downs. Keep pushing.",
        "It's okay to struggle. Just don't quit."
    ]
}

# Daily tips for motivation menu
DAILY_TIPS = [
    "Consistency beats perfection — show up today.",
    "Your only competition is who you were yesterday.",
    "Small progress is still progress.",
    "The pain you feel today is the strength you feel tomorrow.",
    "Every rep counts. Every set matters.",
    "Rest is part of the training. Recovery builds strength.",
    "Focus on form before weight. Quality over quantity.",
    "Trust the process. Results take time.",
    "Celebrate small wins. They compound into big results.",
    "Listen to your body. It knows what it needs."
]

# ============================================================
# ML ADAPTATION PARAMETERS
# ============================================================

# ML adaptation thresholds
ML_ADAPTATION_THRESHOLDS = {
    "completion_rate_low": 0.7,  # Below this, reduce volume
    "completion_rate_high": 0.95,  # Above this, increase volume
    "rpe_high": 8.5,  # Above this, increase rest
    "rpe_low": 6.0,  # Below this, can reduce rest
    "satisfaction_low": 3.0,  # Below this, needs adjustment
    "satisfaction_high": 4.5  # Above this, user loves it
}

# ML adaptation increments
ML_ADAPTATION_INCREMENTS = {
    "sets_reduce": -1,  # Reduce by 1 set if struggling
    "sets_increase": 1,  # Increase by 1 set if crushing it
    "rest_increase": 15,  # Add 15 seconds if high RPE
    "rest_decrease": 15,  # Remove 15 seconds if low RPE
    "volume_multiplier_low": 0.9,  # 90% volume if completion low
    "volume_multiplier_high": 1.1  # 110% volume if completion high
}

# Recency penalty weights
RECENCY_WEIGHTS = {
    "recent_same_exercise": -0.3,  # Strong penalty for same exercise
    "recent_same_body_part": -0.15,  # Moderate penalty for same body part
    "recent_same_equipment": -0.05  # Light penalty for same equipment
}

# Preference boost weights
PREFERENCE_WEIGHTS = {
    "high_satisfaction_body_part": 0.2,  # Boost for loved body parts
    "preferred_equipment": 0.1,  # Boost for available equipment
    "goal_alignment": 0.15,  # Boost for goal-aligned exercises
    "variety_bonus": 0.1  # Bonus for introducing variety
}

# ============================================================
# CASCADE FALLBACK LEVELS
# ============================================================

CASCADE_FALLBACK_LEVELS = [
    "perfect",  # Level 1: Perfect match
    "equipment_relaxed",  # Level 2: Relaxed equipment
    "difficulty_relaxed",  # Level 3: Relaxed difficulty (±1 level)
    "related_goals",  # Level 4: Related goals
    "bmi_relaxed",  # Level 5: Slightly relaxed BMI safety
    "emergency_bodyweight"  # Level 6: Emergency safe fallback
]

# ============================================================
# EMERGENCY FALLBACK EXERCISES
# ============================================================

# Hardcoded safe exercises as absolute last resort
EMERGENCY_EXERCISES = [
    {
        "Title": "Push-ups",
        "BodyPart": "Chest",
        "Equipment": "Bodyweight",
        "Level": "Beginner",
        "exercise_id_clean": "pushups",
        "Type": "Compound"
    },
    {
        "Title": "Bodyweight Squats",
        "BodyPart": "Quadriceps",
        "Equipment": "Bodyweight",
        "Level": "Beginner",
        "exercise_id_clean": "bodyweight-squats",
        "Type": "Compound"
    },
    {
        "Title": "Plank",
        "BodyPart": "Abdominals",
        "Equipment": "Bodyweight",
        "Level": "Beginner",
        "exercise_id_clean": "plank",
        "Type": "Isometric"
    },
    {
        "Title": "Lunges",
        "BodyPart": "Quadriceps",
        "Equipment": "Bodyweight",
        "Level": "Beginner",
        "exercise_id_clean": "lunges",
        "Type": "Compound"
    },
    {
        "Title": "Mountain Climbers",
        "BodyPart": "Abdominals",
        "Equipment": "Bodyweight",
        "Level": "Intermediate",
        "exercise_id_clean": "mountain-climbers",
        "Type": "Cardio"
    },
    {
        "Title": "Glute Bridges",
        "BodyPart": "Glutes",
        "Equipment": "Bodyweight",
        "Level": "Beginner",
        "exercise_id_clean": "glute-bridges",
        "Type": "Isolation"
    },
    {
        "Title": "Wall Sit",
        "BodyPart": "Quadriceps",
        "Equipment": "Bodyweight",
        "Level": "Beginner",
        "exercise_id_clean": "wall-sit",
        "Type": "Isometric"
    }
]
