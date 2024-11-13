import pandas as pd
from sqlalchemy import create_engine
import os
import matplotlib.pyplot as plt

# Load environment variables from .env file if necessary
from dotenv import load_dotenv
load_dotenv()

# Database Configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Create a database engine
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Query to get running workout data
query = """
SELECT * FROM workouts
WHERE name = 'Outdoor Run'
ORDER BY start_time;
"""

# Load the data into a DataFrame
running_data = pd.read_sql(query, engine)


# Calculate pace (e.g., minutes per mile if distance is available)
running_data['pace'] = (running_data['duration'] / 60) / running_data['distance']  # adjust for units

plt.figure(figsize=(10, 5))
plt.plot(running_data['start_time'], running_data['pace'], marker='o')
plt.title('Pace Over Time')
plt.xlabel('Date')
plt.ylabel('Pace (min/mile)')
plt.show()

# Calculate cumulative distance
running_data['cumulative_distance'] = running_data['distance'].cumsum()

plt.figure(figsize=(10, 5))
plt.plot(running_data['start_time'], running_data['cumulative_distance'], marker='o', color='orange')
plt.title('Cumulative Distance Run Over Time')
plt.xlabel('Date')
plt.ylabel('Total Distance (miles)')
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(running_data['start_time'], running_data['activeenergyburned'], marker='o', color='green')
plt.title('Energy Burned Over Time')
plt.xlabel('Date')
plt.ylabel('Energy Burned (kcal)')
plt.show()