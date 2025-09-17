# GitLab AI Chatbot

## Overview
The GitLab AI Chatbot is a generative AI application designed to retrieve and provide information from GitLab's Handbook and Direction pages. It uses a retrieval-augmented generation (RAG) pipeline with ChromaDB and sentence-transformers for semantic search, cross-encoder for reranking embeddings and Google Gemini for answer synthesis. The frontend is built using Streamlit for an interactive, user-friendly experience.

## Project Structure
```
gitlab-ai-chatbot
├── .env
├── src
│   ├── backend
│   │   ├── __init__.py
│   │   ├── data_ingestion.py
│   │   ├── chatbot.py
│   │   └── config.py
│   ├── app.py
│   ├── data
│   │   └── (chroma_db/ - downloaded at runtime)
│   └── utils
│       └── helpers.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Quick Start

### 1. Clone and Install
```bash
git clone <repository-url>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the project root and add your Gemini API key:
```
GEMINI_API_KEY=your-gemini-api-key
```

### 3. Download ChromaDB

On first run, the app will automatically download and extract the ChromaDB database from Google Drive if not present in `src/data/chroma_db`.

**If the automatic download fails:**  
1. Download the zip file manually from [Google Drive link](https://drive.google.com/uc?export=download&id=1h01HNP2jsbYPL4x-CYfbt_ssnB5Jcex6)
2. Place the downloaded `chroma_db.zip` file inside the `src/data` directory.
3. Extract it:
   ```bash
   cd src/data
   unzip chroma_db.zip

### 4. Run the App
```bash
cd src
streamlit run app.py
```

## Features

- **Data Retrieval & Processing**: Crawls, chunks, and embeds content from GitLab's Handbook and Direction pages using sentence-transformers and stores it in ChromaDB. (done using data_ingestion.py)
- **Semantic Search**: Finds matching chunks for user query after embedding & Reranks results using a cross-encoder for improved relevance.
- **User Interface**: Clean Streamlit UI
- **Generative AI Chatbot**: Uses Google Gemini to synthesize answers from retrieved context.
- **Transparency**: Shows source links for each generated answer.
- **Feedback System**: Users can rate answers with thumbs up/down, stored for future analysis.


## Environment Variables

| Variable         | Purpose                       |
|------------------|------------------------------|
| GEMINI_API_KEY   | Google Gemini API access      |


## Screenshots
![](https://github.com/Ronak-B/Gitlab-AI-Chatbot/blob/main/screenshots/img1.png)
![](https://github.com/Ronak-B/Gitlab-AI-Chatbot/blob/main/screenshots/img2.png)
![](https://github.com/Ronak-B/Gitlab-AI-Chatbot/blob/main/screenshots/img3.gif)

## Future Work
- Future enhancements: smarter follow-ups, analytics dashboard, advanced moderation.
