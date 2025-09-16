import csv
import os
import gdown
import re
import requests
import streamlit as st
import string
import zipfile
from backend.config import CHROMA_DB_PATH, CHROMA_DB_ZIP_URL

def ensure_chroma_db():
    db_dir = os.path.abspath(CHROMA_DB_PATH)
    parent_dir = os.path.dirname(db_dir)
    zip_path = os.path.join(parent_dir, "chroma_db.zip")
    if not os.path.exists(db_dir):
        os.makedirs(parent_dir, exist_ok=True)
        st.info("ChromaDB not found. Downloading database, please wait...")
        gdown.download(CHROMA_DB_ZIP_URL, zip_path, quiet=False)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(parent_dir)
        os.remove(zip_path)
        st.success("ChromaDB downloaded and extracted.")


def normalize(text):
    """
    Normalize the text by lowercasing, removing punctuation, and stripping whitespace.
    """

    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def title_keywords(title):
    """
    Extract keywords from the title.
    """

    title = re.sub(r'\(.*?\)', '', title)
    return set(re.findall(r'\w+', title.lower()))

def extract_error_type(e):
    """
    Extract error type or status code from an exception.
    """

    msg = str(e)
    match = re.search(r'\b(5\d{2})\b', msg)
    if match:
        return match.group(1)
    if hasattr(e, "status_code"):
        return str(e.status_code)
    return ""

def record_feedback(question, answer, feedback):
    """
    Record user feedback for a specific question and answer pair.
    """

    with open("feedback.csv", "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([question, answer, feedback])