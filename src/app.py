import random
import streamlit as st
from backend.chatbot import Chatbot
from backend.config import FOLLOWUP_QUESTIONS, GITLAB_SVG
from utils.helpers import ensure_chroma_db, record_feedback, is_valid_query

ensure_chroma_db()

# --- Streamlit App Configuration ---
st.set_page_config(page_title="GitLab AI Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 GitLab AI Chatbot")
st.markdown("Ask questions about GitLab's Handbook. Powered by Google Gemini.")


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
if "last_bot_response" not in st.session_state:
    st.session_state.last_bot_response = ""
if "last_user_question" not in st.session_state:
    st.session_state.last_user_question = ""

def append_assistant_response(prompt):
    """
    Call the chatbot to get a response for the user prompt.
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

# --- Render chat history ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)
        if (
            message["role"] == "assistant"
            and message.get("content") != "⏳ _Thinking..._"
            and message.get("feedback") is None
        ):
            cols = st.columns([1, 10])
            with cols[0]:
                c1, c2 = st.columns(2, gap="medium")
                with c1:
                    if st.button("👍", key=f"thumbs_up_{idx}", use_container_width=True):
                        st.session_state.messages[idx]["feedback"] = "up"
                        record_feedback(
                            st.session_state.last_user_question,
                            st.session_state.last_bot_response,
                            "up"
                        )
                        st.rerun()
                with c2:
                    if st.button("👎", key=f"thumbs_down_{idx}", use_container_width=True):
                        st.session_state.messages[idx]["feedback"] = "down"
                        record_feedback(
                            st.session_state.last_user_question,
                            st.session_state.last_bot_response,
                            "down"
                        ) 
                        st.rerun()
        elif message.get("feedback") == "up":
            st.markdown("**Feedback:** 👍")
        elif message.get("feedback") == "down":
            st.markdown("**Feedback:** 👎")

# --- Follow-up Suggestions ---
if not st.session_state.waiting:  # only show suggestions if bot is not thinking
    st.markdown("**Quick questions you can try:**")
    cols = st.columns(3)
    for i, q in enumerate(st.session_state.suggestions):
        if cols[i].button(q, key=f"suggest-{i}"):
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
    # --- Validate Query ---
    if not is_valid_query(q):
        st.session_state.pending_question = None
        st.session_state.user_message_added = False
        st.session_state.waiting = False
        st.stop()
    # Step 1: Add user message first if not already added
    if not st.session_state.get("user_message_added", False):
        st.session_state.messages.append({"role": "user", "content": q})
        # Add placeholder assistant message (spinner)
        st.session_state.messages.append({"role": "assistant", "content": "⏳ _Thinking..._"})
        st.session_state.user_message_added = True
        st.session_state.waiting = True
        st.rerun()

    # Step 2: Replace placeholder with actual response
    if st.session_state.messages and st.session_state.messages[-1]["content"] == "⏳ _Thinking..._":
        st.session_state.messages.pop()

    append_assistant_response(q)
    st.session_state.pending_question = None
    st.session_state.user_message_added = False
    st.session_state.suggestions = random.sample(FOLLOWUP_QUESTIONS, 3)
    st.session_state.waiting = False
    st.rerun()