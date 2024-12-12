import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google_services import GoogleServices
import mplcursors  # Add this import at the top with other imports
import matplotlib.dates

# Load environment variables
load_dotenv()

class WorkoutVisualizer:
    def __init__(self):
        self.google_services = GoogleServices()
        self.data = None
        
    def load_data(self, range_name):
        result = self.google_services.sheets_service.spreadsheets().values().get(
            spreadsheetId=os.getenv('SPREADSHEET_ID'),
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        self.data = pd.DataFrame(values[1:], columns=values[0])
        
        # Convert date strings to datetime (not date)
        self.data['start_time'] = pd.to_datetime(self.data['start_time'], utc=True)
        
        # Convert string numbers to float
        self.data['distance_qty'] = pd.to_numeric(self.data['distance_qty'])
        self.data['duration'] = pd.to_numeric(self.data['duration'])
        
        # Apply filters
        twelve_months_ago = pd.Timestamp.now(tz='UTC') - pd.DateOffset(months=12)
        self.data = self.data[
            (self.data['type'] == 'Outdoor Run') &
            (self.data['start_time'] >= twelve_months_ago) &
            (self.data['distance_qty'] > 1)
        ]
        
        # Calculate pace (minutes per mile)
        self.data['pace'] = (self.data['duration'] / 60) / self.data['distance_qty']
        
    def plot_distance_and_pace(self):
        # Create figure and axis objects with a single subplot
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot distance on primary y-axis
        color = 'tab:green'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Distance (mi)', color=color)
        line1 = ax1.plot(self.data['start_time'], self.data['distance_qty'], 
                        color=color, label='Distance')
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Create secondary y-axis and plot pace
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Pace (min/mi)', color=color)
        line2 = ax2.plot(self.data['start_time'], self.data['pace'], 
                        color=color, linestyle='--', label='Pace')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(6, 25)  # Set y-axis limits for pace
        
        # Add title and adjust layout
        plt.title('Distance vs Pace Over Time')
        fig.tight_layout()
        
        # Add legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        # Add interactive cursors
        cursor = mplcursors.cursor(lines, hover=True)
        
        @cursor.connect("add")
        def on_add(sel):
            x, y = sel.target
            # Convert matplotlib's float date to datetime
            x_datetime = pd.Timestamp(matplotlib.dates.num2date(x))
            
            # Find the closest date
            index = abs(self.data['start_time'] - x_datetime).argmin()
            
            # Format the date and values
            date = self.data['start_time'].iloc[index].strftime('%Y-%m-%d')
            distance = f"{self.data['distance_qty'].iloc[index]:.2f}"
            pace = f"{self.data['pace'].iloc[index]:.2f}"
            
            # Create tooltip text
            sel.annotation.set_text(
                f"Date: {date}\nDistance: {distance} mi\nPace: {pace} min/mi"
            )
        
        plt.show()

if __name__ == "__main__":
    visualizer = WorkoutVisualizer()
    visualizer.load_data('Sheet1!A:T')  # Adjust range to include duration column
    visualizer.plot_distance_and_pace() 