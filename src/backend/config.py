# ChromaDB settings
import os

CHROMA_DB_ZIP_URL = "https://drive.google.com/uc?export=download&id=1h01HNP2jsbYPL4x-CYfbt_ssnB5Jcex6"
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./data/chroma_db")
COLLECTION_NAME = "handbook_chunks"

# Gemini API settings
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# Retrieval settings
N_RESULTS = 15
TOP_K = 3

FOLLOWUP_QUESTIONS = [
    "What are GitLab's core values?",
    "How does GitLab support remote work?",
    "How does GitLab handle onboarding?",
    "How does GitLab support diversity and inclusion?",
    "How can I edit contents of GitLab Handbook?",
    "Tell me about the CTO leadership team",
    "Employee benefits at gitlab",
]

GITLAB_SVG = (
    '<svg width="20" height="20" viewBox="0 0 1000 1000" style="vertical-align:middle; margin-right:6px;">'
    '<path d="M339.867 12.18c-23.77 2.74-48.01 8.23-70.87 16.23-62.41 22.17-101.5 56.24-123.22 107.45l-5.94 14.4V897.8l8.46 17.37c18.97 38.64 56.69 59.67 126.19 69.96 22.18 3.2 59.9 3.89 303.36 4.57 208.26.69 280.73.23 288.04-1.6 20.8-5.72 33.84-28.8 27.43-48.46-3.43-10.06-15.55-21.95-25.6-24.69-4.8-1.6-121.39-3.2-309.54-4.8-295.82-2.29-301.99-2.52-315.48-7.09-26.52-9.14-41.38-24.69-40.69-42.29.69-18.06 14.17-32.46 39.32-41.84 11.2-4.34 23.09-4.57 310.68-7.08 164.37-1.37 299.25-3.43 299.93-4.12.69-.92 5.94-4.34 11.89-7.77 5.71-3.43 13.72-10.51 17.6-15.77 14.86-20.12 14.17 1.6 13.49-377.89l-.69-345.2-6.4-13.03c-6.86-13.94-17.83-24.46-31.32-30.4-4.34-2.06-9.83-4.57-11.89-5.71-5.01-2.76-480.51-2.53-504.75.22" style="fill:#a989f5;fill-opacity:1;stroke-width:.1"></path>'
    '<path d="m781.144 348.852-.734-1.874-71.005-185.31a18.5 18.5.0 00-7.307-8.8 19.01 19.01.0 00-21.73 1.168 19 19 0 00-6.302 9.561L626.122 310.28H431.985l-47.943-146.683a18.63 18.63.0 00-6.302-9.588 19.01 19.01.0 00-21.73-1.168 18.66 18.66.0 00-7.308 8.8l-71.14 185.228-.707 1.874a131.85 131.85.0 0043.733 152.387l.245.19.652.462 108.164 81.001 53.512 40.5 32.596 24.61a21.92 21.92.0 0026.512.0l32.596-24.61 53.512-40.5 108.816-81.49.272-.217a131.906 131.906.0 0043.679-152.224" style="fill:#fff;stroke-width:2.71634"></path></svg>'
)