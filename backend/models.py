from database import db
from pgvector.sqlalchemy import Vector

# Define models
class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class DBDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'))
    name = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(255), nullable=False)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'))
    is_user = db.Column(db.Boolean, default=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'))
    document_id = db.Column(db.Integer, db.ForeignKey('db_document.id'), nullable=True)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=True)
    chunk_text = db.Column(db.Text, nullable=False)
    embedding = db.Column(Vector(768))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())