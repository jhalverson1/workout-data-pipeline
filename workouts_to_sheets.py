import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import StringIO
import sys

# Load environment variables from .env file
load_dotenv()

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Add your Google Sheet ID to .env
SERVICE_ACCOUNT_FILE = "service_account.json"  # Path to your JSON key file

# Gmail Config
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# File Configuration
icloud_folder = Path(os.getenv("ICLOUD_FOLDER"))
file_extension = os.getenv("FILE_EXTENSION", "csv")

def get_sheets_service():
    """
    Authenticates using the service account JSON file and returns a Sheets API service instance.
    """
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    return service


def update_google_sheets_with_data(data):
    """
    Clears the Google Sheets file and updates it with the given data.

    Args:
        data (DataFrame): The data to be written to Google Sheets.
    """
    for col in data.select_dtypes(include=["datetime", "datetimetz"]):
        data[col] = data[col].astype(str)

    data = data.fillna("")
    sheet_data = [data.columns.tolist()] + data.values.tolist()

    service = get_sheets_service()
    sheet = service.spreadsheets()

    sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
    print("Google Sheet cleared.")

    sheet.values().update(
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
    sender_email = GMAIL_ADDRESS  # Replace with your Gmail address
    receiver_email = GMAIL_ADDRESS  # Replace with your Gmail address
    password = GMAIL_PASSWORD  # Replace with your Gmail app password

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


def process_workout_files_direct_to_sheets():
    """
    Processes all workout files from the specified iCloud folder:
    - Reads workout data from CSV files.
    - Calculates 'Pace' (minutes per mile) for 'Outdoor Walk' and 'Outdoor Run' workouts.
    - Writes the combined data directly to Google Sheets.
    """
    total_files_processed = 0
    combined_data = pd.DataFrame()

    for file in icloud_folder.glob(f"*.{file_extension}"):
        try:
            data = pd.read_csv(file)
            data["Start"] = pd.to_datetime(data["Start"])
            data["End"] = pd.to_datetime(data["End"])
            data["Active Energy (kcal)"] = pd.to_numeric(
                data["Active Energy (kcal)"], errors="coerce"
            )
            data["Distance (mi)"] = pd.to_numeric(data["Distance (mi)"], errors="coerce")
            data["Duration"] = data["Duration"].apply(
                lambda x: sum(
                    int(t) * 60**i for i, t in enumerate(reversed(x.split(":")))
                )
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
            print(f"Error processing file {file.name}: {e}")

    if not combined_data.empty:
        update_google_sheets_with_data(combined_data)

    print(f"Total files processed: {total_files_processed}")


if __name__ == "__main__":
    # Capture program output
    original_stdout = sys.stdout
    program_output = StringIO()
    sys.stdout = program_output

    try:
        process_workout_files_direct_to_sheets()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sys.stdout = original_stdout
        output = program_output.getvalue()
        program_output.close()
        send_email(output)