"""
Injury Risk Prediction System
Analyzes patterns to predict injury risk
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from app.ml.constants_ml import INJURY_RISK_FACTORS, RISK_LEVELS

logger = logging.getLogger(__name__)


class InjuryPredictor:
    """Predict injury risk from workout patterns."""
    
    def __init__(self, db):
        self.db = db
    
    def analyze_risk(self, user_id: str) -> Dict[str, Any]:
        """Analyze injury risk for a user."""
        try:
            # Get recent sessions (last 14 days)
            cutoff_date = (datetime.utcnow() - timedelta(days=14)).isoformat()
            sessions = list(self.db.session_logs.find({
                "user_id": user_id,
                "logged_at": {"$gte": cutoff_date}
            }).sort("logged_at", -1))
            
            if len(sessions) < 3:
                return {
                    'overall_risk': 'low',
                    'risk_score': 0.0,
                    'risk_factors': [],
                    'recommendations': [],
                    'explanation': 'Not enough data for analysis'
                }
            
            # Calculate risk factors
            risk_factors = []
            risk_scores = []
            
            # 1. High RPE Streak
            high_rpe_risk = self._check_high_rpe_streak(sessions)
            if high_rpe_risk['detected']:
                risk_factors.append(high_rpe_risk)
                risk_scores.append(high_rpe_risk['risk_score'])
            
            # 2. Volume Spike
            volume_spike_risk = self._check_volume_spike(user_id, sessions)
            if volume_spike_risk['detected']:
                risk_factors.append(volume_spike_risk)
                risk_scores.append(volume_spike_risk['risk_score'])
            
            # 3. Insufficient Rest
            rest_risk = self._check_insufficient_rest(sessions)
            if rest_risk['detected']:
                risk_factors.append(rest_risk)
                risk_scores.append(rest_risk['risk_score'])
            
            # 4. Overuse Pattern
            overuse_risk = self._check_overuse_pattern(user_id)
            if overuse_risk['detected']:
                risk_factors.append(overuse_risk)
                risk_scores.append(overuse_risk['risk_score'])
            
            # 5. Declining Completion
            completion_risk = self._check_declining_completion(sessions)
            if completion_risk['detected']:
                risk_factors.append(completion_risk)
                risk_scores.append(completion_risk['risk_score'])
            
            # Calculate overall risk score
            overall_risk_score = np.mean(risk_scores) if risk_scores else 0.0
            
            # Determine risk level
            overall_risk = self._determine_risk_level(overall_risk_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_factors)
            
            return {
                'overall_risk': overall_risk,
                'risk_score': overall_risk_score,
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'explanation': self._generate_explanation(overall_risk, risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing injury risk: {e}")
            return {
                'overall_risk': 'unknown',
                'risk_score': 0.0,
                'risk_factors': [],
                'recommendations': []
            }
    
    def _check_high_rpe_streak(self, sessions: List[Dict]) -> Dict:
        """Check for consecutive high RPE sessions."""
        params = INJURY_RISK_FACTORS['high_rpe_streak']
        threshold = params['threshold']
        consecutive_required = params['consecutive_days']
        
        rpes = [s.get('avg_rpe', 7) for s in sessions if s.get('avg_rpe')]
        
        consecutive_high = 0
        max_consecutive = 0
        
        for rpe in rpes:
            if rpe >= threshold:
                consecutive_high += 1
                max_consecutive = max(max_consecutive, consecutive_high)
            else:
                consecutive_high = 0
        
        detected = max_consecutive >= consecutive_required
        
        if detected:
            risk_score = min(1.0, (max_consecutive / consecutive_required) * params['weight'])
            return {
                'detected': True,
                'name': 'High RPE Streak',
                'description': f'{max_consecutive} consecutive sessions with RPE ≥ {threshold}',
                'risk_score': risk_score,
                'confidence': 0.85
            }
        
        return {'detected': False}
    
    def _check_volume_spike(self, user_id: str, recent_sessions: List[Dict]) -> Dict:
        """Check for sudden volume increases."""
        params = INJURY_RISK_FACTORS['volume_spike']
        
        # Get historical average volume
        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        historical = list(self.db.session_logs.find({
            "user_id": user_id,
            "logged_at": {"$lt": cutoff_date}
        }).limit(20))
        
        if len(historical) < 5:
            return {'detected': False}
        
        historical_volumes = [s.get('total_volume', 0) for s in historical if s.get('total_volume')]
        recent_volumes = [s.get('total_volume', 0) for s in recent_sessions if s.get('total_volume')]
        
        if not historical_volumes or not recent_volumes:
            return {'detected': False}
        
        avg_historical = np.mean(historical_volumes)
        avg_recent = np.mean(recent_volumes)
        
        spike_ratio = avg_recent / avg_historical if avg_historical > 0 else 1.0
        
        detected = spike_ratio >= params['threshold']
        
        if detected:
            risk_score = min(1.0, (spike_ratio - 1.0) * params['weight'])
            return {
                'detected': True,
                'name': 'Volume Spike',
                'description': f'Training volume increased {(spike_ratio-1)*100:.0f}% recently',
                'risk_score': risk_score,
                'confidence': 0.75
            }
        
        return {'detected': False}
    
    def _check_insufficient_rest(self, sessions: List[Dict]) -> Dict:
        """Check for insufficient rest between sessions."""
        params = INJURY_RISK_FACTORS['insufficient_rest']
        min_rest_hours = params['min_hours']
        
        insufficient_rest_count = 0
        
        for i in range(len(sessions) - 1):
            current = datetime.fromisoformat(sessions[i].get('logged_at', ''))
            previous = datetime.fromisoformat(sessions[i+1].get('logged_at', ''))
            
            hours_between = (current - previous).total_seconds() / 3600
            
            if hours_between < min_rest_hours:
                insufficient_rest_count += 1
        
        detected = insufficient_rest_count >= 2
        
        if detected:
            risk_score = min(1.0, (insufficient_rest_count / len(sessions)) * params['weight'])
            return {
                'detected': True,
                'name': 'Insufficient Rest',
                'description': f'{insufficient_rest_count} sessions with <{min_rest_hours}h rest',
                'risk_score': risk_score,
                'confidence': 0.70
            }
        
        return {'detected': False}
    
    def _check_overuse_pattern(self, user_id: str) -> Dict:
        """Check for overuse of specific body parts."""
        params = INJURY_RISK_FACTORS['overuse_pattern']
        
        # Get recent workout plans
        cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        plans = list(self.db.user_weekly_plans.find({
            "user_id": user_id,
            "generated_at_iso": {"$gte": cutoff_date}
        }))
        
        if not plans:
            return {'detected': False}
        
        # Count body part frequency
        body_part_days = {}
        
        for plan in plans:
            for day_plan in plan.get('days', {}).values():
                for exercise in day_plan.get('main', []):
                    body_part = exercise.get('body_part', '')
                    if body_part:
                        body_part_days[body_part] = body_part_days.get(body_part, 0) + 1
        
        # Check for overuse
        overused_parts = {bp: count for bp, count in body_part_days.items() 
                          if count >= params['same_bodypart_days']}
        
        detected = len(overused_parts) > 0
        
        if detected:
            most_overused = max(overused_parts.items(), key=lambda x: x[1])
            risk_score = params['weight']
            
            return {
                'detected': True,
                'name': 'Overuse Pattern',
                'description': f'{most_overused[0]} trained {most_overused[1]} days in a week',
                'risk_score': risk_score,
                'confidence': 0.65
            }
        
        return {'detected': False}
    
    def _check_declining_completion(self, sessions: List[Dict]) -> Dict:
        """Check for declining completion rates."""
        params = INJURY_RISK_FACTORS['declining_completion']
        
        if len(sessions) < 5:
            return {'detected': False}
        
        completions = [s.get('completion_percent', 0.8) for s in sessions]
        
        # Compare first half vs second half
        mid = len(completions) // 2
        first_half_avg = np.mean(completions[:mid])
        second_half_avg = np.mean(completions[mid:])
        
        decline = first_half_avg - second_half_avg
        
        detected = decline >= params['drop_threshold']
        
        if detected:
            risk_score = min(1.0, decline * params['weight'])
            return {
                'detected': True,
                'name': 'Declining Completion',
                'description': f'Completion rate dropped {decline*100:.0f}% recently',
                'risk_score': risk_score,
                'confidence': 0.60
            }
        
        return {'detected': False}
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine overall risk level from score."""
        for level, info in RISK_LEVELS.items():
            min_threshold, max_threshold = info['threshold']
            if min_threshold <= risk_score < max_threshold:
                return level
        return 'low'
    
    def _generate_recommendations(self, risk_factors: List[Dict]) -> List[Dict]:
        """Generate recommendations based on risk factors."""
        recommendations = []
        
        for factor in risk_factors:
            if factor['name'] == 'High RPE Streak':
                recommendations.append({
                    'action': 'Take a deload week - reduce intensity by 30-40%',
                    'reason': 'Sustained high RPE indicates accumulated fatigue',
                    'priority': 'high'
                })
            
            elif factor['name'] == 'Volume Spike':
                recommendations.append({
                    'action': 'Reduce training volume by 20% for 1-2 weeks',
                    'reason': 'Rapid volume increases increase injury risk',
                    'priority': 'high'
                })
            
            elif factor['name'] == 'Insufficient Rest':
                recommendations.append({
                    'action': 'Ensure 48+ hours between intense sessions',
                    'reason': 'Adequate recovery is essential for adaptation',
                    'priority': 'medium'
                })
            
            elif factor['name'] == 'Overuse Pattern':
                recommendations.append({
                    'action': 'Rotate body part focus more frequently',
                    'reason': 'Overuse increases risk of repetitive strain injuries',
                    'priority': 'medium'
                })
            
            elif factor['name'] == 'Declining Completion':
                recommendations.append({
                    'action': 'Reduce workout duration or exercise count',
                    'reason': 'Declining completion suggests overreaching',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def _generate_explanation(self, risk_level: str, risk_factors: List[Dict]) -> str:
        """Generate human-readable explanation."""
        if risk_level == 'low':
            return "Your training patterns look healthy. Keep up the good work!"
        
        elif risk_level == 'medium':
            factor_names = [f['name'] for f in risk_factors]
            return f"Moderate risk detected: {', '.join(factor_names)}. Consider the recommendations to reduce risk."
        
        else:  # high
            return "High injury risk detected. Please review recommendations and consider reducing training intensity immediately."
