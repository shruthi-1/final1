"""
Database Schemas using Beanie ODM for MongoDB
"""
from beanie import Document
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FitnessLevel(str, Enum):
    """Fitness level enumeration"""
    Beginner = "Beginner"
    Intermediate = "Intermediate"
    Advanced = "Advanced"
    Expert = "Expert"


class User(Document):
    """User document schema"""
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    age: int = Field(..., ge=10, le=100)
    height: float = Field(..., ge=100.0, le=250.0)  # cm
    weight: float = Field(..., ge=30.0, le=300.0)  # kg
    fitness_level: FitnessLevel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    total_workouts: int = 0
    
    class Settings:
        name = "users"
        indexes = ["email", "created_at"]


class Workout(Document):
    """Workout document schema"""
    user_id: str
    exercises: List[Dict[str, Any]] = Field(default_factory=list)
    duration: int  # minutes
    difficulty: str
    performance_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    calories_burned: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    notes: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    completed: bool = False
    
    class Settings:
        name = "workouts"
        indexes = ["user_id", "date"]


class ModelWeight(Document):
    """Model weights document schema"""
    user_id: str
    model_data: bytes
    version: int = Field(default=1)
    training_samples: int = Field(default=0)
    performance_metrics: Optional[Dict[str, float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "model_weights"
        indexes = ["user_id", "version"]


# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    age: int = Field(..., ge=10, le=100)
    height: float = Field(..., ge=100.0, le=250.0)
    weight: float = Field(..., ge=30.0, le=300.0)
    fitness_level: FitnessLevel


class UserUpdate(BaseModel):
    """Schema for updating user"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: Optional[FitnessLevel] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    name: str
    email: Optional[str] = None
    age: int
    height: float
    weight: float
    fitness_level: str
    total_workouts: int
    created_at: datetime


class WorkoutCreate(BaseModel):
    """Schema for creating a workout"""
    user_id: str
    exercises: List[Dict[str, Any]]
    duration: int
    difficulty: str
    performance_score: Optional[float] = None
    calories_burned: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    notes: Optional[str] = None


class WorkoutResponse(BaseModel):
    """Schema for workout response"""
    id: str
    user_id: str
    exercises: List[Dict[str, Any]]
    duration: int
    difficulty: str
    performance_score: Optional[float] = None
    date: datetime
    completed: bool


class WorkoutGenerateRequest(BaseModel):
    """Schema for generating workout"""
    user_id: str
    target_duration: Optional[int] = 30
    focus_areas: Optional[List[str]] = None
    equipment: Optional[List[str]] = None


class APIResponse(BaseModel):
    """Standard API response"""
    status: str
    message: str
    data: Optional[Any] = None
