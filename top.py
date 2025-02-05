from flask import Blueprint, render_template, request, jsonify
import os
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta
from algorithms import process_course_data_with_date_filter, count_courses_per_month, process_device_info, count_fleet_per_month  # Import the function
import plotly.graph_objects as go

top_bp = Blueprint('top', __name__, template_folder='templates')

uploaded_files = {}

# Load configuration from the JSON file
def load_config():
    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        return None
    
# Load config data
config = load_config()

# Check if config is loaded properly
if config is None:
    exit()

# Extract values from the config dictionary
rsaf_laptops = config["rsaf_laptops"]
a380_laptops = config["a380_laptops"]
cannot_assign_laptops = config["cannot_assign_laptops"]
cannot_assign_ipads = config["cannot_assign_ipads"]
include_course_types = config['include_course_types']

# Helper function to get the date for this Thursday
def get_this_thursday():
    today = datetime.today()
    days_until_thursday = (3 - today.weekday() + 7) % 7  # Ensure a positive number
    this_thursday = today + timedelta(days=days_until_thursday)
    return this_thursday.strftime('%Y-%m-%d')

def generate_laptops_donut_chart():
    # Ensure assets file is uploaded
    if 'assets' not in uploaded_files:
        return None
    
    # Load the CSV file
    file_path = uploaded_files['assets']
    df = pd.read_csv(file_path)
    
    # Filter for laptops
    laptops = df[(df['Asset ID'].str.startswith('L')) & (df['Status'] == 'Ready')]
    
    # Initialize counters for the different sections
    categories = {
        'Standard': 0,
        'Ongoing Course': 0,
        'RSAF Laptops': 0,
        'A380 Laptops': 0
    }
    
    # Filter laptops based on conditions
    for _, row in laptops.iterrows():
        asset_id = row['Asset ID']
        location = row['Location']
        # Skip laptops in the 'cannot_assign_laptops' list
        if asset_id in cannot_assign_laptops:
            continue
        
        # Check for RSAF Laptops
        if asset_id in rsaf_laptops and location == 'M01-13':
            categories['RSAF Laptops'] += 1
            continue
        
        # Check for A380 Laptops
        if asset_id in a380_laptops and location == 'M01-13':
            categories['A380 Laptops'] += 1
            continue
        
        # Check for 'M01-13' and 'Ongoing Course' categories based on location
        if location == 'M01-13':
            categories['Standard'] += 1
        elif str(location).startswith('SIN'):
            categories['Ongoing Course'] += 1

    # Prepare data for the donut chart
    chart_data = pd.DataFrame(list(categories.items()), columns=['Location', 'Count'])
    
    # Create donut chart
    fig = px.pie(chart_data, names='Location', values='Count', hole=0.4,
                 title='Laptop inventory')
    
    # Update traces to show label + value
    fig.update_traces(textinfo='label+value')  # This will show label and count
    
    return fig.to_html(full_html=False)

def generate_ipads_donut_chart():
    # Ensure assets file is uploaded
    if 'assets' not in uploaded_files:
        return None
    
    # Load the CSV file
    file_path = uploaded_files['assets']
    df = pd.read_csv(file_path)
    
    # Filter for iPads (Asset ID starts with 'A' and Status is 'Ready')
    ipads = df[(df['Asset ID'].str.startswith('A')) & (df['Status'] == 'Ready')]
    
    # Initialize counters for the different sections
    categories = {
        'M01-13': 0,
        'Ongoing Course': 0
    }
    
    # Filter iPads based on conditions
    for _, row in ipads.iterrows():
        asset_id = row['Asset ID']
        location = row['Location']
        
        # Check for 'M01-13' location
        if location == 'M01-13':
            categories['M01-13'] += 1
        elif str(location).startswith('SIN'):
            categories['Ongoing Course'] += 1
    # Prepare data for the donut chart
    chart_data = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
    
    # Create donut chart
    fig = px.pie(chart_data, names='Category', values='Count', hole=0.4,
                 title='iPad inventory')
    
    # Update traces to show label + value
    fig.update_traces(textinfo='label+value')  # This will show label and count
    
    return fig.to_html(full_html=False)

