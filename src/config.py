"""Application configuration."""

from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Google Configuration
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    
    # Gmail Configuration
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
    GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")
    
    # Application Configuration
    DATABASE_PATH = os.getenv("DATABASE_PATH", "workouts.db")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))