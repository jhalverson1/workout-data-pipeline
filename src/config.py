from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Google Configuration
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    GOOGLE_DRIVE_WORKOUTS_FOLDER_ID = os.getenv("GOOGLE_DRIVE_WORKOUTS_FOLDER_ID")
    
    # Gmail Configuration
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
    GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")
    
    # Application Configuration
    VALID_WORKOUT_TYPES = ["Outdoor Run"]
