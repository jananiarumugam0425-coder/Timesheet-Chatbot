import csv
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
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

# HTML content embedded directly in the Python file
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timesheet Reviewer Bot</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- React and ReactDOM CDNs - these will be global variables -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <!-- Babel Standalone CDN -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body class="bg-[#121212] font-sans text-gray-200 flex items-center justify-center min-h-screen">
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useRef, useEffect } = React;
        const { createRoot } = ReactDOM;

        const App = () => {
            const [messages, setMessages] = useState([]);
            const [input, setInput] = useState('');
            const [isLoading, setIsLoading] = useState(false);
            const messagesEndRef = useRef(null);
            
            const scrollToBottom = () => {
                messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            };

            useEffect(scrollToBottom, [messages]);

            const handleSend = async (e) => {
                e.preventDefault();
                if (!input.trim()) return;
                const newUserMessage = { text: input, sender: 'user' };
                setMessages((prevMessages) => [...prevMessages, newUserMessage]);
                setIsLoading(true);

                try {
                    // Corrected fetch URL to be relative
                    const response = await fetch('/review', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: input }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    setMessages((prevMessages) => [...prevMessages, { text: data.response, sender: 'bot' }]);
                } catch (error) {
                    console.error('Error:', error);
                    setMessages((prevMessages) => [...prevMessages, { text: "I'm sorry, I encountered an error. Please try again.", sender: 'bot' }]);
                } finally {
                    setIsLoading(false);
                    setInput('');
                }
            };
            
            const handleResetChat = () => {
                setMessages([]);
            };

            const LoadingIndicator = () => (
                <div className="flex items-center space-x-2 my-2">
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse"></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse delay-150"></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse delay-300"></div>
                </div>
            );

            const ChatSuggestions = () => (
                <div className="mt-4 flex flex-wrap gap-2 justify-center">
                    <button onClick={() => setInput("total hours of John Doe")} className="bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs py-2 px-4 rounded-full transition-colors duration-200">
                        John's Hours
                    </button>
                    <button onClick={() => setInput("overtime done by employees")} className="bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs py-2 px-4 rounded-full transition-colors duration-200">
                        Overtime
                    </button>
                    <button onClick={() => setInput("total time spent on Project Alpha")} className="bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs py-2 px-4 rounded-full transition-colors duration-200">
                        Project Alpha
                    </button>
                    <button onClick={() => setInput("when did Jane Smith work on Project Gamma")} className="bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs py-2 px-4 rounded-full transition-colors duration-200">
                        Jane's Hours
                    </button>
                </div>
            );

            return (
                <div className="p-4 md:p-8 w-full max-w-2xl">
                    <div className="bg-[#1f1f1f] rounded-3xl shadow-xl overflow-hidden flex flex-col h-[85vh]">
                        <div className="bg-[#2a2a2a] p-5 flex items-center justify-between rounded-t-3xl">
                            <h1 className="text-xl md:text-2xl font-semibold">Timesheet Reviewer Bot</h1>
                            <div className="flex items-center text-sm text-gray-400">
                                <span className="relative flex h-2 w-2 mr-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                </span>
                                Status: Online
                            </div>
                        </div>

                        <div className="flex-grow p-5 md:p-6 overflow-y-auto space-y-4 chat-messages">
                            {messages.length === 0 && (
                                <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
                                    <p className="text-lg">Ask me about timesheets...</p>
                                    <p className="text-sm mt-1">I can answer questions about hours worked, projects, and employee overtime.</p>
                                    <ChatSuggestions />
                                </div>
                            )}
                            {messages.map((msg, index) => (
                                <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`message-bubble ${msg.sender === 'user' ? 'bg-[#0d47a1] text-right rounded-br-2xl' : 'bg-[#333333] rounded-bl-2xl'}`}>
                                        {msg.text}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <LoadingIndicator />
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <form onSubmit={handleSend} className="bg-[#2a2a2a] p-4 flex items-center space-x-2 rounded-b-3xl">
                            <button
                                type="button"
                                onClick={handleResetChat}
                                className="text-gray-400 hover:text-gray-200 transition-colors duration-200 p-2"
                                title="Reset Chat"
                            >
                                <i className="fas fa-sync-alt"></i>
                            </button>
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                className="flex-grow bg-[#1f1f1f] border border-[#333333] rounded-full py-2 px-4 text-sm focus:outline-none focus:border-blue-500 placeholder-gray-500"
                                placeholder="Ask about timesheets..."
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full transition-colors duration-200 disabled:opacity-50"
                                disabled={isLoading}
                                aria-label="Send"
                            >
                                <i className="fas fa-paper-plane"></i>
                            </button>
                        </form>
                    </div>
                </div>
            );
        };

        const container = document.getElementById('root');
        const root = createRoot(container);
        root.render(<App />);

    </script>
</body>
</html>
"""

# Route to serve the main HTML file
@app.route('/')
def serve_index():
    return FRONTEND_HTML

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
