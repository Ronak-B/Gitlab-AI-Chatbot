import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
from google import genai
from dotenv import load_dotenv
from utils.helpers import normalize, title_keywords, extract_error_type
from backend.config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    GEMINI_MODEL,
    GEMINI_API_KEY_ENV,
    N_RESULTS,
    TOP_K,
    LLM_PROMPT_TEMPLATE,
)

load_dotenv()

class Chatbot:
    """
    Chatbot class to handle embedding, retrieval, reranking, and response generation.
    """

    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)
        self.genai_client = genai.Client(api_key=os.getenv(GEMINI_API_KEY_ENV))

    def embed_query(self, query):
        """
        Generate embedding for the user query.
        """
        return self.model.encode([query]).tolist()

    def retrieve_documents(self, query_emb, n_results=N_RESULTS):
        """
        Retrieve documents from ChromaDB based on the query embedding.
        """
    
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        return docs, metas

    def rerank_documents(self, user_query, docs, metas, top_k=TOP_K):
        """
        Rerank documents using a cross-encoder and title matching.
        """
        if not docs or not metas:
            return [], []

        pairs = [(user_query, doc) for doc in docs]
        scores = self.cross_encoder.predict(pairs)
        keywords = set(user_query.lower().split())

        # Boost scores based on title keyword matches
        for i, meta in enumerate(metas):
            title_norm = normalize(meta.get('section_title', ''))
            title_kw = title_keywords(meta.get('section_title', ''))
            if len(title_kw & keywords) / max(1, len(title_kw)) > 0.6:
                scores[i] += 2.0
            elif any(k in title_norm for k in keywords):
                scores[i] += 0.75

        reranked = sorted(zip(docs, metas, scores), key=lambda x: x[2], reverse=True)
        return reranked[:top_k]

    def generate_llm_response(self, user_query, context_docs):
        """
        Generate a response using the LLM based on the user query and context documents.
        """
    
        context_text = "\n\n".join([doc for doc, _, _ in context_docs])
        prompt = LLM_PROMPT_TEMPLATE.format(context=context_text, question=user_query)

        try:
            response = self.genai_client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt
            )
            response_text = response.text.strip() if hasattr(response, "text") else str(response)
            sources = list({meta.get('url') for _, meta, _ in context_docs if meta.get('url')})
            return response_text, sources
        except Exception as e:
            error_type = extract_error_type(e)
            if error_type.startswith("5"):
                return "Server error (5xx). Please try again later.", []
            return "Error generating response.", []

    def generate_response(self, user_query):
        """
        Main method to generate a response for the user query.
        """

        emb = self.embed_query(user_query)
        docs, metas = self.retrieve_documents(emb)
        top_docs = self.rerank_documents(user_query, docs, metas)
        if not top_docs:
            return "No relevant info found.", []
        return self.generate_llm_response(user_query, top_docs)
