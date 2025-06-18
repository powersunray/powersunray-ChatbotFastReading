from langchain_together import TogetherEmbeddings, Together
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os
import re
from models import DocumentChunk
from dotenv import load_dotenv

load_dotenv()

def clean_redundant(text, question):
    # Eliminate the first sentence if it is similar to the question
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if sentences and sentences[0].strip() == question.strip():
        text = ' '.join(sentences[1:])
    
    # Eliminate unwanted phrases
    patterns = [
        r"(Tôi luôn sẵn.*?)(?=(Tôi luôn sẵn|Xin chào|Xin cảm ơn|$))",
        r"Xin chào.*",
        r"Xin cảm ơn.*",
        r"Nếu bạn cần thêm.*",
        r"Chúc bạn thành công.*",
        r"Tôi hy vọng.*",
        r"Tôi sẵn sàng.*",
        r"Tôi luôn sẵn lòng.*",
        r"Hãy cho tôi biết.*",
        r"Tôi chúc bạn.*",
        r"\|\s*\|",
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
        
    # Eliminate repeated sentences
    seen = set()
    unique_sentences = []
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if sentence not in seen:
            seen.add(sentence)
            unique_sentences.append(sentence)

    return ' '.join(unique_sentences).strip()

def trim_to_last_sentence(text, max_length=700):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = ""
    for s in sentences:
        if len(result) + len(s) > max_length:
            break
        result += s + " "
    return result.strip()

# Chatbot function
def chatbot(question, session_id, file_ids, link_ids):
    # Get chunks from database
    chunks = DocumentChunk.query.filter(
        (DocumentChunk.session_id == session_id) &
        ( (DocumentChunk.document_id.in_(file_ids)) | (DocumentChunk.link_id.in_(link_ids)) )
    ).all()
    
    if not chunks:
        raise ValueError("No chunks were found for the selected documents or links.")
    
    texts = [chunk.chunk_text for chunk in chunks]
    metadatas = [{"source": chunk.document_id or chunk.link_id} for chunk in chunks]
    
    # Create vector stores
    embeddings = TogetherEmbeddings(
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
        model="togethercomputer/m2-bert-80M-32k-retrieval"
    )
    vector_store = FAISS.from_texts(
        texts,
        embeddings,
        metadatas=metadatas
    )
    
    # Initialize LLM
    llm = Together(
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        # temperature=0,
        # max_tokens=1000,
        temperature=0.2, # slight creativity but mostly deterministic
        max_tokens=800,  # faster response with tighter focus
    )
    
    # Define a specific prompt to restrict LLM to provided documents
    prompt_template = PromptTemplate(
        input_variables=["question", "context"],
        template= (
            "Answer the question '{question}' based only on the information from the following text: {context}. "
            "If the question asks for a summary or overview (e.g., 'File hiện tại chứa thông tin gì?'), provide a concise and brief summary of the main topics in the text. "
            
            "If no relevant information is found in the text, reply with: 'Thông tin bạn hỏi không được đề cập trong file.' "
            "if the question is in Vietnamese, or 'The information you asked for is not mentioned in the file.' if the question is in English. "
            "Ensure the entire response, including this message, is in the same language as the question '{question}'."
            "Keep answers short, 600 tokens max, and end naturally so as not to be cut off within the 600 token limit."
        )
    )
    
    # Create QA chain with the custom prompt
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt_template)
    
    ### ! FIRST WAY
    # Search and answer
    matches = vector_store.similarity_search(question, k=15)
    # matches = vector_store.similarity_search(question, k=5) #! NEW: reduce to top 5 for speed
    
    # Create answer using the LLM
    response = chain.run(input_documents=matches, question=question)
    #! NEW: Post-process to remove repeated phrases and trim
    response = clean_redundant(response, question)
    response = trim_to_last_sentence(response, max_length=700)
    
    # Check if the response is exactly the "no information found" message
    no_info_messages = [
        "Thông tin bạn hỏi không được đề cập trong file.",
        "The information you asked for is not mentioned in the file."
    ]
    if response.strip() in no_info_messages:
        unique_sources = []
    else:
        # Filter sources based on relevance to the response
        unique_sources = []
        if matches:
            # Extract key terms from the question and response (simple approach: split into words)
            response_terms = set(re.findall(r'\w+', response.lower()))
            for match in matches:
                match_text = match.page_content.lower()
                #! DEBUG
                # print("Response terms:", response_terms)
                # print("Match text:", match_text)
                # Check if any term in the response is in the match text
                if any(term in match_text for term in response_terms):
                    source = match.metadata["source"]
                    if source not in unique_sources:
                        unique_sources.append(source)
    
    return response, unique_sources
