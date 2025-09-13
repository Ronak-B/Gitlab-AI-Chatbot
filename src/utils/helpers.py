def log_error(error_message):
    # Function to log errors to a file or console
    print(f"Error: {error_message}")

def format_response(response):
    # Function to format the chatbot's response for better readability
    return response.strip() if response else "I'm sorry, I don't have an answer for that."