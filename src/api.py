"""
REST API Module for Workout Tracking Application

This module provides the FastAPI application and endpoints for receiving and
managing workout data.
"""

from fastapi import FastAPI, APIRouter
from typing import Dict, Any
from database import DatabaseManager
from email_service import EmailService
import pandas as pd
from google_services import GoogleServices
from config import Config
import os

app = FastAPI()
db = DatabaseManager()
google_services = GoogleServices()

router = APIRouter(prefix="/api/v1/workouts", tags=["workouts"])

def get_db_size():
    """Get database size in MB"""
    try:
        size_bytes = os.path.getsize(db.db_path)
        return round(size_bytes / (1024 * 1024), 2)  # Convert bytes to MB
    except:
        return 0

def update_google_sheets(workouts_df: pd.DataFrame) -> bool:
    """Update Google Sheets with the workout data"""
    try:
        google_services.update_sheet(workouts_df, Config.SPREADSHEET_ID)
        return True
    except Exception as e:
        print(f"Error updating Google Sheets: {e}")
        return False

@router.post("/")
async def create_workout(payload: dict[str, Any]):
    try:
        workouts = payload.get('data', {}).get('workouts', [])
        stored_workouts = []
        duplicate_count = 0
        
        for workout in workouts:
            success = db.store_workout(workout)
            if success:
                stored_workouts.append({
                    'type': workout.get('name', 'Unknown'),
                    'start': workout.get('start'),
                    'end': workout.get('end'),
                    'activeEnergyBurned': workout.get('activeEnergyBurned', {}).get('qty', 0),
                    'units': workout.get('activeEnergyBurned', {}).get('units', 'kcal')
                })
            else:
                duplicate_count += 1
        
        total_workouts = len(db.get_all_workouts())
        db_size = get_db_size()
        
        sheets_update_status = "Not attempted"
        if stored_workouts:
            workouts_df = db.get_all_workouts()
            if update_google_sheets(workouts_df):
                sheets_update_status = "Success"
            else:
                sheets_update_status = "Failed"
        
        summary = (
            "\n=== Workout Import Summary ===\n"
            f"Processed: {len(workouts)} workouts\n"
            f"Stored:    {len(stored_workouts)} new workouts\n"
            f"Skipped:   {duplicate_count} duplicates\n"
            f"Total DB:  {total_workouts} workouts\n"
            f"DB Size:   {db_size} MB\n"
            f"Sheets:    {sheets_update_status}\n"
            "===========================\n"
        )
        
        print(summary)
        EmailService.send_email(summary)
            
        return {
            "status": "success",
            "message": f"Processed {len(workouts)} workouts",
            "stored": len(stored_workouts),
            "duplicates": duplicate_count,
            "total_in_db": total_workouts,
            "db_size_mb": db_size,
            "sheets_update": sheets_update_status,
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

app.include_router(router)