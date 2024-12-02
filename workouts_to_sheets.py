import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import StringIO
import sys
import argparse

# Load environment variables from .env file
load_dotenv()

# Google Sheets and Drive Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Add your Google Sheet ID to .env
SERVICE_ACCOUNT_FILE = "service_account.json"  # Path to your JSON key file
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # Add your Google Drive folder ID to .env

# Gmail Config
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")


def authenticate_google_services():
    """
    Authenticate using the service account JSON file and return Google Drive and Sheets API service instances.
    """
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
    )
    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return drive_service, sheets_service


def fetch_files_from_drive(drive_service, folder_id):
    """
    Fetch CSV files from the specified Google Drive folder.

    Args:
        drive_service: Authenticated Google Drive API service instance.
        folder_id (str): ID of the Google Drive folder to fetch files from.

    Returns:
        List of file metadata (name and ID) for CSV files in the folder.
    """
    query = f"'{folder_id}' in parents and mimeType='text/csv'"
    files = []
    page_token = None

    while True:
        response = drive_service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name)",
            pageToken=page_token
        ).execute()

        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken", None)

        if not page_token:
            break

    print(f"Total files fetched: {len(files)}")  # Debugging
    return files


def download_file(drive_service, file_id):
    """
    Download a file from Google Drive.

    Args:
        drive_service: Authenticated Google Drive API service instance.
        file_id (str): ID of the file to download.

    Returns:
        BytesIO object containing the file's content.
    """
    from googleapiclient.http import MediaIoBaseDownload

    request = drive_service.files().get_media(fileId=file_id)
    file_stream = BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    return file_stream


def update_google_sheets_with_data(sheets_service, data):
    """
    Clears the Google Sheets file and updates it with the given data.

    Args:
        sheets_service: Authenticated Google Sheets API service instance.
        data (DataFrame): The data to be written to Google Sheets.
    """
    # Convert all datetime columns to strings
    for col in data.select_dtypes(include=["datetime", "datetimetz"]):
        data[col] = data[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Replace NaN or None values with empty strings to avoid JSON errors
    data = data.fillna("")

    # Clear the Google Sheet content
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range="Sheet1"
    ).execute()

    print("Google Sheet cleared.")

    # Prepare data to append (include column names)
    sheet_data = [data.columns.tolist()] + data.values.tolist()

    # Update the Google Sheet by overwriting existing data
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": sheet_data},
    ).execute()

    print(f"Google Sheet updated with {len(data)} rows.")


def send_email(program_output):
    """
    Sends an email containing the full output of the program.
    """
    sender_email = GMAIL_ADDRESS
    receiver_email = GMAIL_ADDRESS
    password = GMAIL_PASSWORD

    subject = "Workout Data Processing Completed"
    body = f"The script has completed processing. Here is the output:\n\n{program_output}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")


def process_workout_files_from_drive():
    """
    Processes all workout files from the specified Google Drive folder.
    Clears the existing Google Sheets file and repopulates it with all data.
    """
    drive_service, sheets_service = authenticate_google_services()
    files = fetch_files_from_drive(drive_service, GOOGLE_DRIVE_FOLDER_ID)
    print(f"Found {len(files)} files in the folder.")

    if not files:
        print("No files found in the specified Google Drive folder.")
        return

    combined_data = pd.DataFrame()
    total_files_processed = 0

    for file in files:
        try:
            print(f"Processing file: {file['name']}")
            file_stream = download_file(drive_service, file["id"])
            data = pd.read_csv(file_stream)

            # Preprocess workout data
            data["Start"] = pd.to_datetime(data["Start"])
            data["End"] = pd.to_datetime(data["End"])
            data["Active Energy (kcal)"] = pd.to_numeric(data["Active Energy (kcal)"], errors="coerce")
            data["Distance (mi)"] = pd.to_numeric(data["Distance (mi)"], errors="coerce")
            data["Duration"] = data["Duration"].apply(
                lambda x: sum(int(t) * 60**i for i, t in enumerate(reversed(x.split(":"))))
            )

            valid_workouts = ["Outdoor Run"]
            data = data[data["Type"].isin(valid_workouts)]

            data["Pace (min/mi)"] = data.apply(
                lambda row: round(row["Duration"] / 60 / row["Distance (mi)"], 2)
                if row["Distance (mi)"] > 0
                else None,
                axis=1,
            )

            combined_data = pd.concat([combined_data, data], ignore_index=True)
            total_files_processed += 1

        except Exception as e:
            print(f"Error processing file {file['name']}: {e}")

    # Deduplicate combined data
    if not combined_data.empty:
        print("Deduplicating data...")
        combined_data = combined_data.drop_duplicates(subset=["Start", "Type"])
        update_google_sheets_with_data(sheets_service, combined_data)

    # Print summary
    print(f"Total files processed: {total_files_processed}")


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Process workout files and update Google Sheets.")
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send the program output via email. If not specified, the output will be printed to the terminal."
    )
    args = parser.parse_args()

    # Capture program output
    original_stdout = sys.stdout
    program_output = StringIO()
    sys.stdout = program_output
    try:
        process_workout_files_from_drive()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sys.stdout = original_stdout
        output = program_output.getvalue()
        program_output.close()

        # Decide whether to send email or print output
        if args.send_email:
            send_email(output)
        else:
            print("Program Output:")
            print(output)