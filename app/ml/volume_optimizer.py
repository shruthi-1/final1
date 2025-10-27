"""
Workout Volume Optimizer
Adjusts training volume based on user performance
"""
import numpy as np
from typing import Dict, Any, Tuple
import logging

from app.ml.constants_ml import VOLUME_OPTIMIZATION

logger = logging.getLogger(__name__)


class VolumeOptimizer:
    """Optimize workout volume based on completion and recovery patterns."""
    
    def __init__(self, db):
        self.db = db
    
    def optimize_volume(self, user_id: str, current_sets: int, current_reps: int) -> Dict[str, Any]:
        """Optimize sets and reps based on user's historical performance."""
        try:
            # Get user's recent performance
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", -1).limit(10))
            
            if len(sessions) < 3:
                return {
                    'optimized_sets': current_sets,
                    'optimized_reps': current_reps,
                    'adjustment_reason': 'Not enough data for optimization',
                    'confidence': 0.0
                }
            
            # Calculate performance metrics
            avg_completion = np.mean([s.get('completion_percent', 0.8) for s in sessions])
            avg_rpe = np.mean([s.get('avg_rpe', 7) for s in sessions if s.get('avg_rpe')])
            avg_satisfaction = np.mean([s.get('satisfaction', 5) for s in sessions])
            
            # Determine adjustment
            adjustment_factor, reason = self._calculate_adjustment_factor(
                avg_completion, avg_rpe, avg_satisfaction
            )
            
            # Apply adjustment
            optimized_sets = max(2, int(current_sets * adjustment_factor))
            optimized_reps = current_reps  # Keep reps constant for now
            
            # Calculate confidence based on data quality
            confidence = min(1.0, len(sessions) / 10)
            
            return {
                'optimized_sets': optimized_sets,
                'optimized_reps': optimized_reps,
                'adjustment_factor': adjustment_factor,
                'adjustment_reason': reason,
                'confidence': confidence,
                'metrics': {
                    'avg_completion': avg_completion,
                    'avg_rpe': avg_rpe,
                    'avg_satisfaction': avg_satisfaction
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing volume: {e}")
            return {
                'optimized_sets': current_sets,
                'optimized_reps': current_reps,
                'adjustment_reason': 'Error in optimization',
                'confidence': 0.0
            }
    
    def _calculate_adjustment_factor(self, completion: float, rpe: float, satisfaction: float) -> Tuple[float, str]:
        """Calculate volume adjustment factor based on performance."""
        params = VOLUME_OPTIMIZATION
        
        # Case 1: User struggling (low completion)
        if completion < params['low_completion_threshold']:
            factor = params['volume_reduction_factor']
            reason = f"Reducing volume - completion rate {completion:.0%} is below target"
            return factor, reason
        
        # Case 2: User crushing it (high completion + good satisfaction)
        if completion > params['high_completion_threshold'] and satisfaction >= 4.0:
            factor = params['volume_increase_factor']
            reason = f"Increasing volume - consistent high performance (completion: {completion:.0%})"
            return factor, reason
        
        # Case 3: RPE too high
        if rpe > 9.0:
            factor = params['volume_reduction_factor']
            reason = f"Reducing volume - RPE {rpe:.1f} indicates overreaching"
            return factor, reason
        
        # Case 4: RPE too low + high completion
        if rpe < 6.0 and completion > 0.9:
            factor = params['volume_increase_factor']
            reason = f"Increasing volume - low RPE {rpe:.1f} suggests room for more work"
            return factor, reason
        
        # Case 5: Maintain current volume
        return 1.0, "Current volume is appropriate"
    
    def suggest_deload(self, user_id: str) -> Dict[str, Any]:
        """Determine if user needs a deload week."""
        try:
            # Get recent workout history
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", -1).limit(20))
            
            if len(sessions) < 10:
                return {
                    'needs_deload': False,
                    'confidence': 0.0,
                    'reason': 'Not enough training history'
                }
            
            # Count consecutive training weeks
            weeks_training = len(sessions) / 3  # Assume 3 sessions per week
            
            # Check fatigue indicators
            recent_completions = [s.get('completion_percent', 0.8) for s in sessions[:5]]
            recent_rpes = [s.get('avg_rpe', 7) for s in sessions[:5] if s.get('avg_rpe')]
            recent_satisfactions = [s.get('satisfaction', 5) for s in sessions[:5]]
            
            avg_recent_completion = np.mean(recent_completions)
            avg_recent_rpe = np.mean(recent_rpes) if recent_rpes else 7.0
            avg_recent_satisfaction = np.mean(recent_satisfactions)
            
            # Deload indicators
            low_completion = avg_recent_completion < 0.75
            high_rpe = avg_recent_rpe > 8.5
            low_satisfaction = avg_recent_satisfaction < 4.0
            enough_training = weeks_training >= VOLUME_OPTIMIZATION['deload_frequency_weeks']
            
            # Determine if deload needed
            fatigue_score = sum([low_completion, high_rpe, low_satisfaction]) / 3
            needs_deload = (fatigue_score >= 0.67) and enough_training
            
            reason = ""
            if needs_deload:
                indicators = []
                if low_completion:
                    indicators.append(f"completion {avg_recent_completion:.0%}")
                if high_rpe:
                    indicators.append(f"RPE {avg_recent_rpe:.1f}")
                if low_satisfaction:
                    indicators.append(f"satisfaction {avg_recent_satisfaction:.1f}/10")
                reason = f"Fatigue indicators: {', '.join(indicators)}"
            else:
                reason = "No significant fatigue indicators detected"
            
            return {
                'needs_deload': needs_deload,
                'confidence': min(1.0, len(sessions) / 20),
                'weeks_since_deload': weeks_training,
                'fatigue_score': fatigue_score,
                'reason': reason,
                'deload_protocol': self._get_deload_protocol() if needs_deload else None
            }
            
        except Exception as e:
            logger.error(f"Error checking deload need: {e}")
            return {'needs_deload': False, 'confidence': 0.0}
    
    def _get_deload_protocol(self) -> Dict[str, Any]:
        """Get deload week protocol."""
        return {
            'duration': '1 week',
            'volume_reduction': '40-50%',
            'intensity_reduction': '20-30%',
            'guidelines': [
                'Reduce sets by 40-50% (4 sets → 2 sets)',
                'Keep weight at 70-80% of normal',
                'Focus on movement quality and recovery',
                'Increase sleep and nutrition',
                'Return to normal training after deload week'
            ]
        }
