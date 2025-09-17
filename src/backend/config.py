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
    "What are the areas of focus of security program",
    "How does gitlab support professional development",
    "What is the gitlab approach to incident management",
    "How does gitlab ensure compliance with data privacy regulations",
    "What is gitlab's approach to open source contributions",
    "How does gitlab support mental health and well-being of employees",
    "How does gitlab foster innovation within the company",
    "How does gitlab handle performance reviews and feedback",
    "What are the key metrics gitlab uses to measure success",
    "How does gitlab support work-life balance for employees",
    "How does gitlab ensure security of its products and services",
    "How does gitlab support community engagement and social responsibility",
    "What are the future plans and vision for gitlab",
]


SVG_PATH = os.path.join(os.path.dirname(__file__), "../assets/gitlab.svg")
with open(SVG_PATH, "r") as f:
    GITLAB_SVG = f.read()