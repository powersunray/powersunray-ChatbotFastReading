from process_documents import get_document_chunks
from langchain_together import TogetherEmbeddings, Together
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Chatbot function
def chatbot(question, selected_files, selected_links):
    # Get chunks from selected files and links
    chunks_with_metadata = get_document_chunks(selected_files, selected_links)
    
    # Create vector stores from them
    embeddings = TogetherEmbeddings(
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
        model="togethercomputer/m2-bert-80M-32k-retrieval"
    )
    vector_store = FAISS.from_texts(
        [chunk["text"] for chunk in chunks_with_metadata],
        embeddings,
        metadatas=[{"source": chunk["source"]} for chunk in chunks_with_metadata]
    )
    
    # Initialize LLM
    llm = Together(
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        temperature=0,
        max_tokens=1000,
    )
    
    # # Create QA chain
    # chain = load_qa_chain(llm, chain_type="stuff")
    
    #! New
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
    )
    
    # Create QA chain with the custom prompt
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt_template)
    
    # Find related text passages
    matches = vector_store.similarity_search(question, k=10)
    
    # Create answer using the LLM
    response = chain.run(input_documents=matches, question=question)
    
    # # Get sources list and eliminate duplicate sources
    # sources = [match.metadata["source"] for match in matches]
    # unique_sources = list(set(sources))
    
    #! New
    # # Filter sources based on relevance to the response
    # unique_sources = []
    # if "không được đề cập trong file" not in response and "not mentioned in the file" not in response:
    #     # Extract key terms from the response (simple approach: split into words)
    #     response_terms = set(re.findall(r'\w+', response.lower()))
    #     for match in matches:
    #         match_text = match.page_content.lower()
    #         # Check if any term in the response is in the match text
    #         if any(term in match_text for term in response_terms):
    #             if match.metadata["source"] not in unique_sources:
    #                 unique_sources.append(match.metadata["source"])
                    
    #! New 02
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
            print("Question terms:", question_terms)
            print("Response terms:", response_terms)
            print("Match text:", match_text)
            # Check if any term in the response is in the match text
            if any(term in match_text for term in relevant_terms):
                if match.metadata["source"] not in unique_sources:
                    unique_sources.append(match.metadata["source"])
    
    return response, unique_sources
