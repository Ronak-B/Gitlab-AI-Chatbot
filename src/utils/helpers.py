import csv
import re
import string

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