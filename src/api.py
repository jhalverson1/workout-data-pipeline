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
from typing import List, Dict, Optional, Any
from datetime import datetime
from database import DatabaseManager
from data_processor import WorkoutDataProcessor
import json
import os

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
async def create_workout(payload: dict[str, Any]):
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/payload_{timestamp}.json"
        
        # Write payload to file with pretty printing
        with open(filename, 'w') as f:
            json.dump(payload, f, indent=2)
        
        # Extract workout details for response
        workouts = payload.get('data', {}).get('workouts', [])
        workout_info = [
            {
                'name': workout.get('name', 'Unknown'),
                'start': workout.get('start'),
                'end': workout.get('end'),
                'activeEnergyBurned': workout.get('activeEnergyBurned', {}).get('qty', 0),
                'units': workout.get('activeEnergyBurned', {}).get('units', 'kcal')
            }
            for workout in workouts
        ]
            
        return {
            "status": "success",
            "message": f"Received {len(workouts)} workouts",
            "filename": filename,
            "workouts": workout_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/{workout_id}")
async def get_workout(workout_id: str):
    # Retrieve workout data from database
    pass 

app.include_router(router)