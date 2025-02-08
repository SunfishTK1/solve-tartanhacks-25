from flask import Flask, request, jsonify
import os
import uuid
import time
from .superStructure.summaries import SummaryManager

app = Flask(__name__)

# Directory to store user files
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize the summary manager
summary_manager = SummaryManager()
summary_manager.load_from_file('summaries.json')

@app.route("/write", methods=["POST"])
def write_text():
    """Write text to the user's file."""
    data = request.json
    session_id = data.get("session_id")
    text = data.get("text", "")

    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("")

    with open(file_path, "w") as f:
        f.write(text + "\n")

    # Update the summary for this session
    summary_manager.update_summary(session_id, text)
    summary_manager.save_to_file('summaries.json')

    return jsonify({"message": "Text added"}), 200

@app.route("/read_json", methods=["GET"])
def read_text():
    """Read text from the user's file."""
    session_id = request.args.get("session_id")
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("") 

    with open(file_path, "r") as f:
        content = f.read()

    return jsonify({"content": content})

def append_to_file(session_id, text):
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")

    if not os.path.exists(file_path):
        raise FileNotFoundError("Invalid session ID")

    with open(file_path, "a") as f:
        f.write(text + "\n")

@app.route("/get_summary", methods=["GET"])
def get_summary():
    """Get the summary for a specific session ID."""
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400

    summary = summary_manager.get_summary(session_id)
    if summary:
        return jsonify({"content": summary.get('content', 'No summary available')})
    return jsonify({"content": "Generating research summary..."})

@app.route("/create_session", methods=["POST"])
def create_session():
    """Create a new session with a unique ID."""
    session_id = str(uuid.uuid4())
    print(f"Created new session with ID: {session_id}")
    
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    
    # Initialize empty file for the session
    with open(file_path, "w") as f:
        f.write("")
    
    return jsonify({"session_id": session_id}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

def perform_test():
    session_id = "test"
    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")
    text = "Hello!"
    for i in range(5):
        print("Ran!")
        with open(file_path, "a") as f:
            f.write(text + "\n")
            time.sleep(3)