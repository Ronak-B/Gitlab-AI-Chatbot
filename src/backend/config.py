# ChromaDB settings
import os

MAX_QUERY_LENGTH = 256

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
    "What are the engineering initiatives at gitlab?",
]


SVG_PATH = os.path.join(os.path.dirname(__file__), "../assets/gitlab.svg")
with open(SVG_PATH, "r") as f:
    GITLAB_SVG = f.read()