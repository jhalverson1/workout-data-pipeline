"""
This module provides the REST API endpoints for receiving workout data.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import DatabaseManager
from data_processor import WorkoutDataProcessor

app = FastAPI()
db = DatabaseManager()
processor = WorkoutDataProcessor()

class WorkoutData(BaseModel):
    """
    Pydantic model for workout data validation.
    """
    start_time: datetime
    end_time: datetime
    type: str
    duration: str  # Format: "HH:MM:SS"
    distance_mi: Optional[float] = None
    active_energy_kcal: Optional[float] = None

@app.post("/workouts")
async def create_workout(workout: WorkoutData):
    """
    Endpoint to receive and store workout data.
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
    Endpoint to retrieve all workouts.
    """
    try:
        workouts = db.get_all_workouts()
        return workouts.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 