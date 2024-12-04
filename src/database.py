"""
This module handles all database operations for storing workout data.
"""

import sqlite3
from typing import Dict, Any
import pandas as pd
from contextlib import contextmanager

class DatabaseManager:
    """
    Manages SQLite database operations for workout data.
    """
    
    def __init__(self, db_path: str = "workouts.db"):
        """
        Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self) -> None:
        """
        Initialize database by creating necessary tables if they don't exist.
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
            workout_data (Dict[str, Any]): Workout data to insert
            
        Returns:
            int: ID of the inserted record
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
            pd.DataFrame: DataFrame containing all workout records
        """
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM workouts ORDER BY start_time DESC", conn) 