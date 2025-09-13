import os
import re
import string
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
from google import genai
from dotenv import load_dotenv
load_dotenv()

def normalize(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def title_keywords(title):
    # Remove parentheticals and punctuation, split into words
    title = re.sub(r'\(.*?\)', '', title)
    return set(re.findall(r'\w+', title.lower()))

class Chatbot:
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.client = chromadb.PersistentClient(path="./data/chroma_db3")
        self.collection = self.client.get_or_create_collection("handbook_chunks")
        self.genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Uses GEMINI_API_KEY from env

    def generate_response(self, user_query, n_results=15, top_k=3):
        query_emb = self.model.encode([user_query]).tolist()
        # 2. Retrieve relevant chunks
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        docs = results['documents'][0]
        metas = results['metadatas'][0]

        # Rerank using cross-encoder
        pairs = [(user_query, doc) for doc in docs]
        scores = self.cross_encoder.predict(pairs)

        keywords = set(re.findall(r'\w+', user_query.lower()))
        for i, meta in enumerate(metas):
            title_norm = normalize(meta['section_title'])
            title_kw = title_keywords(meta['section_title'])
            # Strong boost if most title keywords are in the query
            if len(title_kw & keywords) / max(1, len(title_kw)) > 0.6:
                scores[i] += 2.0
            elif any(k in title_norm for k in keywords):
                scores[i] += 0.75

        reranked = sorted(zip(docs, metas, scores), key=lambda x: x[2], reverse=True)

        # Build context from reranked docs (top n_results)
        context = "\n\n".join([doc for doc, _, _ in reranked[:top_k]])

        if not context:
            return "Sorry, I couldn't find relevant information."

        prompt = (
            "You are a helpful assistant answering questions using the GitLab Handbook. "
            "Use only the provided context to answer. If the answer is not in the context, say you don't know.\n\n" \
            "Do not repeat the context verbatim. Summarize and synthesize the information.\n\n"
            f"Context:\n{context}\n"
            f"User question: {user_query}\n"
            "Answer:"
        )

        response = self.genai_client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        response_text = response.text.strip() if hasattr(response, "text") else str(response)
        sources = set(meta['url'] for _, meta, _ in reranked[:top_k])
        return response_text, list(sources)

if __name__ == "__main__":
    pass
    bot = Chatbot()
    query = "What are gitlab's core values?"
    print(bot.generate_response(query))