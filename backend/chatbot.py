from process_documents import get_document_chunks
from langchain_together import TogetherEmbeddings, Together
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os
import re
from dotenv import load_dotenv

load_dotenv()

def clean_redundant_ending(text):
    patterns = [
        r"(Tôi luôn sẵn.*?)(?=(Tôi luôn sẵn|Xin chào|Xin cảm ơn|$))",
        r"Xin chào.*",
        r"Xin cảm ơn.*",
        r"Nếu bạn cần thêm.*",
        r"Chúc bạn thành công.*"
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    return text.strip()

def trim_to_last_sentence(text, max_length=700):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = ""
    for s in sentences:
        if len(result) + len(s) > max_length:
            break
        result += s + " "
    return result.strip()

# Chatbot function
def chatbot(question, selected_files, selected_links):
    # Get chunks from selected files and links
    chunks_with_metadata = get_document_chunks(selected_files, selected_links)
    if not chunks_with_metadata:
        raise ValueError("No text extracted from the selected documents or links.")
    
    # Filter non-empty text
    texts = [chunk["text"] for chunk in chunks_with_metadata if chunk["text"].strip()]
    metadatas = [{"source": chunk["source"]} for chunk in chunks_with_metadata if chunk["text"].strip()]

    if not texts:
        raise ValueError("No valid (non-empty) text chunks found to build vector store.")
    
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
    
    # # Create QA chain
    # chain = load_qa_chain(llm, chain_type="stuff")
    
    # Define a specific prompt to restrict LLM to provided documents
    prompt_template = PromptTemplate(
        input_variables=["question", "context"],
        # template="Chỉ trả lời câu hỏi '{question}' dựa trên thông tin từ đoạn văn bản sau: {context}. Nếu không tìm thấy thông tin liên quan trong đoạn văn bản, hãy trả lời: 'Thông tin bạn hỏi không được đề cập trong file.'"
        template= (
            "Answer the question '{question}' based only on the information from the following text: {context}. "
            "If the question asks for a summary or overview (e.g., 'File hiện tại chứa thông tin gì?'), provide a concise and brief summary of the main topics in the text. "
            "If no relevant information is found in the text, reply with: 'Thông tin bạn hỏi không được đề cập trong file.' "
            "if the question is in Vietnamese, or 'The information you asked for is not mentioned in the file.' if the question is in English. "
            "Ensure the entire response, including this message, is in the same language as the question '{question}'."
            "Keep answers short, 600 tokens max, and end naturally so as not to be cut off within the 600 token limit."
        )
        #! NEW
        # template=(
        #     "You are a document assistant. Answer the question: '{question}' based strictly on this content: {context}.\n"
        #     "- If the question asks for a summary, summarize only what is present.\n"
        #     "- If nothing relevant is found, reply 'Thông tin bạn hỏi không được đề cập trong file.'\n"
        #     "- Always respond in the same language as the question. '\n"
        #     "- Keep your answer clear, under 800 tokens, and make sure it ends naturally."
        # )
    )
    
    # Create QA chain with the custom prompt
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt_template)
    
    # Search and answer
    # matches = vector_store.similarity_search(question, k=10)
    matches = vector_store.similarity_search(question, k=5) #! NEW: reduce to top 5 for speed
    
    # Create answer using the LLM
    response = chain.run(input_documents=matches, question=question)
    #! NEW: Post-process to remove repeated phrases and trim
    response = clean_redundant_ending(response)
    response = trim_to_last_sentence(response, max_length=700)
                   
    # Filter sources based on relevance to the response
    unique_sources = []
    if "không được đề cập trong file" not in response and "not mentioned in the file" not in response:
        # Extract key terms from the question and response (simple approach: split into words)
        question_terms = set(re.findall(r'\w+', question.lower()))
        response_terms = set(re.findall(r'\w+', response.lower()))
        relevant_terms = question_terms.union(response_terms) # Combine terms for better filtering
        for match in matches:
            match_text = match.page_content.lower()
            #! DEBUG
            # print("Question terms:", question_terms)
            # print("Response terms:", response_terms)
            # print("Match text:", match_text)
            # Check if any term in the response is in the match text
            if any(term in match_text for term in relevant_terms):
                if match.metadata["source"] not in unique_sources:
                    unique_sources.append(match.metadata["source"])
    
    return response, unique_sources
