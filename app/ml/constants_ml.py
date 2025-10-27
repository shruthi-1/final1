"""
ML-specific constants and configuration for FitGen AI
"""

# Model file paths
MODEL_PATHS = {
    'exercise_recommender': 'models/exercise_recommender_{user_id}.pkl',
    'injury_predictor': 'models/injury_predictor_{user_id}.pkl',
    'plateau_detector': 'models/plateau_detector_{user_id}.pkl',
    'volume_optimizer': 'models/volume_optimizer_{user_id}.pkl',
    'completion_predictor': 'models/completion_predictor_{user_id}.pkl'
}

# Feature importance thresholds
FEATURE_IMPORTANCE_THRESHOLD = 0.05

# Model performance thresholds
MIN_MODEL_ACCURACY = 0.6
MIN_TRAINING_SAMPLES = 10
MIN_SESSIONS_FOR_ANALYSIS = 5

# Recommendation confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.4

# Analytics time windows (days)
TIME_WINDOWS = {
    'week': 7,
    'month': 30,
    'quarter': 90,
    'year': 365
}

# ML feature categories
FEATURE_CATEGORIES = {
    'user_profile': ['age', 'gender', 'bmi', 'fitness_level', 'primary_goal'],
    'workout_history': ['completion_rate', 'avg_rpe', 'avg_satisfaction', 'total_volume'],
    'temporal': ['day_of_week', 'time_of_day', 'days_since_start', 'session_count'],
    'exercise_specific': ['body_part', 'equipment', 'difficulty_level', 'sets', 'reps'],
    'contextual': ['mood', 'energy_level', 'sleep_quality', 'stress_level']
}

# Injury risk factors
INJURY_RISK_FACTORS = {
    'high_rpe_streak': {'threshold': 8.5, 'consecutive_days': 5, 'weight': 0.3},
    'volume_spike': {'threshold': 1.3, 'window_days': 7, 'weight': 0.25},
    'insufficient_rest': {'min_hours': 24, 'between_sessions': True, 'weight': 0.2},
    'overuse_pattern': {'same_bodypart_days': 3, 'window_days': 7, 'weight': 0.15},
    'declining_completion': {'drop_threshold': 0.2, 'window_days': 14, 'weight': 0.1}
}

# Plateau detection parameters
PLATEAU_PARAMS = {
    'min_stagnation_weeks': 3,
    'performance_variance_threshold': 0.05,
    'volume_increase_required': 0.10,
    'strength_plateau_weeks': 4
}

# Volume optimization parameters
VOLUME_OPTIMIZATION = {
    'low_completion_threshold': 0.7,
    'high_completion_threshold': 0.95,
    'volume_reduction_factor': 0.85,  # Reduce to 85% if struggling
    'volume_increase_factor': 1.10,   # Increase to 110% if crushing it
    'max_weekly_increase': 0.15,      # Max 15% increase per week
    'deload_frequency_weeks': 4
}

# Exercise recommendation parameters
RECOMMENDATION_PARAMS = {
    'min_similar_users': 3,
    'similarity_threshold': 0.6,
    'min_satisfaction_score': 4.0,
    'min_completion_rate': 0.8,
    'diversity_factor': 0.3  # Balance between similarity and diversity
}

# Trend analysis parameters
TREND_ANALYSIS = {
    'smoothing_window': 7,  # Days for moving average
    'outlier_std_threshold': 2.5,
    'significant_change_threshold': 0.15,  # 15% change is significant
    'min_data_points': 10
}

# Visualization settings
VISUALIZATION = {
    'figure_size': (12, 6),
    'dpi': 100,
    'style': 'seaborn-v0_8-darkgrid',
    'color_palette': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'],
    'font_size': 10
}

# ML model hyperparameters
MODEL_HYPERPARAMETERS = {
    'random_forest': {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'random_state': 42
    },
    'gradient_boosting': {
        'n_estimators': 50,
        'learning_rate': 0.1,
        'max_depth': 5,
        'random_state': 42
    }
}

# Risk level definitions
RISK_LEVELS = {
    'low': {'color': '🟢', 'threshold': (0, 0.3), 'action': 'continue'},
    'medium': {'color': '🟡', 'threshold': (0.3, 0.7), 'action': 'monitor'},
    'high': {'color': '🔴', 'threshold': (0.7, 1.0), 'action': 'immediate_action'}
}

# Workout completion prediction features
COMPLETION_FEATURES = [
    'day_of_week',
    'workout_duration',
    'num_exercises',
    'avg_sets_per_exercise',
    'user_fitness_level',
    'days_since_last_workout',
    'recent_completion_rate',
    'recent_avg_satisfaction'
]

# Export formats
EXPORT_FORMATS = {
    'csv': {'extension': '.csv', 'mime': 'text/csv'},
    'pdf': {'extension': '.pdf', 'mime': 'application/pdf'},
    'json': {'extension': '.json', 'mime': 'application/json'}
}
