"""
Trend Analyzer
Time series analysis for workout metrics
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging

from app.ml.constants_ml import TREND_ANALYSIS

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze trends in workout performance over time."""
    
    def __init__(self, db):
        self.db = db
    
    def analyze_all_trends(self, user_id: str, days: int = 90) -> Dict[str, Any]:
        """Analyze all metric trends for a user."""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            sessions = list(self.db.session_logs.find({
                "user_id": user_id,
                "logged_at": {"$gte": cutoff_date}
            }).sort("logged_at", 1))
            
            if len(sessions) < TREND_ANALYSIS['min_data_points']:
                return {
                    'has_sufficient_data': False,
                    'message': f'Need at least {TREND_ANALYSIS["min_data_points"]} sessions for trend analysis'
                }
            
            # Extract time series data
            df = self._sessions_to_dataframe(sessions)
            
            # Analyze each metric
            trends = {
                'has_sufficient_data': True,
                'period_days': days,
                'num_sessions': len(sessions),
                'completion_trend': self._analyze_metric_trend(df, 'completion_percent'),
                'satisfaction_trend': self._analyze_metric_trend(df, 'satisfaction'),
                'rpe_trend': self._analyze_metric_trend(df, 'avg_rpe'),
                'duration_trend': self._analyze_metric_trend(df, 'actual_duration'),
                'summary': self._generate_trend_summary(df)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {'has_sufficient_data': False}
    
    def _sessions_to_dataframe(self, sessions: List[Dict]) -> pd.DataFrame:
        """Convert session logs to pandas DataFrame."""
        data = []
        for session in sessions:
            data.append({
                'date': datetime.fromisoformat(session.get('logged_at', '')),
                'completion_percent': session.get('completion_percent', 0.8),
                'satisfaction': session.get('satisfaction', 5),
                'avg_rpe': session.get('avg_rpe', 7),
                'actual_duration': session.get('actual_duration', 45),
                'total_volume': session.get('total_volume', 0)
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('date')
        return df
    
    def _analyze_metric_trend(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """Analyze trend for a specific metric."""
        try:
            values = df[metric].dropna().values
            
            if len(values) < 3:
                return {'trend': 'insufficient_data'}
            
            # Remove outliers
            values_clean = self._remove_outliers(values)
            
            # Calculate smoothed values
            window = TREND_ANALYSIS['smoothing_window']
            if len(values_clean) >= window:
                smoothed = pd.Series(values_clean).rolling(window=window, center=True).mean().values
                smoothed = smoothed[~np.isnan(smoothed)]
            else:
                smoothed = values_clean
            
            # Calculate linear trend
            x = np.arange(len(smoothed))
            slope, intercept = np.polyfit(x, smoothed, 1)
            
            # Classify trend
            trend_classification = self._classify_trend_direction(slope, smoothed)
            
            # Calculate volatility
            volatility = np.std(values_clean) / np.mean(values_clean) if np.mean(values_clean) > 0 else 0
            
            # Current vs historical
            recent_avg = np.mean(values_clean[-5:]) if len(values_clean) >= 5 else np.mean(values_clean)
            historical_avg = np.mean(values_clean[:-5]) if len(values_clean) > 5 else recent_avg
            change_pct = ((recent_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0
            
            return {
                'trend': trend_classification,
                'slope': float(slope),
                'current_value': float(values_clean[-1]),
                'recent_avg': float(recent_avg),
                'historical_avg': float(historical_avg),
                'change_percent': float(change_pct),
                'volatility': float(volatility),
                'is_significant': abs(change_pct) >= TREND_ANALYSIS['significant_change_threshold'] * 100
            }
            
        except Exception as e:
            logger.error(f"Error analyzing metric trend: {e}")
            return {'trend': 'error'}
    
    def _remove_outliers(self, values: np.ndarray) -> np.ndarray:
        """Remove statistical outliers."""
        mean = np.mean(values)
        std = np.std(values)
        threshold = TREND_ANALYSIS['outlier_std_threshold']
        
        # Keep values within threshold standard deviations
        mask = np.abs(values - mean) <= threshold * std
        return values[mask]
    
    def _classify_trend_direction(self, slope: float, values: np.ndarray) -> str:
        """Classify trend direction."""
        # Normalize slope by value range
        value_range = np.max(values) - np.min(values)
        normalized_slope = slope / value_range if value_range > 0 else 0
        
        if normalized_slope > 0.05:
            return 'improving'
        elif normalized_slope < -0.05:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_trend_summary(self, df: pd.DataFrame) -> str:
        """Generate human-readable trend summary."""
        try:
            completion_trend = self._analyze_metric_trend(df, 'completion_percent')
            satisfaction_trend = self._analyze_metric_trend(df, 'satisfaction')
            
            summary_parts = []
            
            # Completion summary
            if completion_trend['trend'] == 'improving':
                summary_parts.append(f"✅ Completion rate improving (+{completion_trend['change_percent']:.1f}%)")
            elif completion_trend['trend'] == 'declining':
                summary_parts.append(f"⚠️ Completion rate declining ({completion_trend['change_percent']:.1f}%)")
            else:
                summary_parts.append(f"➡️ Completion rate stable ({completion_trend['current_value']:.0%})")
            
            # Satisfaction summary
            if satisfaction_trend['trend'] == 'improving':
                summary_parts.append(f"😊 Satisfaction improving (+{satisfaction_trend['change_percent']:.1f}%)")
            elif satisfaction_trend['trend'] == 'declining':
                summary_parts.append(f"😐 Satisfaction declining ({satisfaction_trend['change_percent']:.1f}%)")
            else:
                summary_parts.append(f"😊 Satisfaction stable ({satisfaction_trend['current_value']:.1f}/10)")
            
            return " | ".join(summary_parts)
            
        except:
            return "Unable to generate summary"
    
    def forecast_next_week(self, user_id: str) -> Dict[str, Any]:
        """Simple forecast for next week's expected performance."""
        try:
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", -1).limit(20))
            
            if len(sessions) < 5:
                return {'forecast_available': False}
            
            # Extract recent values
            recent_completions = [s.get('completion_percent', 0.8) for s in sessions[:10]]
            recent_satisfactions = [s.get('satisfaction', 5) for s in sessions[:10]]
            
            # Simple moving average forecast
            forecast_completion = np.mean(recent_completions)
            forecast_satisfaction = np.mean(recent_satisfactions)
            
            # Adjust for trend
            x = np.arange(len(recent_completions))
            completion_slope = np.polyfit(x, recent_completions, 1)[0]
            
            # Forecast one week ahead (assuming 3 sessions)
            forecast_completion += completion_slope * 3
            forecast_completion = max(0.0, min(1.0, forecast_completion))
            
            return {
                'forecast_available': True,
                'expected_completion': float(forecast_completion),
                'expected_satisfaction': float(forecast_satisfaction),
                'confidence': min(1.0, len(sessions) / 20),
                'recommendation': self._get_forecast_recommendation(forecast_completion, forecast_satisfaction)
            }
            
        except Exception as e:
            logger.error(f"Error forecasting: {e}")
            return {'forecast_available': False}
    
    def _get_forecast_recommendation(self, completion: float, satisfaction: float) -> str:
        """Get recommendation based on forecast."""
        if completion < 0.7:
            return "⚠️ Low completion expected. Consider reducing workout volume."
        elif completion > 0.9 and satisfaction > 4.0:
            return "🔥 High performance expected. Great time to push harder!"
        elif satisfaction < 4.0:
            return "💡 Consider varying exercises to improve satisfaction."
        else:
            return "✅ Steady performance expected. Keep up the consistency!"
