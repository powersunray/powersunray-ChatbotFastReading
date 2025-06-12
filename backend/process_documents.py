import PyPDF2 # For .pdf
import requests
from bs4 import BeautifulSoup # For link
from langchain.text_splitter import RecursiveCharacterTextSplitter
from docx import Document # For .docx
import subprocess
import openpyxl # For .xlsx
import os
from database import db
from models import DBDocument, Link, DocumentChunk 

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
            return text
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return ""
    
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        main_contents = soup.find_all(['div', 'p'], class_=['content', 'content1', 'content-1', 'content-0', 'nqContent'])
        text = ''
        for content in main_contents:
            text += content.get_text(separator=' ') + ' '
        return text.strip() if text else soup.get_text(separator=' ')
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return ""

def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error processing {docx_path}: {e}")
        return ""

#! doc antiword 01  
def extract_text_from_doc(doc_path):
    try:
        result = subprocess.run(['antiword', doc_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        text = result.stdout.decode('utf-8')
        if not text.strip():
            raise ValueError("antiword returned empty")
        return text
    except Exception as e:
        print(f"Error processing {doc_path}: {e}")
        return ""
    
def extract_text_from_excel(xlsx_path):
    try:
        workbook = openpyxl.load_workbook(xlsx_path)
        text = ''
        for sheet in workbook:
            for row in sheet.iter_rows(values_only=True):
                text += ' '.join([str(cell) for cell in row if cell is not None]) + '\n'
        return text
    except Exception as e:
        print(f"Error processing {xlsx_path}: {e}")
        return ""
    
def process_and_store_chunks(source, source_type, session_id):
    if source_type == 'file':
        ext = os.path.splitext(source)[1].lower()
        if ext == '.pdf':
            text = extract_text_from_pdf(source)
        elif ext == '.docx':
            text = extract_text_from_docx(source)
        elif ext == '.doc':
            text = extract_text_from_doc(source)
        elif ext == '.xlsx':
            text = extract_text_from_excel(source)
        else:
            print(f"Unsupported file type: {source}")
            return
    elif source_type == 'link':
        text = extract_text_from_url(source)
    else:
        print("Invalid source type")
        return
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = text_splitter.split_text(text)
    
    # Save chunks into database
    for chunk in chunks:
        chunk_entry = DocumentChunk(
            session_id=session_id,
            document_id=DBDocument.query.filter_by(filepath=source).first().id if source_type == 'file' else None,
            link_id=Link.query.filter_by(url=source).first().id if source_type == 'link' else None,
            chunk_text=chunk
        )
        db.session.add(chunk_entry)
    db.session.commit()