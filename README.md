# Appointment Scheduling Agent

A **Conversational AI Agent** designed to streamline appointment scheduling for patients, providing functionalities to schedule, reschedule, and cancel appointments seamlessly.

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#Usage)

## Features
- **Natural Language Processing:** Utilize GPT-based models to understand and process user requests.
- **Appointment Management:** Schedule, reschedule, and cancel appointments with ease.
- **Synthetic Data Generation:** Create realistic doctor and patient profiles for testing and development.
- **Real-time Data Hosting:** Host datasets using FastAPI for efficient data retrieval.
- **Interactive Interface:** User-friendly UI built with Streamlit for seamless interactions.
- **Action Tracking:** Monitor agent actions and responses through custom trajectory evaluation.

## Technologies Used
- **[LangChain](https://github.com/hwchase17/langchain):** Framework for developing applications powered by language models.
- **[Streamlit](https://streamlit.io/):** Fast and easy way to build custom web apps for machine learning and data science.
- **[OpenAI](https://openai.com/):** Advanced language models for natural language understanding and generation.
- **[Pandas](https://pandas.pydata.org/):** Data manipulation and analysis library.
- **[Faker](https://faker.readthedocs.io/en/master/):** Generate fake data for testing and development.
- **[LangSmith](https://www.langsmith.ai/):** Tool for monitoring and evaluating language model performance.
- **[FastAPI](https://fastapi.tiangolo.com/):** Modern, fast (high-performance) web framework for building APIs with Python.

## Installation
### Prerequisites
- **Python 3.8 or higher**  
- **Git**
- Clone the repository:
   ```bash
   git clone https://github.com/SudeepMungara/appointment-scheduling-agent.git
   cd appointment-scheduling-agent
   ```
## Usage
  - **Start the FastAPI Server**:
    - Ensure the FastAPI server is running to provide synthetic data.
  - **Interact with the Agent**:
    - Enter your request in the Streamlit app:
        - "Schedule an appointment with Dr. Smith on Monday at 10 AM."
        - "Reschedule my appointment to Tuesday at 2 PM."
        - "Cancel my appointment with Dr. Adams."
  - **Monitor Agent Actions**:
    - Use LangSmith to track and evaluate the agent's decision-making process.
