from typing import Optional
import pandas as pd
import sys
from io import StringIO
import argparse
from google_services import GoogleServices
from data_processor import WorkoutDataProcessor
from email_service import EmailService
from config import Config

class WorkoutProcessor:
    def __init__(self):
        self.google_services = GoogleServices()
        self.data_processor = WorkoutDataProcessor()
    
    def process_files(self) -> None:
        files = self.google_services.fetch_files(folder_id=Config.GOOGLE_DRIVE_WORKOUTS_FOLDER_ID)
        if not files:
            print("No files found in the specified Google Drive folder.")
            return

        combined_data = pd.DataFrame()
        total_files_processed = 0

        for file in files:
            try:
                print(f"Processing file: {file['name']}")
                file_stream = self.google_services.download_file(file["id"])
                data = pd.read_csv(file_stream)
                
                processed_data = self.data_processor.process_workout_data(data)
                combined_data = pd.concat([combined_data, processed_data], ignore_index=True)
                total_files_processed += 1
                
            except Exception as e:
                print(f"Error processing file {file['name']}: {e}")

        if not combined_data.empty:
            print("Deduplicating data...")
            combined_data = combined_data.drop_duplicates(subset=["Start", "Type"])
            self.google_services.update_sheet(combined_data, Config.SPREADSHEET_ID)

        print(f"Total files processed: {total_files_processed}")

def main():
    parser = argparse.ArgumentParser(description="Process workout files and update Google Sheets.")
    parser.add_argument("--send-email", action="store_true",
                       help="Send the program output via email.")
    args = parser.parse_args()

    program_output = StringIO()
    sys.stdout = program_output
    
    try:
        processor = WorkoutProcessor()
        processor.process_files()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sys.stdout = sys.__stdout__
        output = program_output.getvalue()
        program_output.close()

        if args.send_email:
            EmailService.send_email(output)
        else:
            print("Program Output:")
            print(output)

if __name__ == "__main__":
    main()