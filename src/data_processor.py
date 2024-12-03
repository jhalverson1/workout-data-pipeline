"""
This module contains the WorkoutDataProcessor class, which processes workout data
from a pandas DataFrame, including converting data types, filtering, and calculating
additional metrics like pace.
"""

from typing import Optional
import pandas as pd
from config import Config

class WorkoutDataProcessor:
    """
    A class to process workout data from a pandas DataFrame.
    """

    @staticmethod
    def process_workout_data(data: pd.DataFrame) -> pd.DataFrame:
        """
        Processes workout data by converting data types, filtering valid workouts,
        and calculating pace.

        Args:
            data (pd.DataFrame): The workout data to process.

        Returns:
            pd.DataFrame: The processed workout data.
        """
        # Process workout data
        data["Start"] = pd.to_datetime(data["Start"])
        data["End"] = pd.to_datetime(data["End"])
        data["Active Energy (kcal)"] = pd.to_numeric(data["Active Energy (kcal)"], errors="coerce")
        data["Distance (mi)"] = pd.to_numeric(data["Distance (mi)"], errors="coerce")
        
        # Convert duration to seconds
        data["Duration"] = data["Duration"].apply(
            lambda x: sum(int(t) * 60**i for i, t in enumerate(reversed(x.split(":"))))
        )
        
        # Filter valid workouts
        data = data[data["Type"].isin(Config.VALID_WORKOUT_TYPES)].copy()
        
        # Calculate pace
        data["Pace (min/mi)"] = data.apply(
            lambda row: round(row["Duration"] / 60 / row["Distance (mi)"], 2)
            if row["Distance (mi)"] > 0
            else None,
            axis=1,
        )
        
        return data
