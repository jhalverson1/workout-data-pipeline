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
        # Store workouts in database
        workouts = payload.get('data', {}).get('workouts', [])
        stored_workouts = []
        duplicate_count = 0
        
        for workout in workouts:
            success = db.store_workout(workout)
            if success:
                stored_workouts.append({
                    'type': workout.get('workoutActivityType', 'Unknown'),
                    'start': workout.get('start'),
                    'end': workout.get('end'),
                    'activeEnergyBurned': workout.get('activeEnergyBurned', {}).get('qty', 0),
                    'units': workout.get('activeEnergyBurned', {}).get('units', 'kcal')
                })
            else:
                duplicate_count += 1
        
        # Get total count of workouts in DB
        total_workouts = len(db.get_all_workouts())
        
        # Print statistics to terminal
        print("\n=== Workout Import Summary ===")
        print(f"Processed: {len(workouts)} workouts")
        print(f"Stored:    {len(stored_workouts)} new workouts")
        print(f"Skipped:   {duplicate_count} duplicates")
        print(f"Total DB:  {total_workouts} workouts")
        print("===========================\n")
            
        return {
            "status": "success",
            "message": f"Processed {len(workouts)} workouts",
            "stored": len(stored_workouts),
            "duplicates": duplicate_count,
            "total_in_db": total_workouts,
            "workouts": stored_workouts
        }
    except Exception as e:
        print(f"Error processing workouts: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/{workout_id}")
async def get_workout(workout_id: str):
    # Retrieve workout data from database
    pass 

app.include_router(router)