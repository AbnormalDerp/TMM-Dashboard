import pandas as pd
from datetime import datetime

# File paths
excel_file_path = "SIN_ExportSeatsWithTraineesInfos_2025-01-16_03-08-39.xlsx"  # Replace with actual path
csv_file_path = "assets-2025-01-14-1736821245.csv"  # Replace with actual path

# Load the files
assets_df = pd.read_csv(csv_file_path)
myteam_df = pd.read_excel(excel_file_path)

# Prompt user for input
device_id = input("Enter the Asset ID (e.g., L117): ")

# Search for the device in the assets file
device_row = assets_df[assets_df['Asset ID'] == device_id]

if device_row.empty:
    print(f"Device ID {device_id} not found in the assets file.")
else:
    location = device_row.iloc[0]['Location']
    if not location.startswith("SIN"):
        print(f"{device_id} {location}")
    else:
        # Find the corresponding course in the myteam file
        course_row = myteam_df[myteam_df['Course'] == location]
        if course_row.empty:
            print(f"Location {location} not found in the myteam file.")
        else:
            # Extract 'From' and 'Trainee Code'
            from_date = course_row.iloc[0]['From']
            trainee_code = course_row.iloc[0]['Trainee Code']

            # Find all 'To' dates for the same Trainee Code
            trainee_rows = myteam_df[myteam_df['Trainee Code'] == trainee_code]
            to_dates = pd.to_datetime(trainee_rows['To'])
            max_to_date = to_dates.max()

            # Calculate completion percentage
            today = datetime.now()
            from_date = pd.to_datetime(from_date)
            completion_percentage = ((today - from_date).days / (max_to_date - from_date).days) * 100

            # Find other Asset IDs with the same location
            same_location_assets = assets_df[assets_df['Location'] == location]['Asset ID'].tolist()
            same_location_assets.remove(device_id)  # Exclude the input device ID

            # Print the result
            print(f"{device_id} {location} {from_date.strftime('%d %b %Y')} {max_to_date.strftime('%d %b %Y')} {completion_percentage:.2f}% {' '.join(same_location_assets)}")
