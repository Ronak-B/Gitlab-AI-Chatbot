from streamlit import st
from backend.chatbot import Chatbot

def run_app():
    st.title("GitLab AI Chatbot")
    st.write("Ask me anything about GitLab's Handbook and Direction pages!")

    user_input = st.text_input("Your question:")
    
    if st.button("Submit"):
        if user_input:
            chatbot = Chatbot()
            response = chatbot.generate_response(user_input)
            st.write("Chatbot response:")
            st.write(response)
        else:
            st.warning("Please enter a question.") 

if __name__ == "__main__":
    run_app()