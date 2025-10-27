"""
Model Manager
Centralized management for all ML models
"""
import os
import joblib
from typing import Dict, Any
import logging

from app.ml.exercise_recommender import ExerciseRecommender
from app.ml.injury_predictor import InjuryPredictor
from app.ml.plateau_detector import PlateauDetector
from app.ml.volume_optimizer import VolumeOptimizer
from app.ml.completion_predictor import CompletionPredictor
from app.ml.analytics_engine import AnalyticsEngine
from app.ml.trend_analyzer import TrendAnalyzer
from app.ml.visualizer import Visualizer

logger = logging.getLogger(__name__)


class ModelManager:
    """Centralized manager for all ML models and analytics."""
    
    def __init__(self, db):
        self.db = db
        
        # Initialize all components
        self.exercise_recommender = ExerciseRecommender(db)
        self.injury_predictor = InjuryPredictor(db)
        self.plateau_detector = PlateauDetector(db)
        self.volume_optimizer = VolumeOptimizer(db)
        self.completion_predictor = CompletionPredictor(db)
        self.analytics_engine = AnalyticsEngine(db)
        self.trend_analyzer = TrendAnalyzer(db)
        self.visualizer = Visualizer(db)
        
        # Ensure models directory exists
        os.makedirs('models', exist_ok=True)
    
    # ============================================================
    # EXERCISE RECOMMENDATIONS
    # ============================================================
    
    def get_exercise_recommendations(self, user_id: str, n: int = 5) -> list:
        """Get exercise recommendations for user."""
        try:
            return self.exercise_recommender.get_recommendations(user_id, n)
        except Exception as e:
            logger.error(f"Error getting exercise recommendations: {e}")
            return []
    
    # ============================================================
    # INJURY RISK ANALYSIS
    # ============================================================
    
    def get_injury_risk_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get injury risk analysis for user."""
        try:
            return self.injury_predictor.analyze_risk(user_id)
        except Exception as e:
            logger.error(f"Error analyzing injury risk: {e}")
            return {
                'overall_risk': 'unknown',
                'risk_factors': [],
                'recommendations': []
            }
    
    # ============================================================
    # PLATEAU DETECTION
    # ============================================================
    
    def detect_plateau(self, user_id: str) -> Dict[str, Any]:
        """Detect training plateau for user."""
        try:
            return self.plateau_detector.detect_plateau(user_id)
        except Exception as e:
            logger.error(f"Error detecting plateau: {e}")
            return {
                'has_plateau': False,
                'confidence': 0.0,
                'recommendations': []
            }
    
    # ============================================================
    # VOLUME OPTIMIZATION
    # ============================================================
    
    def optimize_volume(self, user_id: str, current_sets: int, current_reps: int) -> Dict[str, Any]:
        """Optimize workout volume for user."""
        try:
            return self.volume_optimizer.optimize_volume(user_id, current_sets, current_reps)
        except Exception as e:
            logger.error(f"Error optimizing volume: {e}")
            return {
                'optimized_sets': current_sets,
                'optimized_reps': current_reps,
                'adjustment_reason': 'Error in optimization'
            }
    
    def check_deload_needed(self, user_id: str) -> Dict[str, Any]:
        """Check if user needs a deload week."""
        try:
            return self.volume_optimizer.suggest_deload(user_id)
        except Exception as e:
            logger.error(f"Error checking deload: {e}")
            return {'needs_deload': False}
    
    # ============================================================
    # COMPLETION PREDICTION
    # ============================================================
    
    def predict_workout_completion(self, user_id: str, duration: int, num_exercises: int) -> Dict[str, Any]:
        """Predict workout completion probability."""
        try:
            return self.completion_predictor.predict_completion(user_id, duration, num_exercises)
        except Exception as e:
            logger.error(f"Error predicting completion: {e}")
            return {
                'completion_probability': 0.8,
                'confidence': 0.0
            }
    
    # ============================================================
    # ANALYTICS & TRENDS
    # ============================================================
    
    def get_comprehensive_insights(self, user_id: str) -> Dict[str, Any]:
        """Get all ML insights for user."""
        try:
            return self.analytics_engine.generate_comprehensive_insights(user_id)
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {}
    
    def analyze_trends(self, user_id: str, days: int = 90) -> Dict[str, Any]:
        """Analyze trends for user."""
        try:
            return self.trend_analyzer.analyze_all_trends(user_id, days)
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {'has_sufficient_data': False}
    
    def forecast_next_week(self, user_id: str) -> Dict[str, Any]:
        """Forecast next week's performance."""
        try:
            return self.trend_analyzer.forecast_next_week(user_id)
        except Exception as e:
            logger.error(f"Error forecasting: {e}")
            return {'forecast_available': False}
    
    # ============================================================
    # VISUALIZATIONS
    # ============================================================
    
    def create_progression_chart(self, user_id: str, save_path: str = None) -> str:
        """Create strength progression chart."""
        try:
            return self.visualizer.create_strength_progression_chart(user_id, save_path)
        except Exception as e:
            logger.error(f"Error creating progression chart: {e}")
            return ""
    
    def create_body_part_heatmap(self, user_id: str, save_path: str = None) -> str:
        """Create body part frequency heatmap."""
        try:
            return self.visualizer.create_body_part_heatmap(user_id, save_path)
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return ""
    
    def create_weekly_summary_chart(self, user_id: str, save_path: str = None) -> str:
        """Create weekly summary chart."""
        try:
            return self.visualizer.create_weekly_summary_chart(user_id, save_path)
        except Exception as e:
            logger.error(f"Error creating weekly summary chart: {e}")
            return ""
    
    # ============================================================
    # COMPLETE ML DASHBOARD
    # ============================================================
    
    def generate_ml_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Generate complete ML dashboard data."""
        try:
            dashboard = {
                'user_id': user_id,
                'exercise_recommendations': self.get_exercise_recommendations(user_id, 5),
                'injury_risk': self.get_injury_risk_analysis(user_id),
                'plateau_detection': self.detect_plateau(user_id),
                'trends': self.analyze_trends(user_id, 30),
                'forecast': self.forecast_next_week(user_id),
                'comprehensive_insights': self.get_comprehensive_insights(user_id)
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating ML dashboard: {e}")
            return {}
    
    # ============================================================
    # MODEL PERSISTENCE
    # ============================================================
    
    def save_all_models(self, user_id: str) -> bool:
        """Save all models for a user."""
        try:
            # Build and save exercise recommender
            if self.exercise_recommender.build_interaction_matrix():
                self.exercise_recommender.save_model(user_id)
            
            logger.info(f"Saved all models for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
    
    def load_all_models(self, user_id: str) -> bool:
        """Load all models for a user."""
        try:
            # Load exercise recommender if exists
            model_path = f'models/exercise_recommender_{user_id}.pkl'
            if os.path.exists(model_path):
                self.exercise_recommender.load_model(user_id)
            
            logger.info(f"Loaded models for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
