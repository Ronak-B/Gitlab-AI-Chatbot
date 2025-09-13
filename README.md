

# GitLab AI Chatbot

## Overview
The GitLab AI Chatbot is a generative AI application designed to retrieve and provide information from GitLab's Handbook and Direction pages. It utilizes a backend architecture for data retrieval and processing, while the frontend is built using Streamlit to create an interactive user interface.

## Project Structure
```
gitlab-ai-chatbot
├── src
│   ├── backend
│   │   ├── __init__.py
│   │   ├── retrieval.py
│   │   ├── chatbot.py
│   │   └── config.py
│   ├── frontend
│   │   ├── __init__.py
│   │   └── app.py
│   ├── data
│   │   └── README.md
│   └── utils
│       └── helpers.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation
To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd gitlab-ai-chatbot
pip install -r requirements.txt
```

## Usage
To run the Streamlit application, execute the following command:

```bash
streamlit run src/frontend/app.py
```

This will start the application, allowing users to interact with the chatbot and retrieve information from GitLab's resources.

## Features
- **Data Retrieval**: The backend retrieves and processes data from GitLab's Handbook and Direction pages.
- **Generative AI**: The chatbot generates responses based on user queries using a trained AI model.
- **User Interface**: A simple and intuitive interface built with Streamlit for easy interaction.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.