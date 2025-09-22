import csv
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests

# Set up the Flask app and CORS
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# The timesheet data is loaded from a CSV file.
def load_timesheet_data(file_path):
    """Loads timesheet data from a CSV file."""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert hours to float for calculations
                try:
                    row['hours_worked'] = float(row['hours_worked'])
                    data.append(row)
                except ValueError:
                    print(f"Warning: Could not convert hours_worked to float for row: {row}")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    return data

# This function handles the LLM interaction using the Gemini API.
def get_conversational_response(prompt):
    """Sends a prompt to the Gemini API and returns a conversational response."""
    # Your provided API key
    api_key = "AIzaSyB4A1xeQpG_UTH7DShnnfVTszI59AbZbtI"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

    # The payload for the API request
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "systemInstruction": {
            "parts": [{"text": "You are a friendly and professional chatbot that summarizes timesheet data in a conversational tone. Your response should be easy to understand and direct."}]
        },
        "generationConfig": {
            "temperature": 0.5,
            "topP": 0.8
        }
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Check for a valid response
        if result and 'candidates' in result and result['candidates'][0]['content']['parts'][0]['text']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Sorry, I couldn't generate a response. The API returned an invalid result."
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "I'm sorry, I'm unable to connect to the API at the moment."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred. Please try again later."

# This function processes the user's query and analyzes the data.
def analyze_timesheet_data(query, data):
    """Analyzes the timesheet data based on the user's query."""
    lower_query = query.lower()
    
    # Dynamically get all employee names, IDs, and projects
    all_employee_names = list(set(d['employee_name'].lower() for d in data))
    all_employee_ids = list(set(d['employee_id'].lower() for d in data))
    all_projects = list(set(d['project'].lower() for d in data))

    # Helper function to find a matching entity
    def find_entity(keywords, query_text):
        for keyword in keywords:
            if keyword in query_text:
                return keyword
        return None

    # Check for general overtime queries
    if "overtime" in lower_query or "overtime done by employees" in lower_query:
        overtime_employees = {}
        for employee_name in all_employee_names:
            total_hours = sum(entry['hours_worked'] for entry in data if entry['employee_name'].lower() == employee_name)
            if total_hours > 40:
                overtime_employees[employee_name.title()] = total_hours
        
        if overtime_employees:
            details = [f"{name} worked {hours} hours" for name, hours in overtime_employees.items()]
            return f"The following employees have done overtime: {', '.join(details)}. A standard work week is 40 hours."
        else:
            return "No employees have worked more than 40 hours this week."

    # Check for queries about a specific employee
    employee_query = find_entity(all_employee_names, lower_query) or find_entity(all_employee_ids, lower_query)
    if employee_query:
        employee_data = [entry for entry in data if entry['employee_name'].lower() == employee_query or entry['employee_id'].lower() == employee_query]
        
        if not employee_data:
            return f"No data found for the requested employee."

        employee_name = employee_data[0]['employee_name']
        
        # Check for specific working hours query
        if "working hours" in lower_query or "total hours" in lower_query:
            total_hours = sum(entry['hours_worked'] for entry in employee_data)
            return f"Total hours worked by {employee_name} is {total_hours}."

        # Check for specific project count query
        if "total project" in lower_query or "projects" in lower_query:
            projects_worked_on = list(set(entry['project'] for entry in employee_data))
            num_projects = len(projects_worked_on)
            project_list = ", ".join(projects_worked_on)
            return f"{employee_name} has worked on {num_projects} projects: {project_list}."

        # Check for specific date range query
        if "date" in lower_query:
            project_query = find_entity(all_projects, lower_query)
            if project_query:
                for entry in employee_data:
                    if entry['project'].lower() == project_query:
                        return f"{employee_name} worked on {entry['project']} from {entry['start_date']} to {entry['end_date']}."
                return f"No dates found for {employee_name} on {project_query}."
            else:
                return "Please specify a project name to get the dates."

        # Default summary for an employee
        total_hours = sum(entry['hours_worked'] for entry in employee_data)
        overtime_status = "above the standard 40-hour limit" if total_hours > 40 else "within the 40-hour limit"
        
        project_hours = {}
        for entry in employee_data:
            project = entry['project']
            hours = entry['hours_worked']
            project_hours[project] = project_hours.get(project, 0) + hours

        project_details = ", ".join([f"{proj} for {hours} hours" for proj, hours in project_hours.items()])

        return f"Timesheet data for {employee_name}: Total hours worked is {total_hours}. This is {overtime_status}. Breakdown by project: {project_details}."

    # Analyze total hours per project
    project_query = find_entity(all_projects, lower_query)
    if project_query:
        total_hours = sum(entry['hours_worked'] for entry in data if entry['project'].lower() == project_query)
        return f"Timesheet data for {project_query}: Total hours worked is {total_hours}."
    
    return "I am unable to analyze that request. Please ask about an employee's total hours or a project's total hours, or ask about overtime."

# Serve the main HTML file from the frontend directory
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/review', methods=['POST'])
def review():
    """Main API endpoint to handle timesheet review requests."""
    user_query = request.json.get('query', '')
    if not user_query:
        return jsonify({"response": "Please provide a query."}), 400

    data = load_timesheet_data('timesheet_data.csv')
    if not data:
        return jsonify({"response": "Could not load timesheet data."}), 500

    analysis_result = analyze_timesheet_data(user_query, data)
    
    # Use the LLM to make the response conversational
    llm_prompt = f"Given the following factual data: '{analysis_result}', provide a concise and conversational summary. Do not add any new facts."
    llm_response = get_conversational_response(llm_prompt)
    
    return jsonify({"response": llm_response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
