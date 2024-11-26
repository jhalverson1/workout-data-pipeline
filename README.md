# Apple Health Data Pipeline and Visualization

This project processes workout data from Apple Health, uploads it to a PostgreSQL database, exports it to Google Sheets, and visualizes trends in Looker Studio.

---

## Features
- Automatically processes and inserts workout data from CSV files into a PostgreSQL database.
- Syncs processed data to a Google Sheets file.
- Visualizes performance trends using Looker Studio.

---

## Setup Guide

### 1. Install Dependencies
Ensure you have Python 3.9 and PostgreSQL installed. Then, set up your virtual environment and install required packages:

```bash
# Navigate to the project folder
cd workout_data_pipeline

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

2. Configure Environment Variables

Create a .env file in the workout_data_pipeline directory and add the following variables:

DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=workout_data
ICLOUD_FOLDER=/path/to/your/icloud/folder
SPREADSHEET_ID=your_google_sheet_id

3. Prepare Your Database

	1.	Create a PostgreSQL database named workout_data.
	2.	Run the following SQL command to set up the workouts and processed_files tables:

-- Create workouts table
CREATE TABLE workouts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    activeEnergyBurned FLOAT,
    duration FLOAT,
    distance FLOAT
);

-- Create processed_files table
CREATE TABLE processed_files (
    id SERIAL PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    file_create_datetime TIMESTAMP NOT NULL,
    file_upload_datetime TIMESTAMP NOT NULL,
    records_inserted INTEGER NOT NULL
);

How to Run the Data Pipeline

Step 1: Process and Insert Data

Run the data_pipeline.py script to process CSV files from your iCloud folder, insert the data into PostgreSQL, and update Google Sheets.

python3 data_pipeline.py

	•	Skipped Files: Files already processed will be skipped.
	•	Google Sheets: The Google Sheets file will be updated with the latest data.

Step 2: Visualize Data in Looker Studio

	1.	Open Looker Studio.
	2.	Connect your Google Sheets file as a data source.
	3.	Use pre-configured visualizations (e.g., pace over time, cumulative distance) or create your own to analyze Outdoor Run performance trends.

Troubleshooting

Common Issues

	1.	service_account.json is missing or misconfigured:
	•	Ensure your Google Cloud service account JSON file is in the project directory and not tracked by Git (added to .gitignore).
	2.	Google Sheets Update Fails:
	•	Ensure the SPREADSHEET_ID in your .env file matches the ID of your Google Sheets file.
	•	Confirm the service account has Editor access to the Google Sheet.
	3.	No Data in Visualizations:
	•	Verify the database contains relevant Outdoor Run data.
	•	Check Looker Studio filters for correct configurations.

Folder Structure

workout_data_pipeline/
├── data_pipeline.py       # Main script to process data and sync with Google Sheets
├── requirements.txt       # Python dependencies
├── .gitignore             # Ignored files (e.g., service_account.json)
├── venv/                  # Virtual environment
└── README.md              # This file

Future Improvements

	•	Automate the pipeline using cron jobs or task schedulers.
	•	Add more data visualizations (e.g., weekly summaries, workout heatmaps).
	•	Securely handle credentials with encrypted secrets management.
