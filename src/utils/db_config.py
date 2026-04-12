import os
from pathlib import Path
from dotenv import load_dotenv

raiz = Path(__file__).resolve().parent.parent
dotenv_path = raiz/ '.env'

load_dotenv(dotenv_path=dotenv_path)


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}