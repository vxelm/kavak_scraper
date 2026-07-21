import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA = DATA_DIR / "raw"
PROCESSED_DATA = DATA_DIR / "processed"

RAW_HTML_DIR = RAW_DATA / "html"
RAW_JSON_DIR = RAW_DATA / "json"
PROCESSED_JSON_DIR = PROCESSED_DATA / "json"
LOGGING_DIR  = BASE_DIR / "logs"
FINANCIAL_DATA_DIR = PROCESSED_DATA / "csv" / "financial_data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_JSON_DIR.mkdir(parents=True, exist_ok=True)
RAW_JSON_DIR.mkdir(parents=True, exist_ok=True)
LOGGING_DIR.mkdir(parents=True, exist_ok=True)
FINANCIAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.kavak.com/mx/seminuevos"
MAX_WORKERS = 3
REQUEST_TIMEOUT = 10
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; SM-S911U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone17,5; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 FireKeepers/1.7.0",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
]


def credential_validation() -> None:
    required = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
    missing = [param for param in required if param not in os.environ]
    if missing:
        raise RuntimeError(f"Parametros faltantes para postgreSQL: {missing}")
    
def build_url_db() -> URL:
    credential_validation()

    user = os.environ["POSTGRES_USER"]
    passwd = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]

    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=passwd,
        host=host,
        port=int(port),
        database=db
    )