import logging
from src.settings import LOGGING_DIR
from pathlib import Path
from datetime import datetime

def setup_logging():
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    log_filename = f"kavak_pipeline_{today_date}.log"
    log_path = Path(LOGGING_DIR) / log_filename
    
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_path, encoding='utf-8')]
    )