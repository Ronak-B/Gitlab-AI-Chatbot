import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
from collections import deque
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')
def get_embedding(text):
    return model.encode(text).tolist()

BASE_URL = "https://handbook.gitlab.com/handbook/"
DOMAIN = "handbook.gitlab.com"
MAX_DEPTH = 3
BATCH_SIZE = 100  # Save progress after every 100 URLs

def is_handbook_url(url):
    parsed = urlparse(url)
    return (
        parsed.netloc == DOMAIN and
        parsed.path.startswith("/handbook/") and
        not parsed.query
        and not parsed.path.startswith("/handbook/company/team")
    )

def normalize_url(url):
    url, _ = urldefrag(url)
    parsed = urlparse(url)
    norm = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip('/')
    )
    return norm.geturl()

def get_subpage_links(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            full_url = urljoin(url, a["href"])
            if is_handbook_url(full_url):
                links.add(normalize_url(full_url))
        return links
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return set()

def extract_main_content(soup):
    main = soup.find("main") or soup.find("article")
    if not main:
        main = soup
    return main

def chunk_content(soup, url):
    main = extract_main_content(soup)
    chunks = []

    # Step 1: capture any text BEFORE the first heading
    intro_parts = []
    for el in main.children:
        if getattr(el, "name", None) and el.name.startswith('h') and len(el.name) == 2:
            break
        if el.name == 'p':
            intro_parts.append(el.get_text(strip=True))
        elif el.name == 'div':
            intro_parts.append(el.get_text(strip=True))
    if intro_parts:
        chunks.append({"section_title": "Introduction", "text": "\n".join(intro_parts), "url": url})

    # Step 2: normal heading-based chunks
    for heading in main.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        section_title = heading.get_text(strip=True)
        section_content = []
        for sib in heading.find_next_siblings():
            if sib.name and sib.name.startswith('h') and len(sib.name) == 2:
                break
            if sib.name == 'p':
                section_content.append(sib.get_text(strip=True))
            elif sib.name == 'li':
                section_content.append(f"- {sib.get_text(strip=True)}")
            elif sib.name in ['ul', 'ol']:
                for li in sib.find_all('li'):
                    section_content.append(f"- {li.get_text(strip=True)}")
            elif sib.name == 'div':
                section_content.append(sib.get_text(strip=True))
        if section_content:
            chunks.append({"section_title": section_title, "text": "\n".join(section_content), "url": url})

    return chunks


splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=250)

def save_to_chroma(chunks, collection, chunk_id_start):
    documents = []
    metadatas = []
    ids = []
    sub_chunk_count = 0
    for i, chunk in enumerate(chunks):
        sub_chunks = [chunk["text"]]
        for j, sub_text in enumerate(sub_chunks):
            full_text = f"Section title: {chunk['section_title']}\n{sub_text}"
            documents.append(full_text)
            metadatas.append({"section_title": chunk["section_title"], "url": chunk["url"]})
            ids.append(f"{chunk_id_start + sub_chunk_count}")
            sub_chunk_count += 1
    if documents:
        embeddings = model.encode(documents, batch_size=16, show_progress_bar=True)
        collection.add(
            embeddings=[emb.tolist() for emb in embeddings],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    return chunk_id_start + sub_chunk_count

def crawl_handbook_bfs_and_embed(start_url, max_depth=2, batch_size=100):
    visited = set()
    queue = deque()
    if is_handbook_url(start_url):
        queue.append((normalize_url(start_url), 0))
    chunk_id = 1
    url_counter = 0
    batch_chunks = []

    # Setup ChromaDB persistent client
    client = chromadb.PersistentClient(path="./gitlab-ai-chatbot/src/data/chroma_db2")
    collection = client.get_or_create_collection("handbook_chunks")

    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        print(f"[crawl_handbook] Crawling: {url} (depth {depth})")
        visited.add(url)
        url_counter += 1
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            page_chunks = chunk_content(soup, url)
            batch_chunks.extend(page_chunks)
            if depth < max_depth:
                subpages = get_subpage_links(url)
                for sub_url in subpages:
                    if sub_url not in visited:
                        queue.append((sub_url, depth + 1))
            time.sleep(0.5)
        except Exception as e:
            print(f"[crawl_handbook] Error crawling {url}: {e}")

        # Save to ChromaDB every batch_size URLs
        if url_counter % batch_size == 0:
            print(f"[chroma] Saving batch at URL count: {url_counter}")
            chunk_id = save_to_chroma(batch_chunks, collection, chunk_id)
            batch_chunks = []

    # Save any remaining chunks
    if batch_chunks:
        print(f"[chroma] Saving final batch at URL count: {url_counter}")
        save_to_chroma(batch_chunks, collection, chunk_id)

def main():
    print("Starting handbook crawl and embedding (BFS)...")
    crawl_handbook_bfs_and_embed(BASE_URL, MAX_DEPTH, BATCH_SIZE)
    print("Crawling and embedding complete. Data is in ChromaDB.")


def test_query_chroma(query):
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    print("Loading ChromaDB ...")
    model = SentenceTransformer('all-mpnet-base-v2')
    client = chromadb.PersistentClient(path="./gitlab-ai-chatbot/src/data/chroma_db2")
    collection = client.get_or_create_collection("handbook_chunks")
    print("Loaded collection. Querying...")

    query_emb = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_emb,
        n_results=10,
        include=['documents', 'metadatas', 'distances']
    )
    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        print(f"\nSection: {meta['section_title']}\nURL: {meta['url']}\nScore: {dist:.4f}\nText: {doc}...")

if __name__ == "__main__":
    #main()
    test_query_chroma("Examples of Potentially GitLab Sensitive Topics")

