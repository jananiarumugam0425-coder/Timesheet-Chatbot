# **Timesheet Chatbot**

The Timesheet Chatbot is an interactive tool designed to simplify and automate the process of logging work hours. It uses a conversational interface to allow users to easily submit their timesheet entries, eliminating the need for traditional, often cumbersome, forms or spreadsheets.

-----

## **Key Features**

  * **Natural Language Processing (NLP):** The bot understands and processes commands in plain English, making it intuitive and user-friendly. Users can simply type "log 4 hours on Project Alpha" or "add 2.5 hours to training" and the bot will handle the rest.
  * **Time and Project Management:** It tracks and categorizes hours by project, allowing for a clear overview of time allocation.
  * **Reporting and Analytics:** The chatbot can generate summaries and detailed reports of logged hours for a specified period, aiding in project management and payroll processing.
  * **Notifications and Reminders:** It can send automated reminders to ensure timely submission of timesheets, reducing administrative overhead.
  * **Integration:** The bot is built with flexibility in mind and can be integrated with existing project management and HR systems.

-----

## **Technology Stack**

  * **Backend:** Python
  * **NLP:** NLTK, spaCy
  * **Chatbot Framework:** Rasa, Dialogflow
  * **Database:** PostgreSQL, SQLite
  * **Platform:** Can be deployed on web platforms, Slack, or Microsoft Teams.

-----

## **How it Works**

The chatbot uses a combination of **NLP** and **backend logic** to function. When a user sends a message, the NLP engine extracts key entities like the number of hours, the project name, and the date. This information is then passed to the backend, which validates the data and updates the user's timesheet in the database. The chatbot can then respond with a confirmation or a request for more information.

-----

## **Getting Started**

### **Prerequisites**

  * **Python 3.x** installed.
  * **pip** (Python package installer) installed.
  * A code editor or IDE (e.g., VS Code, PyCharm).

### **Installation**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/timesheet-chatbot.git
    cd timesheet-chatbot
    ```
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    ```
3.  **Activate the virtual environment:**
      * **On macOS and Linux:**
        ```bash
        source venv/bin/activate
        ```
      * **On Windows:**
        ```bash
        venv\Scripts\activate
        ```
4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

-----

## **How to Run `server.py`**

The `server.py` file is the core of the chatbot's backend. It handles API requests, processes timesheet data, and interacts with the database.

1.  **Configure the database:**

      * Open the `config.py` file.
      * Update the database connection string with your credentials. For example, for SQLite, you can simply define the database file path.

2.  **Run the server:**

      * From the root directory of the project (where `server.py` is located), execute the following command in your terminal:

    <!-- end list -->

    ```bash
    python server.py
    ```

      * The server will start and typically run on `http://127.0.0.1:5000` (or a similar address). You'll see a message in the terminal indicating that the server is running.
      * You can now interact with the chatbot's API endpoints using a tool like Postman, or by integrating it with a front-end application or a messaging platform like Slack or Microsoft Teams.
