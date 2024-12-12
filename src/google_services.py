"""
This module provides the GoogleServices class, which handles authentication
and operations with Google Drive and Google Sheets, such as fetching files,
downloading files, and updating sheets.
"""

from typing import Tuple, List, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import pandas as pd
from config import Config

class GoogleServices:
    """
    A class to interact with Google Drive and Google Sheets services.
    """

    def __init__(self):
        """
        Initializes the GoogleServices class and authenticates the user.
        """
        creds = Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        )
        self.sheets_service = build("sheets", "v4", credentials=creds)
    
    def fetch_files(self, folder_id: str) -> List[Dict[str, str]]:
        """
        Fetch CSV files from the specified Google Drive folder.

        Args:
            folder_id (str): ID of the Google Drive folder to fetch files from.

        Returns:
            List[Dict[str, str]]: List of file metadata (name and ID) for CSV files in the folder.
        """
        query = f"'{folder_id}' in parents and mimeType='text/csv'"
        files = []
        page_token = None

        while True:
            response = self.drive_service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()

            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)

            if not page_token:
                break

        return files
    
    def download_file(self, file_id: str) -> BytesIO:
        """
        Download a file from Google Drive.

        Args:
            file_id (str): ID of the file to download.

        Returns:
            BytesIO: BytesIO object containing the file's content.
        """
        request = self.drive_service.files().get_media(fileId=file_id)
        file_stream = BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file_stream.seek(0)
        return file_stream
    
    def update_sheet(self, data: pd.DataFrame, spreadsheet_id: str) -> None:
        """
        Clears the Google Sheets file and updates it with the given data.

        Args:
            data (pd.DataFrame): The data to be written to Google Sheets.
            spreadsheet_id (str): The ID of the Google Sheets file to update.
        """
        # Convert all datetime columns to strings
        for col in data.select_dtypes(include=["datetime", "datetimetz"]):
            data[col] = data[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Replace NaN or None values with empty strings to avoid JSON errors
        data = data.fillna("")

        # Clear the Google Sheet content
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range="Sheet1"
        ).execute()

        print("Google Sheet cleared.")

        # Prepare data to append (include column names)
        sheet_data = [data.columns.tolist()] + data.values.tolist()

        # Update the Google Sheet by overwriting existing data
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": sheet_data},
        ).execute()

        print(f"Google Sheet updated with {len(data)} rows.")
