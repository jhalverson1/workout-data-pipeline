"""
Database Module for Workout Tracking Application

This module handles all database operations for storing workout data. It provides
a DatabaseManager class that abstracts SQLite operations and provides methods for
storing and retrieving workout information.

The module uses SQLite as the database backend and includes:
- Connection management using context managers
- Table creation and initialization
- CRUD operations for workout data
- Pandas DataFrame integration for data retrieval

Example:
    db = DatabaseManager()
    workout_data = {
        "start_time": "2024-03-14T10:00:00",
        "end_time": "2024-03-14T11:00:00",
        "type": "Outdoor Run",
        "duration": 3600,
        "distance_mi": 6.2,
        "active_energy_kcal": 800,
        "pace_min_mi": 9.67
    }
    db.insert_workout(workout_data)
"""

import sqlite3
from typing import Dict, Any
import pandas as pd
from contextlib import contextmanager

class DatabaseManager:
    """
    Manages SQLite database operations for workout data.
    
    This class provides an interface for all database operations, including:
    - Database initialization
    - Connection management
    - Workout data insertion
    - Workout data retrieval
    
    Attributes:
        db_path (str): Path to the SQLite database file
    """
    
    def __init__(self, db_path: str = "workouts.db"):
        """
        Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to SQLite database file. Defaults to "workouts.db"
                          in the current directory.
        """
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Provides a safe way to handle database connections with automatic
        closing after usage.
        
        Yields:
            sqlite3.Connection: Database connection object
        
        Example:
            with db.get_connection() as conn:
                conn.execute("SELECT * FROM workouts")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self) -> None:
        """
        Initialize database by creating necessary tables if they don't exist.
        
        Creates the workouts table with the following schema:
        - id: Primary key
        - start_time: Workout start timestamp
        - end_time: Workout end timestamp
        - type: Workout type (e.g., "Outdoor Run")
        - duration: Duration in seconds
        - distance_mi: Distance in miles
        - active_energy_kcal: Calories burned
        - pace_min_mi: Pace in minutes per mile
        - created_at: Record creation timestamp
        """
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    type TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    distance_mi REAL,
                    active_energy_kcal REAL,
                    pace_min_mi REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(start_time, type)
                )
            """)
            conn.commit()
    
    def insert_workout(self, workout_data: Dict[str, Any]) -> int:
        """
        Insert a new workout record into the database.
        
        Args:
            workout_data (Dict[str, Any]): Dictionary containing workout data with keys:
                - start_time: Workout start timestamp
                - end_time: Workout end timestamp
                - type: Workout type
                - duration: Duration in seconds
                - distance_mi: Distance in miles (optional)
                - active_energy_kcal: Calories burned (optional)
                - pace_min_mi: Pace in minutes per mile (optional)
            
        Returns:
            int: ID of the inserted record
            
        Raises:
            sqlite3.IntegrityError: If a workout with the same start_time and type exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workouts (
                    start_time, end_time, type, duration,
                    distance_mi, active_energy_kcal, pace_min_mi
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                workout_data["start_time"],
                workout_data["end_time"],
                workout_data["type"],
                workout_data["duration"],
                workout_data.get("distance_mi"),
                workout_data.get("active_energy_kcal"),
                workout_data.get("pace_min_mi")
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_workouts(self) -> pd.DataFrame:
        """
        Retrieve all workouts from the database.
        
        Returns:
            pd.DataFrame: DataFrame containing all workout records, sorted by
                         start_time in descending order (most recent first)
        """
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM workouts ORDER BY start_time DESC", conn) 