@top_bp.route('/', methods=['GET', 'POST'])
def index():
    # Get the date from the request, default to this Thursday if not provided
    end_date = request.form.get('end_date', get_this_thursday())
    
    # Ensure end_date is a valid string format
    try:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        end_date = datetime.strptime(get_this_thursday(), "%Y-%m-%d").date()  # Fallback to this Thursday

    # Check for existing files in the 'uploads' directory
    myteam_file_detected = False
    assets_file_detected = False
    donut_chart_l = None  # Initialize the variable for laptop donut chart
    donut_chart_a = None  # Initialize the variable for iPad donut chart
    course_data_results = []  # Initialize a list to hold course data

    # Check for files that match the naming criteria
    for file in os.listdir('uploads'):
        if file.startswith('SIN') and file.endswith('.xlsx'):
            uploaded_files['myteam'] = os.path.join('uploads', file)
            myteam_file_detected = True
        if file.startswith('assets') and file.endswith('.csv'):
            uploaded_files['assets'] = os.path.join('uploads', file)
            assets_file_detected = True

    # Call the course processing function if both files are available
    if myteam_file_detected and assets_file_detected:
        # Call the function and pass the paths of the files
        results = process_course_data_with_date_filter(
            uploaded_files['assets'], 
            uploaded_files['myteam'],
            end_date=end_date  # Pass the selected end date to the function
        )
        # Save the results for rendering in the template
        course_data_results = results

    if myteam_file_detected:
        monthly_bar_chart = generate_monthly_bar_chart()
        monthly_fleet_chart = generate_monthly_fleet_chart()
    
    # If assets file is detected, generate the donut charts
    if assets_file_detected:
        donut_chart_l = generate_laptops_donut_chart()
        donut_chart_a = generate_ipads_donut_chart()

    # Pass the status, course data, both donut charts, search_results, and the end_date to the frontend
    return render_template(
        'top.html',
        myteam_file_detected=myteam_file_detected,
        assets_file_detected=assets_file_detected,
        donut_chart_l=donut_chart_l,  # Pass laptop donut chart
        donut_chart_a=donut_chart_a,  # Pass iPad donut chart
        course_data_results=course_data_results,  # Pass the course data to the template
        end_date=end_date.strftime('%Y-%m-%d'),  # Format date as string
        monthly_bar_chart=monthly_bar_chart,
        monthly_fleet_chart=monthly_fleet_chart
    )



@top_bp.route('/update_date', methods=['GET'])
def update_date():
    # Get the new date from the query parameter (or use a default if not provided)
    end_date = request.args.get('end_date', get_this_thursday())
    
    # Ensure the date is in the correct format
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Ensure both files are available
    myteam_file_detected = 'myteam' in uploaded_files
    assets_file_detected = 'assets' in uploaded_files

    # Initialize the response dictionary
    response = {}
    if myteam_file_detected and assets_file_detected:
        # Process the course data with the selected end date
        results = process_course_data_with_date_filter(
            uploaded_files['assets'], 
            uploaded_files['myteam'],
            end_date=end_date
        )
        
        # Prepare the course data for the table
        course_data_html = ""
        for course_data in results:
            parts = course_data.split(' - ')
            course_data_html += f"""
            <tr>
                <td>{parts[0]}</td>
                <td>{parts[1]}</td>
                <td>{parts[2]}</td>
            </tr>
            """
        
        # Add the HTML for the updated course table to the response
        response['course_table'] = course_data_html

    # Return the updated course table as JSON
    return jsonify(response)


@top_bp.route('/get_search_results', methods=['POST'])
def get_search_results():
    # Get the incoming JSON data (which includes deviceId)
    data = request.get_json()
    device_id = data.get('deviceId')

    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    # Assuming uploaded_files['myteam'] and uploaded_files['assets'] are available
    # Process the device info with the device_id passed from the frontend
    search_results_py = process_device_info(uploaded_files['myteam'], uploaded_files['assets'], device_id)
    # Return the processed results as a JSON response
    return jsonify(search_results_py)

