"""
REST API Module for Workout Tracking Application

This module provides the FastAPI application and endpoints for receiving and
managing workout data. It handles:
- Data validation using Pydantic models
- Workout data submission
- Workout data retrieval
- Error handling and HTTP responses

The API provides endpoints for:
- POST /workouts: Submit new workout data
- GET /workouts: Retrieve all stored workouts

Example:
    To start the API server:
    ```
    uvicorn api:app --host 0.0.0.0 --port 8000
    ```
"""

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from database import DatabaseManager
from data_processor import WorkoutDataProcessor

app = FastAPI()
db = DatabaseManager()
processor = WorkoutDataProcessor()

router = APIRouter(prefix="/api/v1/workouts", tags=["workouts"])

# Pydantic models for data validation
class Measurement(BaseModel):
    units: str
    qty: float

class RoutePoint(BaseModel):
    speed: float
    speedAccuracy: float
    longitude: float
    courseAccuracy: float
    timestamp: datetime
    altitude: float
    course: float
    latitude: float
    horizontalAccuracy: float
    verticalAccuracy: float

class Workout(BaseModel):
    id: str
    name: str
    start: datetime
    end: datetime
    duration: float
    location: str
    distance: Optional[Measurement]
    elevationUp: Optional[Measurement]
    temperature: Optional[Measurement]
    humidity: Optional[Measurement]
    intensity: Optional[Measurement]
    activeEnergyBurned: Optional[Measurement]
    route: List[RoutePoint]
    metadata: Dict = Field(default_factory=dict)

class WorkoutPayload(BaseModel):
    data: Dict[str, List[Workout]]

@router.post("/")
async def create_workout(payload: WorkoutPayload):
    try:
        # Here you would:
        # 1. Process the workout data
        # 2. Save to database
        # 3. Return success response
        
        return {
            "status": "success",
            "message": f"Received {len(payload.data['workouts'])} workouts",
            "workout_ids": [workout.id for workout in payload.data['workouts']]
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing workout data: {str(e)}"
        )

@router.get("/{workout_id}")
async def get_workout(workout_id: str):
    # Retrieve workout data from database
    pass 

app.include_router(router)