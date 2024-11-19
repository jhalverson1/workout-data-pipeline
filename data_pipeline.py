import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# File and Table Configuration
icloud_folder = Path(os.getenv("ICLOUD_FOLDER"))
processed_table_name = os.getenv("PROCESSED_TABLE_NAME", "processed_files")
workout_table_name = os.getenv("WORKOUT_TABLE_NAME", "workouts")
file_extension = os.getenv("FILE_EXTENSION", "csv")

# Create a database engine
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Function to mark a file as processed
def mark_file_as_processed(filename, create_time, upload_time, records_inserted):
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO processed_files (filename, file_create_datetime, file_upload_datetime, records_inserted)
            VALUES (:filename, :create_time, :upload_time, :records_inserted)
            """),
            {
                "filename": filename,
                "create_time": create_time,
                "upload_time": upload_time,
                "records_inserted": records_inserted
            }
        )

def is_file_processed(filename):
    query = "SELECT 1 FROM processed_files WHERE filename = :filename"
    with engine.connect() as conn:
        result = conn.execute(text(query), {"filename": filename}).fetchone()
    return result is not None  # Returns True if the file exists, False otherwise

# Function to insert workout data, avoiding duplicates
def insert_workouts(data):
    # Convert data types if necessary
    data['Start'] = pd.to_datetime(data['Start'])
    data['End'] = pd.to_datetime(data['End'])
    data['Active Energy (kcal)'] = pd.to_numeric(data['Active Energy (kcal)'], errors='coerce')
    data['Distance (mi)'] = pd.to_numeric(data['Distance (mi)'], errors='coerce')  # New line for distance
    
    # Convert duration from hh:mm:ss to total seconds as a float
    data['Duration'] = data['Duration'].apply(lambda x: sum(int(t) * 60**i for i, t in enumerate(reversed(x.split(':')))))

    
    inserted_count = 0
    with engine.begin() as conn:
        for _, row in data.iterrows():
            # Check for duplicates based on start_time and name
            duplicate_check = conn.execute(
                text("""
                SELECT 1 FROM workouts WHERE start_time = :start_time AND name = :name
                """),
                {"start_time": row['Start'], "name": row['Type']}
            ).fetchone()

            if not duplicate_check:
                # Insert the workout record if it's not a duplicate
                conn.execute(
                    text("""
                    INSERT INTO workouts (name, start_time, end_time, activeEnergyBurned, duration, distance)
                    VALUES (:name, :start_time, :end_time, :activeEnergyBurned, :duration, :distance)
                    """),
                    {
                        "name": row['Type'],
                        "start_time": row['Start'],
                        "end_time": row['End'],
                        "activeEnergyBurned": row['Active Energy (kcal)'],
                        "duration": row['Duration'],
                        "distance": row['Distance (mi)']  # New distance field
                    }
                )
                inserted_count += 1
    return inserted_count

# Main function to process only new files from the iCloud folder
def process_workout_files():
    # Initialize counters for files skipped, processed, and records inserted
    skipped_files_count = 0
    processed_files_count = 0
    total_records_inserted = 0

    for file in icloud_folder.glob(f"*.{file_extension}"):
        filename = file.name
        file_create_time = datetime.fromtimestamp(file.stat().st_ctime)
    
        # Check if the file is already in the processed_files table
        if is_file_processed(filename):
            skipped_files_count += 1
            continue

        file_upload_time = datetime.now()
        processed_files_count += 1  # Increment the processed files counter

        try:
            # Read the CSV file into a DataFrame
            data = pd.read_csv(file)

            # Insert workouts and track how many records were added
            records_inserted = insert_workouts(data)
            total_records_inserted += records_inserted  # Add to the total count

            # Mark the file as processed
            mark_file_as_processed(filename, file_create_time, file_upload_time, records_inserted)
        
        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    # Print a summary of the processing
    print(f"Total files skipped: {skipped_files_count}")
    print(f"Total files processed: {processed_files_count}")
    print(f"Total workouts inserted: {total_records_inserted}")

# Run the program
process_workout_files()