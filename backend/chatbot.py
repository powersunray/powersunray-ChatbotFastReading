from process_documents import get_document_chunks
from langchain_together import TogetherEmbeddings, Together
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
import os
from dotenv import load_dotenv

load_dotenv()
# def create_vector_store(chunks):
#     embeddings = TogetherEmbeddings(
#         api_key=os.getenv("TOGETHER_AI_API_KEY"),
#         model="togethercomputer/m2-bert-80M-32k-retrieval",
#     )
#     vector_store = FAISS.from_texts(chunks, embeddings)
#     return vector_store

def create_vector_store(chunks_with_metadata):
    texts = [chunk["text"] for chunk in chunks_with_metadata]
    # metadatas = [chunk["source"] for chunk in chunks_with_metadata]
    metadatas = [{"source": chunk["source"]} for chunk in chunks_with_metadata]
    embeddings = TogetherEmbeddings(
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
        model="togethercomputer/m2-bert-80M-32k-retrieval"
    )
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    return vector_store

def answer_question(vector_store, question):
    llm = Together(
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        temperature=0,
        max_tokens=500,
    )
    chain = load_qa_chain(llm, chain_type="stuff")
    
    # Take 2 most related sources with metadata
    matches = vector_store.similarity_search(question, k=10)
    # docs = [match.page_content for match in matches] # Document content
    sources = [match.metadata["source"] for match in matches] # Source from metadata
    
    # Create answer from LLM
    # response = chain.run(input_documents=match, question=question)
    response = chain.run(input_documents=matches, question=question)
    
    # Eliminate duplicate sources
    unique_sources = list(set(sources))
    return response, unique_sources

# Load and split documents once on startup
chunks = get_document_chunks()
vector_store = create_vector_store(chunks)

# Chatbot function
def chatbot(question):
    # response = answer_question(vector_store, question)
    # return response
    response, sources = answer_question(vector_store, question)
    return response, sources

# Run chatbot
if __name__ == "__main__":
    question = input("Enter your question: ")
    while question.lower() != "stop":
        # answer = chatbot(question)
        answer, sources = chatbot(question)
        print(f"Answer: {answer}")
        if sources:
            print(f"Sources: {', '.join(sources)}")
        else:
            print("No sources found.")
        question = input("Enter your question: ")