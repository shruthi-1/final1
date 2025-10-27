"""
Analytics Engine
Main processor for all ML analytics and insights
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Main analytics engine coordinating all ML components."""
    
    def __init__(self, db):
        self.db = db
    
    def generate_comprehensive_insights(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive ML insights for a user."""
        try:
            insights = {
                'user_id': user_id,
                'generated_at': datetime.utcnow().isoformat(),
                'summary': self._generate_summary(user_id),
                'trends': self._analyze_trends(user_id),
                'body_part_analysis': self._analyze_body_parts(user_id),
                'performance_metrics': self._calculate_performance_metrics(user_id),
                'recommendations': []
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating comprehensive insights: {e}")
            return {}
    
    def _generate_summary(self, user_id: str) -> Dict[str, Any]:
        """Generate high-level summary statistics."""
        try:
            sessions = list(self.db.session_logs.find({"user_id": user_id}))
            
            if not sessions:
                return {
                    'total_sessions': 0,
                    'total_duration': 0,
                    'avg_completion': 0.0,
                    'avg_satisfaction': 0.0
                }
            
            total_duration = sum(s.get('actual_duration', 0) for s in sessions)
            completions = [s.get('completion_percent', 0.8) for s in sessions]
            satisfactions = [s.get('satisfaction', 5) for s in sessions]
            
            # Calculate consistency (sessions per week)
            if len(sessions) > 1:
                first_date = datetime.fromisoformat(sessions[-1].get('logged_at', ''))
                last_date = datetime.fromisoformat(sessions[0].get('logged_at', ''))
                weeks = max(1, (last_date - first_date).days / 7)
                sessions_per_week = len(sessions) / weeks
            else:
                sessions_per_week = 0
            
            return {
                'total_sessions': len(sessions),
                'total_duration': total_duration,
                'avg_duration': total_duration / len(sessions),
                'avg_completion': np.mean(completions),
                'avg_satisfaction': np.mean(satisfactions),
                'consistency_score': sessions_per_week,
                'first_session': sessions[-1].get('logged_at', ''),
                'last_session': sessions[0].get('logged_at', '')
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
    
    def _analyze_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze trends over time."""
        try:
            # Get sessions from last 90 days
            cutoff_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
            sessions = list(self.db.session_logs.find({
                "user_id": user_id,
                "logged_at": {"$gte": cutoff_date}
            }).sort("logged_at", 1))
            
            if len(sessions) < 5:
                return {
                    'completion_trend': 'insufficient_data',
                    'satisfaction_trend': 'insufficient_data',
                    'volume_trend': 'insufficient_data'
                }
            
            # Extract time series data
            completions = [s.get('completion_percent', 0.8) for s in sessions]
            satisfactions = [s.get('satisfaction', 5) for s in sessions]
            volumes = [s.get('total_volume', 0) for s in sessions if s.get('total_volume')]
            
            # Calculate trends
            completion_trend = self._classify_trend(completions)
            satisfaction_trend = self._classify_trend(satisfactions)
            volume_trend = self._classify_trend(volumes) if volumes else 'no_data'
            
            # Calculate moving averages
            window = min(7, len(completions) // 3)
            if window > 1:
                completion_ma = self._moving_average(completions, window)
                satisfaction_ma = self._moving_average(satisfactions, window)
            else:
                completion_ma = completions
                satisfaction_ma = satisfactions
            
            return {
                'completion_trend': completion_trend,
                'satisfaction_trend': satisfaction_trend,
                'volume_trend': volume_trend,
                'completion_moving_avg': completion_ma[-1] if completion_ma else 0,
                'satisfaction_moving_avg': satisfaction_ma[-1] if satisfaction_ma else 0,
                'trend_confidence': min(1.0, len(sessions) / 20)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {}
    
    def _analyze_body_parts(self, user_id: str) -> Dict[str, Any]:
        """Analyze body part training frequency."""
        try:
            plans = list(self.db.user_weekly_plans.find({"user_id": user_id}))
            
            body_part_frequency = {}
            total_exercises = 0
            
            for plan in plans:
                for day_plan in plan.get('days', {}).values():
                    for exercise in day_plan.get('main', []):
                        body_part = exercise.get('body_part', 'Unknown')
                        body_part_frequency[body_part] = body_part_frequency.get(body_part, 0) + 1
                        total_exercises += 1
            
            # Calculate percentages
            body_part_percentages = {
                bp: (count / total_exercises * 100) if total_exercises > 0 else 0
                for bp, count in body_part_frequency.items()
            }
            
            # Identify imbalances
            if body_part_percentages:
                max_pct = max(body_part_percentages.values())
                min_pct = min(body_part_percentages.values())
                imbalance_score = max_pct - min_pct
            else:
                imbalance_score = 0
            
            return {
                'frequency': body_part_frequency,
                'percentages': body_part_percentages,
                'total_exercises': total_exercises,
                'imbalance_score': imbalance_score,
                'most_trained': max(body_part_percentages.items(), key=lambda x: x[1])[0] if body_part_percentages else None,
                'least_trained': min(body_part_percentages.items(), key=lambda x: x[1])[0] if body_part_percentages else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing body parts: {e}")
            return {}
    
    def _calculate_performance_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate various performance metrics."""
        try:
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", -1).limit(30))
            
            if not sessions:
                return {}
            
            # Recent vs historical comparison
            recent_sessions = sessions[:10]
            historical_sessions = sessions[10:]
            
            recent_completion = np.mean([s.get('completion_percent', 0.8) for s in recent_sessions])
            historical_completion = np.mean([s.get('completion_percent', 0.8) for s in historical_sessions]) if historical_sessions else recent_completion
            
            recent_satisfaction = np.mean([s.get('satisfaction', 5) for s in recent_sessions])
            historical_satisfaction = np.mean([s.get('satisfaction', 5) for s in historical_sessions]) if historical_sessions else recent_satisfaction
            
            # Calculate improvements
            completion_change = recent_completion - historical_completion
            satisfaction_change = recent_satisfaction - historical_satisfaction
            
            return {
                'recent_completion': recent_completion,
                'historical_completion': historical_completion,
                'completion_change': completion_change,
                'completion_change_pct': (completion_change / historical_completion * 100) if historical_completion > 0 else 0,
                'recent_satisfaction': recent_satisfaction,
                'historical_satisfaction': historical_satisfaction,
                'satisfaction_change': satisfaction_change,
                'satisfaction_change_pct': (satisfaction_change / historical_satisfaction * 100) if historical_satisfaction > 0 else 0,
                'performance_improving': completion_change > 0.05 and satisfaction_change > 0.3
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _classify_trend(self, values: List[float]) -> str:
        """Classify trend as improving, stable, or declining."""
        if len(values) < 3:
            return 'insufficient_data'
        
        # Simple linear regression
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # Normalize slope by value range
        value_range = max(values) - min(values)
        normalized_slope = slope / value_range if value_range > 0 else 0
        
        if normalized_slope > 0.1:
            return 'improving'
        elif normalized_slope < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _moving_average(self, values: List[float], window: int) -> List[float]:
        """Calculate moving average."""
        if len(values) < window:
            return values
        
        return [np.mean(values[max(0, i-window+1):i+1]) for i in range(len(values))]
