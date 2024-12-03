from typing import Tuple, List, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import pandas as pd
from config import Config

class GoogleServices:
    def __init__(self):
        self.drive_service, self.sheets_service = self._authenticate()
    
    def _authenticate(self) -> Tuple[object, object]:
        creds = Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        )
        return (
            build("drive", "v3", credentials=creds),
            build("sheets", "v4", credentials=creds)
        )
    
    def fetch_files(self, folder_id):
        """
        Fetch CSV files from the specified Google Drive folder.

        Args:
            folder_id (str): ID of the Google Drive folder to fetch files from.

        Returns:
            List of file metadata (name and ID) for CSV files in the folder.
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
            BytesIO object containing the file's content.
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
            data (DataFrame): The data to be written to Google Sheets.
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
