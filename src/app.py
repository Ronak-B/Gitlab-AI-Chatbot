import random
import streamlit as st
from backend.chatbot import Chatbot
from backend.config import FOLLOWUP_QUESTIONS, GITLAB_SVG
from utils.helpers import ensure_chroma_db, record_feedback, is_valid_query

# --- Initialization ---
def init_session_state():
    """
    Initialize session state variables.
    """

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
    if "last_bot_response" not in st.session_state:
        st.session_state.last_bot_response = ""
    if "last_user_question" not in st.session_state:
        st.session_state.last_user_question = ""
    if "user_message_added" not in st.session_state:
        st.session_state.user_message_added = False

def append_assistant_response(prompt):
    """
    Append the assistant's response to the chat history.
    """

    response, sources = st.session_state.chatbot.generate_response(prompt)
    st.session_state.last_bot_response = response
    st.session_state.last_user_question = prompt
    if sources:
        gitlab_svg = GITLAB_SVG
        links = ", &nbsp;".join(
            f'<a href="{url}" target="_blank" style="color:#1a73e8; font-weight:bold; text-decoration:underline;">{i+1}</a>'
            for i, url in enumerate(sources)
        )
        response += f"<br><b>{gitlab_svg} Sources:&nbsp;</b> {links}"
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "feedback": None
    })

def render_feedback_buttons(idx, message):
    """
    Render thumbs up and thumbs down feedback buttons.
    """

    cols = st.columns([1, 1, 3, 3])
    with cols[0]:
        if st.button("👍", key=f"thumbs_up_{idx}"):
            st.session_state.messages[idx]["feedback"] = "up"
            record_feedback(
                st.session_state.last_user_question,
                st.session_state.last_bot_response,
                "up"
            )
            st.rerun()
    with cols[1]:
        if st.button("👎", key=f"thumbs_down_{idx}"):
            st.session_state.messages[idx]["feedback"] = "down"
            record_feedback(
                st.session_state.last_user_question,
                st.session_state.last_bot_response,
                "down"
            )   
            st.rerun()

def render_chat_history():
    """
    Render the chat history with feedback buttons.
    """

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
            if (
                message["role"] == "assistant"
                and message.get("content") != "⏳ _Thinking..._"
                and message.get("feedback") is None
            ):
                render_feedback_buttons(idx, message)
            elif message.get("feedback") == "up":
                st.markdown("**Feedback:** 👍")
            elif message.get("feedback") == "down":
                st.markdown("**Feedback:** 👎")

def render_suggestions():
    """
    Render quick suggestion buttons.
    """

    st.markdown("**Quick questions you can try:**")
    cols = st.columns(3)
    for i, q in enumerate(st.session_state.suggestions):
        if cols[i].button(q, key=f"suggest-{i}"):
            st.session_state.pending_question = q
            st.rerun()

def handle_user_input():
    """
    Handle user input from the chat input box.
    """

    prompt = st.chat_input("Ask a question about GitLab's Handbook...",
                           disabled=st.session_state.waiting)
    if prompt:
        st.session_state.pending_question = prompt
        st.rerun()

def process_pending_question():
    """Process the pending question."""

    q = st.session_state.pending_question
    if not is_valid_query(q):
        st.session_state.pending_question = None
        st.session_state.user_message_added = False
        st.session_state.waiting = False
        st.stop()

    if not st.session_state.get("user_message_added", False):
        st.session_state.messages.append({"role": "user", "content": q})
        st.session_state.messages.append({"role": "assistant", "content": "⏳ _Thinking..._"})
        st.session_state.user_message_added = True
        st.session_state.waiting = True
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["content"] == "⏳ _Thinking..._":
        st.session_state.messages.pop()

    append_assistant_response(q)
    st.session_state.pending_question = None
    st.session_state.user_message_added = False
    st.session_state.suggestions = random.sample(FOLLOWUP_QUESTIONS, 3)
    st.session_state.waiting = False
    st.rerun()

# --- Main App Flow ---
ensure_chroma_db()

st.set_page_config(page_title="GitLab AI Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 GitLab AI Chatbot")
st.markdown("Ask questions about GitLab's Handbook. Powered by Google Gemini.")

init_session_state()
render_chat_history()

if not st.session_state.waiting:
    render_suggestions()

handle_user_input()

if st.session_state.pending_question:
    process_pending_question()