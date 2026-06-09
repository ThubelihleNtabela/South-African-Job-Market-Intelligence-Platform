# South African Job Market Intelligence Platform

A starter project for building a Python-based platform that analyzes and visualizes the South African job market.

## Technologies used
- Python
- Requests
- Pandas
- NumPy
- python-dotenv
- SQLAlchemy
- pyodbc
- Azure Storage Blob
- Streamlit
- Plotly

## Planned pipeline steps
1. Ingest job market data from external sources.
2. Process and clean raw job data.
3. Store processed data in a database.
4. Build an interactive dashboard.
5. Add analytics and visualizations for market intelligence.

## Setup instructions
1. Clone the repository.
2. Create a Python virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in the required values.
5. Run the starter app: `python main.py`

## Security

- Store secrets and private configuration values in `.env` instead of committing them to source control.
- `.env` should never be committed to GitHub because it may contain API keys, database credentials, or storage connection strings.
- Use `.env.example` as a safe template when cloning the repository: copy it to `.env`, then add your own secret values locally.
