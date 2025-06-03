import PyPDF2
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        main_content = soup.find('div', {'class': 'content'}) #! Modify class if needed
        text = main_content.get_text(separator=' ') if main_content else soup.get_text(separator=' ')
        return text
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return ""

def get_document_chunks():
    documents = {}
    # List of PDFs
    pdf_files = ['27_2025_TT-BTC_658258.pdf', '03_2025_TT-BNNMT_657315.pdf']
    for pdf in pdf_files:
        documents[pdf] = extract_text_from_pdf(pdf)
        
    # List of URLs
    urls = ['https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword=th%C3%B4ng%20t%C6%B0&match=True&area=0']
    for url in urls:
        documents[url] = extract_text_from_url(url)
        
    # Split text and save the sources
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
    )
    chunks_with_metadata = []
    for source, text in documents.items():
        chunks = text_splitter.split_text(text)
        for chunk in chunks:
            chunks_with_metadata.append({"text": chunk, "source": source})
    return chunks_with_metadata


# def get_document_chunks():
#     documents = {}
#     # List of PDFs
#     pdf_files = ['27_2025_TT-BTC_658258.pdf', '03_2025_TT-BNNMT_657315.pdf']
#     for pdf in pdf_files:
#         documents[pdf] = extract_text_from_pdf(pdf)
        
#     # List of URLs
#     urls = ['https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword=th%C3%B4ng%20t%C6%B0&match=True&area=0']
#     for url in urls:
#         documents[url] = extract_text_from_url(url)
    
#     # Split text into chunks
#     text_splitter = RecursiveCharacterTextSplitter(
#         separators='\n',
#         chunk_size=1000,
#         chunk_overlap=150,
#         length_function=len
#     )
    
#     all_chunks = []
#     for source, text in documents.items():
#         chunks = text_splitter.split_text(text)
#         all_chunks.extend(chunks)
#     return all_chunks