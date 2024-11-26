import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

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

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Add your Google Sheet ID to .env
SERVICE_ACCOUNT_FILE = "service_account.json"  # Path to your JSON key file

# Create a database engine
# This is the connection object used to interact with the PostgreSQL database
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Function to authenticate and connect to Google Sheets
def get_sheets_service():
    """
    Authenticates using the service account JSON file and returns a Sheets API service instance.
    """
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=creds)
    return service

# Function to update Google Sheets with workout data
def update_google_sheets():
    """
    Fetches all workout data from the database and updates a Google Sheets file.

    The data is written to the specified Google Sheets file starting at cell A1.
    """
    # Query to fetch all workout data from the database
    query = f"SELECT * FROM {workout_table_name} ORDER BY start_time;"
    workout_data = pd.read_sql(query, engine)

    # Convert all Timestamp columns to strings for compatibility with JSON
    for col in workout_data.select_dtypes(include=["datetime", "datetimetz"]):
        workout_data[col] = workout_data[col].astype(str)

    # Replace NaN or None values with empty strings to avoid JSON errors
    workout_data = workout_data.fillna("")

    # Convert the DataFrame to a list of lists (suitable for Google Sheets API)
    sheet_data = [workout_data.columns.tolist()] + workout_data.values.tolist()

    # Authenticate and connect to Google Sheets
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Update the Google Sheet by overwriting existing data
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": sheet_data}
    ).execute()

    print(f"Google Sheet updated with {len(workout_data)} rows.")

# Function to mark a file as processed in the processed_files table
def mark_file_as_processed(filename, create_time, upload_time, records_inserted):
    """
    Inserts a record into the processed_files table to track which files have been processed.

    Args:
        filename (str): Name of the file processed.
        create_time (datetime): File creation timestamp.
        upload_time (datetime): Timestamp when the file was processed.
        records_inserted (int): Number of records inserted from the file.
    """
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

# Function to check if a file has already been processed
def is_file_processed(filename):
    """
    Checks if the specified file has already been processed.

    Args:
        filename (str): Name of the file to check.

    Returns:
        bool: True if the file has been processed, False otherwise.
    """
    query = "SELECT 1 FROM processed_files WHERE filename = :filename"
    with engine.connect() as conn:
        result = conn.execute(text(query), {"filename": filename}).fetchone()
    return result is not None

# Function to insert workout data into the workouts table, avoiding duplicates
def insert_workouts(data):
    """
    Inserts workout data into the database. Skips duplicates based on start_time and name.

    Args:
        data (DataFrame): Pandas DataFrame containing workout data.

    Returns:
        int: Number of records successfully inserted.
    """
    # Preprocess data
    data['Start'] = pd.to_datetime(data['Start'])
    data['End'] = pd.to_datetime(data['End'])
    data['Active Energy (kcal)'] = pd.to_numeric(data['Active Energy (kcal)'], errors='coerce')
    data['Distance (mi)'] = pd.to_numeric(data['Distance (mi)'], errors='coerce')
    data['Duration'] = data['Duration'].apply(lambda x: sum(int(t) * 60**i for i, t in enumerate(reversed(x.split(':')))))

    inserted_count = 0
    with engine.begin() as conn:
        for _, row in data.iterrows():
            # Check for duplicates
            duplicate_check = conn.execute(
                text("""
                SELECT 1 FROM workouts WHERE start_time = :start_time AND name = :name
                """),
                {"start_time": row['Start'], "name": row['Type']}
            ).fetchone()

            if not duplicate_check:
                # Insert workout record
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
                        "distance": row['Distance (mi)']
                    }
                )
                inserted_count += 1
    return inserted_count

# Main function to process workout files and update Google Sheets
def process_workout_files():
    """
    Processes all unprocessed workout files from the specified iCloud folder:
    - Inserts workout data into the database.
    - Updates Google Sheets with the latest data.
    - Tracks processed files in the database.
    """
    skipped_files_count = 0
    processed_files_count = 0
    total_records_inserted = 0

    for file in icloud_folder.glob(f"*.{file_extension}"):
        filename = file.name
        file_create_time = datetime.fromtimestamp(file.stat().st_ctime)
        
        # Skip files already processed
        if is_file_processed(filename):
            skipped_files_count += 1
            continue

        file_upload_time = datetime.now()
        processed_files_count += 1

        try:
            # Load workout data from CSV
            data = pd.read_csv(file)

            # Insert data into database
            records_inserted = insert_workouts(data)
            total_records_inserted += records_inserted

            # Mark file as processed
            mark_file_as_processed(filename, file_create_time, file_upload_time, records_inserted)
        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    # Summary of processing
    print(f"Total files skipped: {skipped_files_count}")
    print(f"Total files processed: {processed_files_count}")
    print(f"Total workouts inserted: {total_records_inserted}")

    # Update Google Sheets with latest data
    update_google_sheets()

# Run the pipeline
process_workout_files()