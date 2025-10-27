"""
Visualization Module
Generate charts and graphs for workout analytics
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import io
import base64
import logging

from app.ml.constants_ml import VISUALIZATION

logger = logging.getLogger(__name__)

# Set style
plt.style.use(VISUALIZATION['style'])
sns.set_palette(VISUALIZATION['color_palette'])


class Visualizer:
    """Generate visualizations for workout analytics."""
    
    def __init__(self, db):
        self.db = db
    

    
    def create_strength_progression_chart(self, user_id: str, save_path: str = None) -> str:
        """Create strength progression line chart."""
        try:
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", 1))
            
            if len(sessions) < 3:
                return ""
            
            # Extract data
            dates = [datetime.fromisoformat(s.get('logged_at', '')) for s in sessions]
            completions = [s.get('completion_percent', 0.8) * 100 for s in sessions]
            satisfactions = [s.get('satisfaction', 5) for s in sessions]
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=VISUALIZATION['figure_size'], 
                                           dpi=VISUALIZATION['dpi'])
            
            # Plot 1: Completion Rate
            ax1.plot(dates, completions, marker='o', linewidth=2, markersize=6, label='Completion Rate')
            ax1.axhline(y=80, color='r', linestyle='--', alpha=0.5, label='80% Target')
            ax1.set_ylabel('Completion Rate (%)', fontsize=VISUALIZATION['font_size'])
            ax1.set_title('Workout Completion Trend', fontsize=VISUALIZATION['font_size']+2, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 100)
            
            # Plot 2: Satisfaction
            ax2.plot(dates, satisfactions, marker='s', linewidth=2, markersize=6, 
                    color='#2ecc71', label='Satisfaction')
            ax2.axhline(y=5, color='r', linestyle='--', alpha=0.5, label='Baseline (5/10)')
            ax2.set_ylabel('Satisfaction (1-10)', fontsize=VISUALIZATION['font_size'])
            ax2.set_xlabel('Date', fontsize=VISUALIZATION['font_size'])
            ax2.set_title('Workout Satisfaction Trend', fontsize=VISUALIZATION['font_size']+2, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 10)
            
            plt.tight_layout()
            
            # Save or return
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                # Return as base64 string
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                plt.close()
                return img_str
                
        except Exception as e:
            logger.error(f"Error creating strength progression chart: {e}")
            return ""
    
    def create_body_part_heatmap(self, user_id: str, save_path: str = None) -> str:
        """Create heatmap of body part training frequency."""
        try:
            plans = list(self.db.user_weekly_plans.find({"user_id": user_id}).limit(8))
            if not plans:
                return ""
            
            # Collect body part data by week
            weekly_data = []
            for i, plan in enumerate(plans):
                week_label = f"Week {i+1}"
                body_parts = {}
                
                for day_plan in plan.get('days', {}).values():
                    for exercise in day_plan.get('main', []):
                        bp = exercise.get('body_part', 'Unknown')
                        body_parts[bp] = body_parts.get(bp, 0) + 1
                
                weekly_data.append({'Week': week_label, **body_parts})
            
            if not weekly_data:
                return ""
            
            # Create DataFrame
            df = pd.DataFrame(weekly_data)
            df = df.fillna(0)
            df = df.set_index('Week')
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(10, 6), dpi=VISUALIZATION['dpi'])
            
            sns.heatmap(df.T, annot=True, fmt='.0f', cmap='YlOrRd', 
                       cbar_kws={'label': 'Frequency'}, ax=ax)
            
            ax.set_title('Body Part Training Frequency by Week', 
                        fontsize=VISUALIZATION['font_size']+2, fontweight='bold')
            ax.set_xlabel('Week', fontsize=VISUALIZATION['font_size'])
            ax.set_ylabel('Body Part', fontsize=VISUALIZATION['font_size'])
            
            plt.tight_layout()
            
            # Save or return
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                plt.close()
                return img_str
                
        except Exception as e:
            logger.error(f"Error creating body part heatmap: {e}")
            return ""
    
    def create_weekly_summary_chart(self, user_id: str, save_path: str = None) -> str:
        """Create bar chart for weekly summary."""
        try:
            # Get last 4 weeks of data
            sessions = list(self.db.session_logs.find({
                "user_id": user_id
            }).sort("logged_at", -1).limit(28))
            
            if len(sessions) < 4:
                return ""
            
            # Group by week
            weekly_stats = {}
            for session in sessions:
                date = datetime.fromisoformat(session.get('logged_at', ''))
                week = date.isocalendar()[1]
                
                if week not in weekly_stats:
                    weekly_stats[week] = {'sessions': 0, 'duration': 0, 'completion': []}
                
                weekly_stats[week]['sessions'] += 1
                weekly_stats[week]['duration'] += session.get('actual_duration', 0)
                weekly_stats[week]['completion'].append(session.get('completion_percent', 0.8))
            
            # Prepare data
            weeks = sorted(weekly_stats.keys())[-4:]
            sessions_per_week = [weekly_stats[w]['sessions'] for w in weeks]
            duration_per_week = [weekly_stats[w]['duration'] for w in weeks]
            avg_completion = [np.mean(weekly_stats[w]['completion']) * 100 for w in weeks]
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=VISUALIZATION['dpi'])
            
            # Plot 1: Sessions & Duration
            x = np.arange(len(weeks))
            width = 0.35
            
            ax1.bar(x - width/2, sessions_per_week, width, label='Sessions', color='#3498db')
            ax1_twin = ax1.twinx()
            ax1_twin.bar(x + width/2, duration_per_week, width, label='Duration (min)', color='#e74c3c')
            
            ax1.set_xlabel('Week', fontsize=VISUALIZATION['font_size'])
            ax1.set_ylabel('Sessions', fontsize=VISUALIZATION['font_size'])
            ax1_twin.set_ylabel('Duration (minutes)', fontsize=VISUALIZATION['font_size'])
            ax1.set_title('Weekly Volume', fontsize=VISUALIZATION['font_size']+2, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels([f'W{w}' for w in weeks])
            ax1.legend(loc='upper left')
            ax1_twin.legend(loc='upper right')
            
            # Plot 2: Average Completion
            ax2.bar(x, avg_completion, color='#2ecc71')
            ax2.axhline(y=80, color='r', linestyle='--', alpha=0.5, label='80% Target')
            ax2.set_xlabel('Week', fontsize=VISUALIZATION['font_size'])
            ax2.set_ylabel('Completion (%)', fontsize=VISUALIZATION['font_size'])
            ax2.set_title('Weekly Completion Rate', fontsize=VISUALIZATION['font_size']+2, fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels([f'W{w}' for w in weeks])
            ax2.set_ylim(0, 100)
            ax2.legend()
            
            plt.tight_layout()
            
            # Save or return
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                plt.close()
                return img_str
                
        except Exception as e:
            logger.error(f"Error creating weekly summary chart: {e}")
            return ""
