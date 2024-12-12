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
from email_service import EmailService

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

def get_db_size():
    """Get database size in MB"""
    try:
        size_bytes = os.path.getsize(db.db_path)
        return round(size_bytes / (1024 * 1024), 2)  # Convert bytes to MB
    except:
        return 0

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
        
        # Get statistics
        total_workouts = len(db.get_all_workouts())
        db_size = get_db_size()
        
        # Create summary message
        summary = (
            "\n=== Workout Import Summary ===\n"
            f"Processed: {len(workouts)} workouts\n"
            f"Stored:    {len(stored_workouts)} new workouts\n"
            f"Skipped:   {duplicate_count} duplicates\n"
            f"Total DB:  {total_workouts} workouts\n"
            f"DB Size:   {db_size} MB\n"
            "===========================\n"
        )
        
        # Print to terminal
        print(summary)
        
        # Send email
        EmailService.send_email(summary)
            
        return {
            "status": "success",
            "message": f"Processed {len(workouts)} workouts",
            "stored": len(stored_workouts),
            "duplicates": duplicate_count,
            "total_in_db": total_workouts,
            "db_size_mb": db_size,
            "workouts": stored_workouts
        }
    except Exception as e:
        error_msg = f"Error processing workouts: {e}"
        print(error_msg)
        EmailService.send_email(error_msg)
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/{workout_id}")
async def get_workout(workout_id: str):
    # Retrieve workout data from database
    pass 

app.include_router(router)