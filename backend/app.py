import os
import shutil
from database import db
from flask_cors import CORS
from chat_service import chatbot
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from process_documents import process_and_store_chunks
from models import ChatSession, DBDocument, Link, ChatHistory, DocumentChunk

from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
# CORS(app) # Add CORS to allow frontend from diff port send requests
CORS(app, resources={r"/*": {
    "origins": "http://127.0.0.1:8000",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})  # Allow frontend to send request
    
# Configure uploads folder
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Attach db with Flask app
db.init_app(app)

# Initialize Migrate
migrate = Migrate(app, db)

# Allowed extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'pptx', 'png', 'jpg', 'jpeg', 'heic'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Manage chat sessions
@app.route('/sessions', methods=['GET', 'POST'])
def sessions():
    if request.method == 'GET':
        sessions = ChatSession.query.all()
        return jsonify([{'id': s.id, 'name': s.name, 'created_at': s.created_at} for s in sessions])
    elif request.method == 'POST':
        name = request.json.get('name', 'New Chat')
        session = ChatSession(name=name)
        db.session.add(session)
        db.session.commit()
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], str(session.id)), exist_ok=True)
        return  jsonify({'id': session.id, 'name': session.name}), 201
    
@app.route('/sessions/<int:session_id>', methods=['PUT'])
def rename_session(session_id):
    session = ChatSession.query.get_or_404(session_id)
    new_name = request.json.get('name')
    if not new_name:
        return jsonify({'error': 'New name is required'}), 400
    session.name = new_name
    db.session.commit()
    return jsonify({'id': session.id, 'name': session.name})

@app.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        # 1. Delete related DocumentChunk
        DocumentChunk.query.filter_by(session_id=session_id).delete()
        # 2. Delete related DBDocument
        DBDocument.query.filter_by(session_id=session_id).delete()
        # 3. Delete related links
        Link.query.filter_by(session_id=session_id).delete()
        # 4. Delete related ChatHistory
        ChatHistory.query.filter_by(session_id=session_id).delete()
        # 5. Delete ChatSession
        session = ChatSession.query.get_or_404(session_id)
        db.session.delete(session)
        
        # Commit all changes to database
        db.session.commit()
        
        # Delete ChatSession's subfolder (if any)
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(session_id))
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)
        
        return '', 204
    except Exception as e:
        db.session.rollback() # Rollback if error occurs
        return jsonify({'error': str(e)}), 500 # Return error code 500 if there is a problem
    
# Manage document
@app.route('/sessions/<int:session_id>/files', methods=['GET'])
def get_files(session_id):
    files = DBDocument.query.filter_by(session_id=session_id).all()
    return jsonify([{'id': f.id, 'filename': f.filename} for f in files])

@app.route('/sessions/<int:session_id>/upload', methods=['POST'])
def upload_file(session_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], str(session_id), file.filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        document = DBDocument(session_id=session_id, filename=file.filename, filepath=filepath)
        db.session.add(document)
        db.session.commit()
        # Save chunks
        process_and_store_chunks(filepath, 'file', session_id)
        return jsonify({'id': document.id, 'filename': document.filename}), 201
    return jsonify({'error': 'File type not allowed'}), 400

# Manage links
@app.route('/sessions/<int:session_id>/links', methods=['GET'])
def get_links(session_id):
    links = Link.query.filter_by(session_id=session_id).all()
    return jsonify([{'id': l.id, 'name': l.name, 'url': l.url} for l in links])

@app.route('/sessions/<int:session_id>/links', methods=['POST'])
def add_link(session_id):
    name = request.json.get('name', '')
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    link = Link(session_id=session_id, name=name, url=url)
    db.session.add(link)
    db.session.commit()
    # Save chunks
    process_and_store_chunks(url, 'link', session_id)
    return jsonify({'id': link.id, 'name':link.name, 'url': link.url}), 201

# Chat history
@app.route('/chat_history/<int:session_id>', methods=['GET'])
def get_chat_history(session_id):
    history = ChatHistory.query.filter_by(session_id=session_id).order_by(ChatHistory.timestamp).all()
    return jsonify([{'message': h.message, 'is_user': h.is_user} for h in history])

# Answer question
@app.route('/sessions/<int:session_id>/ask', methods=['POST'])
def ask_question(session_id):
    data = request.json
    question = data.get('question')
    file_ids = data.get('file_ids', [])
    link_ids = data.get('link_ids', [])
    if not question:
        return jsonify({'error': 'Please enter your question'}), 400

    # Call chatbot with file_ids and link_ids
    answer, sources = chatbot(question, session_id, file_ids, link_ids)

    # Resolve source IDs to names                
    source_names = []
    for source_type, source_id in sources:
        if source_type == "file":
            doc = db.session.get(DBDocument, source_id)
            if doc:
                source_names.append(doc.filename)
        elif source_type == "link":
            link = db.session.get(Link, source_id)
            if link:
                source_names.append(link.name or link.url)
                
    # Format the source text
    source_text = "SOURCE: " + ", ".join(source_names) if source_names else ""
    
    # Save chat history
    user_message = ChatHistory(session_id=session_id, is_user=True, message=question)
    bot_message = ChatHistory(session_id=session_id, is_user=False, message=answer)
    db.session.add(user_message)
    db.session.add(bot_message)
    if source_text:
        source_message = ChatHistory(session_id=session_id, is_user=False, message=source_text)
        db.session.add(source_message)
    db.session.commit()

    return jsonify({'answer': answer, 'source_text': source_text})
    
if __name__ == '__main__':
    # Create database the first time
    with app.app_context():
        try:
            # Automatically create table if it does not exist
            db.create_all()
            print("Connected and created tables in chatbot_db.")
        except Exception as e:
            print(f"Error connecting or creating table: {e}")
            print("Please check if 'chatbot_db' has been created in pgAdmin 4.")
    app.run(debug=True, host="127.0.0.1", port=5000)
