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
from datetime import datetime
import json

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
        self.init_db()
    
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
    
    def init_db(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create workouts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration FLOAT,
                    location TEXT,
                    distance_qty FLOAT,
                    distance_units TEXT,
                    elevation_up_qty FLOAT,
                    elevation_up_units TEXT,
                    energy_burned_qty FLOAT,
                    energy_burned_units TEXT,
                    temperature_qty FLOAT,
                    temperature_units TEXT,
                    humidity_qty FLOAT,
                    humidity_units TEXT,
                    intensity_qty FLOAT,
                    intensity_units TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create route_points table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id TEXT,
                    timestamp TIMESTAMP,
                    latitude FLOAT,
                    longitude FLOAT,
                    altitude FLOAT,
                    speed FLOAT,
                    speed_accuracy FLOAT,
                    course FLOAT,
                    course_accuracy FLOAT,
                    horizontal_accuracy FLOAT,
                    vertical_accuracy FLOAT,
                    FOREIGN KEY (workout_id) REFERENCES workouts (id)
                )
            """)
            
            conn.commit()
    
    def store_workout(self, workout: Dict[str, Any]) -> bool:
        """Store a single workout and its route points."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert workout data
                cursor.execute("""
                    INSERT INTO workouts (
                        id, name, start_time, end_time, duration, location,
                        distance_qty, distance_units,
                        elevation_up_qty, elevation_up_units,
                        energy_burned_qty, energy_burned_units,
                        temperature_qty, temperature_units,
                        humidity_qty, humidity_units,
                        intensity_qty, intensity_units,
                        metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workout['id'],
                    workout['name'],
                    workout['start'],
                    workout['end'],
                    workout['duration'],
                    workout['location'],
                    workout.get('distance', {}).get('qty'),
                    workout.get('distance', {}).get('units'),
                    workout.get('elevationUp', {}).get('qty'),
                    workout.get('elevationUp', {}).get('units'),
                    workout.get('activeEnergyBurned', {}).get('qty'),
                    workout.get('activeEnergyBurned', {}).get('units'),
                    workout.get('temperature', {}).get('qty'),
                    workout.get('temperature', {}).get('units'),
                    workout.get('humidity', {}).get('qty'),
                    workout.get('humidity', {}).get('units'),
                    workout.get('intensity', {}).get('qty'),
                    workout.get('intensity', {}).get('units'),
                    json.dumps(workout.get('metadata', {}))
                ))
                
                # Insert route points
                for point in workout.get('route', []):
                    cursor.execute("""
                        INSERT INTO route_points (
                            workout_id, timestamp, latitude, longitude,
                            altitude, speed, speed_accuracy, course,
                            course_accuracy, horizontal_accuracy, vertical_accuracy
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        workout['id'],
                        point['timestamp'],
                        point['latitude'],
                        point['longitude'],
                        point['altitude'],
                        point['speed'],
                        point['speedAccuracy'],
                        point['course'],
                        point['courseAccuracy'],
                        point['horizontalAccuracy'],
                        point['verticalAccuracy']
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error storing workout: {e}")
            return False
    
    def get_workout(self, workout_id: str) -> Dict[str, Any]:
        """Retrieve a workout and its route points by ID."""
        # Implementation for retrieving workout data
        pass
    
    def get_all_workouts(self) -> pd.DataFrame:
        """
        Retrieve all workouts from the database.
        
        Returns:
            pd.DataFrame: DataFrame containing all workout records, sorted by
                         start_time in descending order (most recent first)
        """
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM workouts ORDER BY start_time DESC", conn) 