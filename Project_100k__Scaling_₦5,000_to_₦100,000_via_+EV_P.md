# Project 100k: Scaling ₦5,000 to ₦100,000 via +EV Predictive Modeling

This project aims to build a Streamlit application for predictive modeling in sports betting, with the goal of scaling an initial capital of ₦5,000 to ₦100,000. It incorporates a Monte Carlo simulation engine, integration with The Odds API, Telegram for notifications and SMS parsing, and Google Sheets for logging.

## Project Structure

- `streamlit_app.py`: Main Streamlit application.
- `predictive_engine.py`: Contains the Monte Carlo simulation and +EV opportunity identification logic.
- `telegram_bot.py`: Handles Telegram bot interactions, including sending signals and parsing SMS.
- `google_sheets.py`: Manages integration with Google Sheets for data logging.
- `config.py`: Stores configuration variables (API keys, tokens, etc.).
- `requirements.txt`: Lists all Python dependencies.
- `.streamlit/config.toml`: Streamlit configuration for mobile-friendly theme.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd project100k
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Create a `config.py` file based on `config.py.example` (to be provided) and fill in your Telegram Bot Token, Odds API Key, and Google Sheets credentials.

4.  **Run the Streamlit app:**
    ```bash
    streamlit run streamlit_app.py
    ```

## Deployment

This project is prepared for deployment on Streamlit Cloud. Ensure all dependencies are listed in `requirements.txt` and the `.streamlit/config.toml` is correctly configured.
