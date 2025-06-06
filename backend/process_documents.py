import PyPDF2 # For .pdf
import requests
from bs4 import BeautifulSoup # For link
from langchain.text_splitter import RecursiveCharacterTextSplitter
from docx import Document # For .docx
import textract
import subprocess
import openpyxl # For .xlsx
import os

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
        # Filter to get main content, remove irrelevant parts
        # main_content = soup.find('div', {'class': 'content'}) #! Modify class if needed
        # text = main_content.get_text(separator=' ') if main_content else soup.get_text(separator=' ')
        # return text
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
# def extract_text_from_doc(doc_path):
#     try:
#         # result = subprocess.run(['antiword', doc_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
#         # text = result.stdout.decode('utf-8')
#         # return text
#         result = subprocess.run(['antiword', doc_path], capture_output=True, text=True)
#         return result.stdout
#     except Exception as e:
#         print(f"Error processing {doc_path}: {e}")
#         return ""

#! doc antiword 02
# def extract_text_from_doc(doc_path):
#     try:
#         # Gọi antiword để trích xuất văn bản từ file .doc
#         result = subprocess.run(['antiword', doc_path], capture_output=True, text=True, check=True)
#         if result.stdout:
#             return result.stdout
#         else:
#             print(f"No text extracted from {doc_path}")
#             return ""
#     except subprocess.CalledProcessError as e:
#         print(f"Antiword error for {doc_path}: {e.stderr}")
#         return ""
#     except FileNotFoundError:
#         print("Antiword not found. Ensure it is installed and added to PATH.")
#         return ""
#     except Exception as e:
#         print(f"Error processing {doc_path}: {e}")
#         return ""

#! doc textract 01
def extract_text_from_doc(doc_path):
    try:
        text = textract.process(doc_path).decode('utf-8')
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
    
def get_document_chunks(selected_files, selected_links):
    documents = {}
    
    # List of PDFs
    # pdf_files = ['27_2025_TT-BTC_658258.pdf', '03_2025_TT-BNNMT_657315.pdf']
    # for pdf in pdf_files:
    
    # for pdf in selected_files:
    #     documents[pdf] = extract_text_from_pdf(pdf)
    
    #! New: List of uploaded files
    for file_path in selected_files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            documents[file_path] = extract_text_from_pdf(file_path)
        elif ext == '.docx':
            documents[file_path] = extract_text_from_docx(file_path)
        elif ext == '.doc':
            documents[file_path] = extract_text_from_doc(file_path)
        elif ext == '.xlsx':
            documents[file_path] = extract_text_from_excel(file_path)
        else:
            print(f"Unsupported file type: {file_path}, extension: {ext}")
        
    # List of URLs
    # urls = ['https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword=th%C3%B4ng%20t%C6%B0&match=True&area=0']
    # for url in urls:
    for url in selected_links:
        documents[url] = extract_text_from_url(url)
        
    # Split text and save the sources
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300,
    )
    chunks_with_metadata = []
    for source, text in documents.items():
        chunks = text_splitter.split_text(text)
        for chunk in chunks:
            chunks_with_metadata.append({"text": chunk, "source": source})
    return chunks_with_metadata
