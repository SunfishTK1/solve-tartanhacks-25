"""
Flask API for Due Diligence Analysis

This API integrates the backend functions to perform company due diligence analysis.
It provides endpoints to start a session, write/read session data, and analyze a company.
"""

from flask import Flask, request, jsonify
import os
import uuid
import time

# Import the backend function for performing the due diligence analysis.
# It is assumed that your backend code is in a module named backend.py
from input import enter_company_name

app = Flask(__name__)

# Directory to store session files (if needed)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------


@app.route("/start", methods=["GET"])
def start_session():
    """
    [GET] /start
    -----------
    Starts a new session by generating a unique session ID and creating an empty session file.
    
    **Sample Response:**
    {
        "session_id": "a1b2c3d4",
        "message": "Session started"
    }
    """
    session_id = str(uuid.uuid4())[:8]  # Generate a short session ID
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    with open(file_path, "w") as f:
        f.write("")
    return jsonify({"session_id": session_id, "message": "Session started"}), 200


@app.route("/write", methods=["POST"])
def write_text():
    """
    [POST] /write
    --------------
    Appends text to the session file associated with the given session ID.
    
    **Request JSON:**
    {
        "session_id": "a1b2c3d4",
        "text": "Some text to append."
    }
    
    **Sample Response:**
    {
        "message": "Text added"
    }
    """
    data = request.json
    session_id = data.get("session_id")
    text = data.get("text", "")

    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    if not os.path.exists(file_path):
        return jsonify({"error": "Invalid session ID"}), 400

    with open(file_path, "a") as f:
        f.write(text + "\n")

    return jsonify({"message": "Text added"}), 200


@app.route("/read", methods=["GET"])
def read_text():
    """
    [GET] /read
    -----------
    Reads and returns the content of the session file for the given session ID.
    
    **Query Parameter:**
      - session_id: The session identifier.
      
    **Sample Response:**
    {
        "content": "Text previously written..."
    }
    """
    session_id = request.args.get("session_id")
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    if not os.path.exists(file_path):
        return jsonify({"error": "Invalid session ID"}), 400

    with open(file_path, "r") as f:
        content = f.read()

    return jsonify({"content": content})


@app.route("/analyze", methods=["POST"])
def analyze_company():
    """
    [POST] /analyze
    ---------------
    Performs a due diligence analysis for the provided company.
    Accepts company_name, industry, and an optional uuid.
    
    **Request JSON:**
    {
        "company_name": "Example Company, Inc.",
        "industry": "Retail",
        "uuid": "optional-unique-identifier"  // Optional; if not provided a new one will be generated.
    }
    
    **Processing Details:**
      - Calls the backend function `enter_company_name()` (or a similar function)
        to perform the due diligence analysis.
      - If an industry is provided, it is attached to the response.
    
    **Sample Response:**
    {
        "full report": "Full due diligence report text...",
        "subquestions": [ ... ],
        "industry": "Retail"  // Echoed back if provided
    }
    """
    print("Analysis Start")
    data = request.json
    company_name = data.get("company_name")
    industry = data.get("industry")  # New field for industry information.
    uuid_value = data.get("uuid", str(uuid.uuid4()))
    
    if not company_name:
        return jsonify({"error": "Missing 'company_name' in request"}), 400

    try:
        # Call the existing backend analysis function.
        # If desired, you could create a separate function that also uses industry.
        print("called")
        result = enter_company_name(company_name, uuid_value, industry)
        print("return from function")

        # If industry is provided, attach it to the result.
        if industry:
            result["industry"] = industry

        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error in /analyze: {e}")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# Helper Functions (if needed)
# -----------------------------------------------------------------------------
def append_to_file(session_id, text):
    """
    Appends text to the session file for the given session ID.
    Used internally if needed.
    """
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError("Invalid session ID")
    with open(file_path, "a") as f:
        f.write(text + "\n")


# -----------------------------------------------------------------------------
# Optional Testing Endpoint
# -----------------------------------------------------------------------------
@app.route("/test", methods=["GET"])
def perform_test():
    """
    [GET] /test
    -----------
    A simple test endpoint that writes "Hello!" to a test session file multiple times.
    This is useful for testing file append operations.
    
    **Sample Response:**
    {
        "message": "Test completed."
    }
    """
    session_id = "test"
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    text = "Hello!"
    for i in range(5):
        app.logger.info("Writing to test file...")
        with open(file_path, "a") as f:
            f.write(text + "\n")
        time.sleep(1)
    return jsonify({"message": "Test completed."}), 200


# -----------------------------------------------------------------------------
# Application Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=8007)
