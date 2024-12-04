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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import DatabaseManager
from data_processor import WorkoutDataProcessor

app = FastAPI(
    title="Workout Tracking API",
    description="API for receiving and storing workout data",
    version="1.0.0"
)
db = DatabaseManager()
processor = WorkoutDataProcessor()

class WorkoutData(BaseModel):
    """
    Pydantic model for workout data validation.
    
    Attributes:
        start_time (datetime): Start time of the workout
        end_time (datetime): End time of the workout
        type (str): Type of workout (e.g., "Outdoor Run")
        duration (str): Duration in format "HH:MM:SS"
        distance_mi (float, optional): Distance in miles
        active_energy_kcal (float, optional): Calories burned
    """
    start_time: datetime
    end_time: datetime
    type: str
    duration: str  # Format: "HH:MM:SS"
    distance_mi: Optional[float] = None
    active_energy_kcal: Optional[float] = None

@app.post("/workouts", response_model=dict)
async def create_workout(workout: WorkoutData):
    """
    Create a new workout record.
    
    Receives workout data, processes it, and stores it in the database.
    Calculates additional metrics like pace before storage.
    
    Args:
        workout (WorkoutData): Validated workout data
        
    Returns:
        dict: Message confirming creation and the ID of the new record
        
    Raises:
        HTTPException: If data processing or storage fails
    """
    try:
        # Convert duration string to seconds
        duration_seconds = sum(
            int(t) * 60**i for i, t in enumerate(reversed(workout.duration.split(":")))
        )
        
        # Calculate pace if distance is available
        pace_min_mi = None
        if workout.distance_mi and workout.distance_mi > 0:
            pace_min_mi = round(duration_seconds / 60 / workout.distance_mi, 2)
        
        # Prepare workout data for database
        workout_data = {
            "start_time": workout.start_time,
            "end_time": workout.end_time,
            "type": workout.type,
            "duration": duration_seconds,
            "distance_mi": workout.distance_mi,
            "active_energy_kcal": workout.active_energy_kcal,
            "pace_min_mi": pace_min_mi
        }
        
        workout_id = db.insert_workout(workout_data)
        return {"message": "Workout created successfully", "id": workout_id}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workouts")
async def get_workouts():
    """
    Retrieve all workout records.
    
    Returns:
        list: List of all workout records as dictionaries
        
    Raises:
        HTTPException: If database retrieval fails
    """
    try:
        workouts = db.get_all_workouts()
        return workouts.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 