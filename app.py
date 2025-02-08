from flask import Flask, request, jsonify
import os
import uuid
import time

app = Flask(__name__)

# Directory to store user files
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

@app.route("/write", methods=["POST"])
def write_text():
    """Write text to the user’s file."""
    data = request.json
    session_id = data.get("session_id")
    text = data.get("text", "")

    file_path = os.path.join(DATA_DIR, f"{session_id}.txt")

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("")

    with open(file_path, "w") as f:
        f.write(text + "\n")

    return jsonify({"message": "Text added"}), 200

@app.route("/read", methods=["GET"])
def read_text():
    """Read text from the user’s file."""
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