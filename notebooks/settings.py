from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA = BASE_DIR / "raw"
PROCESSED_DATA = BASE_DIR / "processed"

RAW_HTML_DIR = RAW_DATA / "html"
RAW_JSON_DIR = RAW_DATA / "json"
PROCESSED_JSON_DIR = PROCESSED_DATA / "json"
LOGGING_DIR  = BASE_DIR / "config" / "logs"
FINANCIAL_DATA_DIR = PROCESSED_DATA / "csv" / "financial_data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_JSON_DIR.mkdir(parents=True, exist_ok=True)
RAW_JSON_DIR.mkdir(parents=True, exist_ok=True)
LOGGING_DIR.mkdir(parents=True, exist_ok=True)
FINANCIAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.kavak.com/mx/seminuevos"
MAX_WORKERS = 3
REQUEST_TIMEOUT = 20
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; SM-S911U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone17,5; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 FireKeepers/1.7.0",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
]