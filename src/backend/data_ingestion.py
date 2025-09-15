import requests
import time
import chromadb
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')
def get_embedding(text):
    return model.encode(text).tolist()

# ---- CONFIG ----
BASE_URLS = [
    ("https://handbook.gitlab.com/", "handbook_"),
    ("https://about.gitlab.com/direction/", "direction_"),
]
MAX_DEPTH = 3
BATCH_SIZE = 100  # Save progress after every 100 URLs

def normalize_url(url):
    """
    Normalize URL by removing fragments, lowercasing scheme and netloc,
    and stripping trailing slashes.
    """

    url, _ = urldefrag(url)
    parsed = urlparse(url)
    norm = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip('/')
    )
    return norm.geturl()

def is_allowed_url(url, base_url):
    """
    Check if the URL is within the same domain and path as the base_url,
    and has no query parameters.
    """

    parsed = urlparse(url)
    return (
        parsed.netloc == urlparse(base_url).netloc and
        normalize_url(url).startswith(normalize_url(base_url)) and
        not parsed.query
    )

def get_subpage_links(url, url_filter=None):
    """
    Fetch the page and extract all valid subpage links.
    """

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            full_url = urljoin(url, a["href"])
            if url_filter is None or url_filter(full_url):
                links.add(normalize_url(full_url))
        return links
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return set()

def extract_main_content(soup):
    """
    Extract the main content area from the soup.
    """

    main = soup.find("main") or soup.find("article")
    if not main:
        main = soup
    return main

def chunk_content(soup, url):
    """
    Chunk the content of the page into smaller sections.
    """

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

def get_next_chunk_id(collection, id_prefix):
    """
    Get the next available chunk ID with the given prefix.
    """

    all_ids = collection.get()['ids']
    max_id = 0
    for cid in all_ids:
        if cid.startswith(id_prefix):
            try:
                num = int(cid[len(id_prefix):])
                if num > max_id:
                    max_id = num
            except Exception:
                continue
    return max_id + 1

def save_to_chroma(chunks, collection, chunk_id_start, id_prefix=""):
    """
    Save the list of chunks to ChromaDB collection.
    """

    documents = []
    metadatas = []
    ids = []
    sub_chunk_count = 0
    for i, chunk in enumerate(chunks):
        sub_chunks = [chunk["text"]]
        for j, sub_text in enumerate(sub_chunks):
            full_text = f"Section title: {chunk['section_title']}\n{sub_text}"
            documents.append(full_text)
            metadatas.append({"section_title": chunk["section_title"], "url": chunk["url"], "source_prefix": id_prefix})
            ids.append(f"{id_prefix}{chunk_id_start + sub_chunk_count}")
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

def crawl_and_embed(start_url, url_filter, max_depth=2, batch_size=100, id_prefix=""):
    """
    Crawl the website starting from start_url up to max_depth using BFS.
    Extract and chunk content, then embed and store in ChromaDB.
    """

    visited = set()
    queue = deque()
    queue.append((normalize_url(start_url), 0))
    # Setup ChromaDB persistent client
    client = chromadb.PersistentClient(path="./data/chroma_db2")
    collection = client.get_or_create_collection("handbook_chunks")
    chunk_id = get_next_chunk_id(collection, id_prefix)
    url_counter = 0
    batch_chunks = []

    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        if url_filter and not url_filter(url):
            continue
        print(f"[crawl] Crawling: {url} (depth {depth})")
        visited.add(url)
        url_counter += 1
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            page_chunks = chunk_content(soup, url)
            batch_chunks.extend(page_chunks)
            if depth < max_depth:
                subpages = get_subpage_links(url, url_filter)
                for sub_url in subpages:
                    if sub_url not in visited:
                        queue.append((sub_url, depth + 1))
            time.sleep(0.5) # Be polite with a short delay
        except Exception as e:
            print(f"[crawl] Error crawling {url}: {e}")

        # Save to ChromaDB every batch_size URLs
        if url_counter % batch_size == 0:
            print(f"[chroma] Saving batch at URL count: {url_counter}")
            chunk_id = save_to_chroma(batch_chunks, collection, chunk_id, id_prefix=id_prefix)
            batch_chunks = []

    # Save any remaining chunks
    if batch_chunks:
        print(f"[chroma] Saving final batch at URL count: {url_counter}")
        save_to_chroma(batch_chunks, collection, chunk_id, id_prefix=id_prefix)

def main():
    for base_url, id_prefix in BASE_URLS:
        print(f"\n--- Starting crawl for {base_url} ---\n")
        crawl_and_embed(
            start_url=base_url,
            url_filter=lambda url, bu=base_url: is_allowed_url(url, bu),
            max_depth=MAX_DEPTH,
            batch_size=BATCH_SIZE,
            id_prefix=id_prefix
        )

if __name__ == "__main__":
    main()