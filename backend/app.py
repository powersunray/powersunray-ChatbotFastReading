from chatbot import chatbot
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app) # Add CORS to allow frontend from diff port send requests

# Folder to save files
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({"path": filepath}), 200


@app.route('/ask', methods=['POST'])
def ask():
    # Get JSON data from POST
    data = request.json
    question = data.get('question')
    selected_files = data.get('files', [])
    selected_links = data.get('links', [])    
    
    # Check if question is empty
    if not question:
        return jsonify({'error': 'Please enter your question'}), 400
    
    # Call chatbot function to ge answer and sources
    # answer, sources = chatbot(question)
    answer, sources = chatbot(question, selected_files, selected_links)
    
    # Return result in JSON format
    return jsonify({
        'answer': answer,
        'sources': sources
    })
    
if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host="127.0.0.1", port=5000)