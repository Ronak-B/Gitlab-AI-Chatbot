import streamlit as st
from backend.chatbot import Chatbot
import random

FOLLOWUP_QUESTIONS = [
    "What are GitLab's core values?",
    "How does GitLab support remote work?",
    "Where can I find information about paid time off?",
    "How does performance review work at GitLab?",
    "What is the process for requesting time off?",
    "How does GitLab handle onboarding?",
    "What are the main communication tools at GitLab?",
    "How does GitLab support diversity and inclusion?",
    "What is the handbook's policy on security?",
    "How can I contribute to the GitLab Handbook?",
]

st.set_page_config(page_title="GitLab AI Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 GitLab AI Chatbot")
st.markdown("Ask questions about GitLab's Handbook. Powered by Google Gemini and ChromaDB.")

# --- Session State ---
if "chatbot" not in st.session_state:
    st.session_state.chatbot = Chatbot()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "suggestions" not in st.session_state:
    st.session_state.suggestions = random.sample(FOLLOWUP_QUESTIONS, 3)
if "waiting" not in st.session_state:
    st.session_state.waiting = False

# --- Helper for bot call ---
def append_assistant_response(prompt):
    response, sources = st.session_state.chatbot.generate_response(prompt)
    if sources:
        links = ", &nbsp;".join(
            f'<a href="{url}" target="_blank" style="color:#1a73e8; font-weight:bold; text-decoration:underline;">{i+1}</a>'
            for i, url in enumerate(sources)
        )
        response += f"<br><b>Sources:</b> {links}"
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Render chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# --- Follow-up Suggestions ---
st.markdown("**Quick questions you can try:**")
cols = st.columns(3)
for i, q in enumerate(st.session_state.suggestions):
    disabled = st.session_state.waiting  # disable while bot is thinking
    if cols[i].button(q, key=f"suggest-{i}", disabled=disabled):
        st.session_state.pending_question = q
        st.rerun()

# --- Chat Input ---
prompt = st.chat_input("Ask a question about GitLab's Handbook...",
                       disabled=st.session_state.waiting)
if prompt:
    st.session_state.pending_question = prompt
    st.rerun()

# --- Process Pending Question ---
if st.session_state.pending_question:
    q = st.session_state.pending_question
    # Step 1: Add user message first if not already added
    if not st.session_state.get("user_message_added", False):
        st.session_state.messages.append({"role": "user", "content": q})
        # Add placeholder assistant message (spinner)
        st.session_state.messages.append({"role": "assistant", "content": "⏳ _Thinking..._"})
        st.session_state.user_message_added = True
        st.session_state.waiting = True
        st.rerun()

    # Step 2: Replace placeholder with actual response
    # Remove last message (the "Thinking..." one)
    if st.session_state.messages and st.session_state.messages[-1]["content"] == "⏳ _Thinking..._":
        st.session_state.messages.pop()

    append_assistant_response(q)
    st.session_state.pending_question = None
    st.session_state.user_message_added = False
    st.session_state.suggestions = random.sample(FOLLOWUP_QUESTIONS, 3)
    st.session_state.waiting = False
    st.rerun()
