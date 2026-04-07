import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
VECTOR_DB_PATH    = "./vector_db"
DATA_FILE_PATH    = "./company_data.txt"