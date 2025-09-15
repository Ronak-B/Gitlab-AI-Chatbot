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
)

load_dotenv()

class Chatbot:
    """
    Chatbot class integrating ChromaDB for retrieval and Google Gemini for generation.
    """
    
    def __init__(self):
        """
        Initialize the Chatbot with necessary models and clients.
        """

        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)
        self.genai_client = genai.Client(api_key=os.getenv(GEMINI_API_KEY_ENV))

    def generate_response(self, user_query, n_results=N_RESULTS, top_k=TOP_K):
        """
        Generate a response to the user query using retrieval and generation.
        Fetch top N_RESULTS from ChromaDB.
        Rerank retrieved documents and use top_k as context for the Gemini model.
        """

        query_emb = self.model.encode([user_query]).tolist()
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )

        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]

        if not docs or not metas:
            return (
                "Sorry, I couldn't find any relevant information for your question.",
                []
            )

        pairs = [(user_query, doc) for doc in docs]
        scores = self.cross_encoder.predict(pairs)
        keywords = set(user_query.lower().split())

        # Boost scores based on title relevance
        for i, meta in enumerate(metas):
            title_norm = normalize(meta.get('section_title', ''))
            title_kw = title_keywords(meta.get('section_title', ''))
            if len(title_kw & keywords) / max(1, len(title_kw)) > 0.6:
                scores[i] += 2.0
            elif any(k in title_norm for k in keywords):
                scores[i] += 0.75

        reranked = sorted(zip(docs, metas, scores), key=lambda x: x[2], reverse=True)
        context = "\n\n".join([doc for doc, _, _ in reranked[:top_k]])

        if not context.strip():
            return (
                "Sorry, I couldn't find any relevant information for your question.",
                []
            )

        prompt = (
            "You are a helpful assistant answering questions using the GitLab Handbook. "
            "Use only the provided context to answer. If the answer is not in the context, just respond with \"I don't know.\"\n\n"
            "Do not repeat the context verbatim. Summarize and synthesize the information.\n\n"
            f"Context:\n{context}\n"
            f"User question: {user_query}\n"
            "Answer:"
        )

        try:
            response = self.genai_client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt
            )
            response_text = response.text.strip() if hasattr(response, "text") else str(response)
            # If model says "I don't know", treat as no answer
            if "i don't know" in response_text.lower():
                return (
                    "Sorry, I couldn't find an answer to your question in my knowledge base.",
                    []
                )
            # Extract unique source URLs
            sources = list({meta.get('url') for _, meta, _ in reranked[:top_k] if meta.get('url')})
            return response_text, sources
        except Exception as e:
            error_type = extract_error_type(e)
            if error_type.startswith("5"):
                return (
                    "Sorry, there was a server error (5xx) while generating the answer. Please try again later.",
                    []
                )
            return (
                f"Sorry, there was an error generating the answer.",
                []
            )