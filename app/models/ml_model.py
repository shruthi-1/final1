"""
Machine Learning Model for Workout Generation
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import io


class WorkoutModel:
    """ML Model for personalized workout generation"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.version = 1
        self.training_samples = 0
    
    def serialize(self) -> bytes:
        """Serialize model to bytes"""
        buffer = io.BytesIO()
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "is_trained": self.is_trained,
            "version": self.version,
            "training_samples": self.training_samples
        }
        joblib.dump(model_data, buffer)
        return buffer.getvalue()
    
    @classmethod
    def deserialize(cls, data: bytes) -> "WorkoutModel":
        """Deserialize model from bytes"""
        buffer = io.BytesIO(data)
        model_data = joblib.load(buffer)
        
        instance = cls()
        instance.model = model_data["model"]
        instance.scaler = model_data["scaler"]
        instance.is_trained = model_data["is_trained"]
        instance.version = model_data["version"]
        instance.training_samples = model_data["training_samples"]
        
        return instance
