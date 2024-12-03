from typing import Optional
import pandas as pd
from config import Config

class WorkoutDataProcessor:
    @staticmethod
    def process_workout_data(data: pd.DataFrame) -> pd.DataFrame:
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