@top_bp.route('/search-device', methods=['POST'])
def search_device():
    # Get the incoming data (deviceId) from the request
    data = request.get_json()
    device_id = data.get('deviceId')

    # Example response: Send a success message or device details
    response_data = {
        'message': f"Device {device_id} found",
        # You can add more details here if needed
    }
    
    return jsonify(response_data)
    

def generate_monthly_bar_chart():
    results_count = count_courses_per_month(uploaded_files['myteam'], include_course_types=include_course_types)

    # Prepare the months and counts for laptops and iPads
    months = []
    laptops_count = []
    ipads_count = []
    for result in results_count:
        # Format: 'October 2024: 6 0'
        month, counts = result.split(': ')
        laptop_count, ipad_count = map(int, counts.split())

        months.append(month)
        laptops_count.append(laptop_count)
        ipads_count.append(ipad_count)

    # Create the bar chart with Plotly
    fig = go.Figure()
    # Add bottom bar (laptops)
    fig.add_trace(go.Bar(
        x=months,
        y=laptops_count,
        name='Laptops',
        marker_color='blue',
        base=0  # Bottom bar starts at 0
    ))

    # Add upper bar (iPads)
    fig.add_trace(go.Bar(
        x=months,
        y=ipads_count,
        name='iPads',
        marker_color='orange',
        base=laptops_count  # Upper bar starts at the value of the laptops count
    ))

    # Customize layout
    fig.update_layout(
        title='Monthly Laptop and iPad Count',
        barmode='stack',  # Stack the bars
        xaxis_title='Month',
        yaxis_title='Count',
        template='plotly_white',  # Use a clean white template
        showlegend=True
    )
    return fig.to_html(full_html=False)

import plotly.graph_objects as go

def generate_monthly_fleet_chart():
    results_count = count_fleet_per_month(uploaded_files['myteam'], include_course_types=include_course_types)

    # Prepare the months and counts for A320, A330, A350, and A380
    months = []
    a320_count = []
    a330_count = []
    a350_count = []
    a380_count = []
    
    for result in results_count:

        # Split into month and counts
        parts = result.split(': ', 1)  # Split only on the first ': ' to get the month and the rest

        if len(parts) == 2:
            month = parts[0]
            counts_str = parts[1]
            
            # Split counts by ', ' and further split by ': ' to get the count for each aircraft type
            fleet_counts = [count.split(': ') for count in counts_str.split(', ')]

            
            # Ensure there are exactly four counts for A320, A330, A350, A380
            if len(fleet_counts) == 4:
                a320 = int(fleet_counts[0][1])
                a330 = int(fleet_counts[1][1])
                a350 = int(fleet_counts[2][1])
                a380 = int(fleet_counts[3][1])

                # Append to the lists
                months.append(month)
                a320_count.append(a320)
                a330_count.append(a330)
                a350_count.append(a350)
                a380_count.append(a380)
            else:
                print(f"Skipping invalid result due to incorrect fleet counts: {result}")
        else:
            print(f"Skipping invalid result due to split issue: {result}")
    
    # Create the bar chart with Plotly
    fig = go.Figure()

    # Add bars for each aircraft type
    fig.add_trace(go.Bar(
        x=months,
        y=a320_count,
        name='A320',
        marker_color='blue',
        base=0
    ))

    fig.add_trace(go.Bar(
        x=months,
        y=a330_count,
        name='A330',
        marker_color='green',
        base=a320_count  # Stack on top of A320
    ))

    fig.add_trace(go.Bar(
        x=months,
        y=a350_count,
        name='A350',
        marker_color='red',
        base=[sum(x) for x in zip(a320_count, a330_count)]  # Stack on top of A320 + A330
    ))

    fig.add_trace(go.Bar(
        x=months,
        y=a380_count,
        name='A380',
        marker_color='orange',
        base=[sum(x) for x in zip(a320_count, a330_count, a350_count)]  # Stack on top of A320 + A330 + A350
    ))

    # Customize layout
    fig.update_layout(
        title='Monthly Aircraft Type Count',
        barmode='stack',  # Stack the bars
        xaxis_title='Month',
        yaxis_title='Count',
        template='plotly_white',
        showlegend=True
    )
    
    return fig.to_html(full_html=False)


