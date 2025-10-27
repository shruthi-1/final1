"""
Lightweight ML Insights System
Production-ready with minimal dependencies
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class MLInsights:
    """Lightweight ML insights without heavy model dependencies."""
    
    def __init__(self, db):
        self.db = db
    
    def get_exercise_recommendations(self, user_id: str, n=5) -> List[Dict]:
        """Get exercise recommendations based on collaborative filtering."""
        try:
            # Get user profile
            user = self.db.users.find_one({"user_id": user_id})
            if not user:
                return []
            
            # Get user's completed exercises
            user_sessions = list(self.db.session_logs.find({"user_id": user_id}))
            user_exercises = set()
            for session in user_sessions:
                user_exercises.update(session.get('exercises_completed', []))
            
            # Find similar users
            similar_users = self._find_similar_users(user)
            
            # Get recommendations from similar users
            recommendations = {}
            
            for similar_user in similar_users[:5]:
                similar_sessions = list(self.db.session_logs.find({"user_id": similar_user['user_id']}))
                
                for session in similar_sessions:
                    satisfaction = session.get('satisfaction', 5)
                    completion = session.get('completion_percent', 0.8)
                    
                    if satisfaction >= 4 and completion >= 0.8:
                        for ex_id in session.get('exercises_completed', []):
                            if ex_id not in user_exercises:
                                if ex_id not in recommendations:
                                    recommendations[ex_id] = 0
                                recommendations[ex_id] += satisfaction * completion
            
            # Get top recommendations
            sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
            
            result = []
            for ex_id, score in sorted_recs[:n]:
                exercise = self.db.exercises.find_one({"exercise_id_clean": ex_id})
                if exercise:
                    result.append({
                        'name': exercise.get('Title', ''),
                        'body_part': exercise.get('BodyPart', ''),
                        'equipment': exercise.get('Equipment', ''),
                        'confidence_score': min(1.0, score / 10),
                        'reason': f"Users similar to you rated this {score/2:.1f}/5"
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def _find_similar_users(self, user: Dict) -> List[Dict]:
        """Find users with similar profiles."""
        similar = list(self.db.users.find({
            "fitness_level": user.get('fitness_level'),
            "primary_goal": user.get('primary_goal'),
            "user_id": {"$ne": user['user_id']}
        }).limit(10))
        
        return similar
    
    def get_injury_risk_analysis(self, user_id: str) -> Dict:
        """Analyze injury risk from patterns."""
        try:
            sessions = list(self.db.session_logs.find(
                {"user_id": user_id}
            ).sort("logged_at", -1).limit(14))
            
            if len(sessions) < 3:
                return {
                    'overall_risk': 'low',
                    'risk_factors': [],
                    'recommendations': []
                }
            
            # Calculate RPE trends
            recent_rpes = [s.get('avg_rpe', 7) for s in sessions[:7] if s.get('avg_rpe')]
            avg_rpe = np.mean(recent_rpes) if recent_rpes else 7.0
            
            # Check for high RPE streak
            high_rpe_streak = sum(1 for rpe in recent_rpes if rpe >= 8.5)
            
            # Check completion rates
            completions = [s.get('completion_percent', 0.8) for s in sessions]
            avg_completion = np.mean(completions)
            declining_completion = completions[0] < completions[-1] - 0.2 if len(completions) > 1 else False
            
            # Determine risk level
            risk_factors = []
            recommendations = []
            
            if high_rpe_streak >= 3:
                risk_factors.append({
                    'name': 'High RPE Streak',
                    'description': f'{high_rpe_streak} consecutive high-intensity sessions',
                    'confidence': 0.8
                })
                recommendations.append({
                    'action': 'Reduce training intensity by 15-20%',
                    'reason': 'Sustained high RPE increases injury risk'
                })
            
            if avg_rpe > 8.5:
                risk_factors.append({
                    'name': 'Consistently High RPE',
                    'description': f'Average RPE of {avg_rpe:.1f} over last week',
                    'confidence': 0.75
                })
                recommendations.append({
                    'action': 'Add more rest days or deload week',
                    'reason': 'High average RPE suggests insufficient recovery'
                })
            
            if declining_completion:
                risk_factors.append({
                    'name': 'Declining Completion Rate',
                    'description': 'Workout completion dropping over time',
                    'confidence': 0.7
                })
                recommendations.append({
                    'action': 'Reduce workout volume by 20%',
                    'reason': 'Declining completion suggests overreaching'
                })
            
            # Determine overall risk
            if len(risk_factors) >= 2:
                overall_risk = 'high'
            elif len(risk_factors) == 1:
                overall_risk = 'medium'
            else:
                overall_risk = 'low'
            
            return {
                'overall_risk': overall_risk,
                'risk_factors': risk_factors,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing injury risk: {e}")
            return {'overall_risk': 'unknown', 'risk_factors': [], 'recommendations': []}
    
    def detect_plateau(self, user_id: str) -> Dict:
        """Detect training plateaus."""
        try:
            # Get recent workout plans
            plans = list(self.db.user_weekly_plans.find(
                {"user_id": user_id}
            ).sort("generated_at_iso", -1).limit(4))
            
            if len(plans) < 3:
                return {'has_plateau': False, 'recommendations': []}
            
            # Extract volume metrics
            volumes = []
            for plan in plans:
                total_sets = 0
                for day_plan in plan.get('days', {}).values():
                    for exercise in day_plan.get('main', []):
                        total_sets += exercise.get('sets', 0)
                volumes.append(total_sets)
            
            # Check for stagnation
            volume_variance = np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
            
            has_plateau = volume_variance < 0.05  # Less than 5% variance
            
            recommendations = []
            if has_plateau:
                recommendations = [
                    {
                        'action': 'Increase training volume by 10-15%',
                        'reason': 'Volume has been stagnant for 3+ weeks'
                    },
                    {
                        'action': 'Switch to different exercise variations',
                        'reason': 'New stimulus needed to break plateau'
                    },
                    {
                        'action': 'Consider changing split (e.g., Push/Pull/Legs)',
                        'reason': 'Different training structure may help progress'
                    }
                ]
            
            return {
                'has_plateau': has_plateau,
                'weeks_stagnant': len(plans) if has_plateau else 0,
                'current_volume': volumes[0] if volumes else 0,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error detecting plateau: {e}")
            return {'has_plateau': False, 'recommendations': []}
    
    def get_strength_progression(self, user_id: str) -> Dict:
        """Get strength progression data."""
        try:
            sessions = list(self.db.session_logs.find(
                {"user_id": user_id}
            ).sort("logged_at", 1))
            
            if not sessions:
                return {'has_data': False}
            
            dates = [s.get('logged_at', '') for s in sessions]
            volumes = [s.get('total_volume', 0) for s in sessions]
            completions = [s.get('completion_percent', 0.8) for s in sessions]
            satisfactions = [s.get('satisfaction', 5) for s in sessions]
            
            # Calculate trends
            completion_trend = 'improving' if completions[-1] > completions[0] else 'declining'
            volume_trend = 'increasing' if volumes[-1] > volumes[0] else 'decreasing'
            
            return {
                'has_data': True,
                'total_sessions': len(sessions),
                'dates': dates,
                'volumes': volumes,
                'completions': completions,
                'satisfactions': satisfactions,
                'completion_trend': completion_trend,
                'volume_trend': volume_trend,
                'avg_satisfaction': np.mean(satisfactions)
            }
            
        except Exception as e:
            logger.error(f"Error getting progression: {e}")
            return {'has_data': False}
    
    def get_body_part_frequency(self, user_id: str) -> Dict[str, int]:
        """Get frequency of body parts trained."""
        try:
            plans = list(self.db.user_weekly_plans.find({"user_id": user_id}))
            
            body_part_count = {}
            
            for plan in plans:
                for day_plan in plan.get('days', {}).values():
                    for exercise in day_plan.get('main', []):
                        body_part = exercise.get('body_part', 'Unknown')
                        body_part_count[body_part] = body_part_count.get(body_part, 0) + 1
            
            return body_part_count
            
        except Exception as e:
            logger.error(f"Error getting body part frequency: {e}")
            return {}
