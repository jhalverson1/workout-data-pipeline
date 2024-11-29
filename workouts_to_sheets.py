import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Load environment variables from .env file
load_dotenv()

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Add your Google Sheet ID to .env
SERVICE_ACCOUNT_FILE = "service_account.json"  # Path to your JSON key file

# File Configuration
icloud_folder = Path(os.getenv("ICLOUD_FOLDER"))
file_extension = os.getenv("FILE_EXTENSION", "csv")

# Function to authenticate and connect to Google Sheets
def get_sheets_service():
    """
    Authenticates using the service account JSON file and returns a Sheets API service instance.
    """
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=creds)
    return service

# Function to update Google Sheets with workout data
def update_google_sheets_with_data(data):
    """
    Updates the Google Sheets file with the given data.

    Args:
        data (DataFrame): The data to be written to Google Sheets.
    """
    # Convert all Timestamp columns to strings for compatibility with JSON
    for col in data.select_dtypes(include=["datetime", "datetimetz"]):
        data[col] = data[col].astype(str)

    # Replace NaN or None values with empty strings to avoid JSON errors
    data = data.fillna("")

    # Convert the DataFrame to a list of lists (suitable for Google Sheets API)
    sheet_data = [data.columns.tolist()] + data.values.tolist()

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

    print(f"Google Sheet updated with {len(data)} rows.")

# Function to process workout files and write directly to Google Sheets
def process_workout_files_direct_to_sheets():
    """
    Processes all workout files from the specified iCloud folder:
    - Reads workout data from CSV files.
    - Writes the combined data directly to Google Sheets.
    """
    total_files_processed = 0
    combined_data = pd.DataFrame()

    for file in icloud_folder.glob(f"*.{file_extension}"):
        try:
            # Load workout data from CSV
            data = pd.read_csv(file)

            # Preprocess data for consistency
            data['Start'] = pd.to_datetime(data['Start'])
            data['End'] = pd.to_datetime(data['End'])
            data['Active Energy (kcal)'] = pd.to_numeric(data['Active Energy (kcal)'], errors='coerce')
            data['Distance (mi)'] = pd.to_numeric(data['Distance (mi)'], errors='coerce')
            data['Duration'] = data['Duration'].apply(lambda x: sum(int(t) * 60**i for i, t in enumerate(reversed(x.split(':')))))

            # Combine data from all files
            combined_data = pd.concat([combined_data, data], ignore_index=True)
            total_files_processed += 1
        except Exception as e:
            print(f"Error processing file {file.name}: {e}")

    # Update Google Sheets with combined data
    if not combined_data.empty:
        update_google_sheets_with_data(combined_data)

    # Summary of processing
    print(f"Total files processed: {total_files_processed}")

# Run the script
if __name__ == "__main__":
    process_workout_files_direct_to_sheets()